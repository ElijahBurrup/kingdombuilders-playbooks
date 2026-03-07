from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import get_db
from api.dependencies import get_current_user
from api.models.user import OAuthAccount, RefreshToken, User, VerificationToken
from api.schemas.auth import (
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)
from api.utils.security import (
    create_access_token,
    create_refresh_token,
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_token_response(
    access_token: str, raw_refresh: str
) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def _create_token_pair(
    user: User, db: AsyncSession
) -> TokenResponse:
    """Create an access + refresh token pair and persist the refresh hash."""
    access_token = create_access_token(
        user_id=str(user.id),
        role=user.role,
        email_verified=user.email_verified,
    )
    raw_refresh, refresh_hash = create_refresh_token()

    refresh_row = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_row)
    await db.commit()

    return _build_token_response(access_token, raw_refresh)


# ---------- 1. POST /register ----------
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check for existing user
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
    )
    db.add(user)
    await db.flush()  # populate user.id before creating tokens

    return await _create_token_pair(user, db)


# ---------- 2. POST /login ----------
@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return await _create_token_pair(user, db)


# ---------- 3. POST /refresh ----------
@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    incoming_hash = hash_token(body.refresh_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == incoming_hash,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    token_row = result.scalar_one_or_none()

    if token_row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke the old refresh token (rotation)
    token_row.revoked = True
    await db.flush()

    # Load the user
    user_result = await db.execute(
        select(User).where(User.id == token_row.user_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return await _create_token_pair(user, db)


# ---------- 4. POST /logout ----------
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    incoming_hash = hash_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == incoming_hash)
    )
    token_row = result.scalar_one_or_none()
    if token_row is not None:
        token_row.revoked = True
        await db.commit()
    return {"detail": "Logged out"}


# ---------- 5. POST /google ----------
@router.post("/google", response_model=TokenResponse)
async def google_auth(
    body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)
):
    # Verify the id_token with Google
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": body.id_token},
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google ID token",
        )

    token_info = resp.json()
    google_id = token_info.get("sub")
    email = token_info.get("email")
    name = token_info.get("name")
    picture = token_info.get("picture")

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not extract user info from Google token",
        )

    # Verify the audience matches our client ID
    if settings.GOOGLE_CLIENT_ID and token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token audience mismatch",
        )

    # Check if this Google account is already linked
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == "google",
            OAuthAccount.provider_id == google_id,
        )
    )
    oauth_account = result.scalar_one_or_none()

    if oauth_account is not None:
        # Existing linked account — load the user
        user_result = await db.execute(
            select(User).where(User.id == oauth_account.user_id)
        )
        user = user_result.scalar_one()
    else:
        # Check if a user with this email already exists
        user_result = await db.execute(
            select(User).where(User.email == email)
        )
        user = user_result.scalar_one_or_none()

        if user is None:
            # Create a new user
            user = User(
                email=email,
                display_name=name,
                avatar_url=picture,
                email_verified=True,
            )
            db.add(user)
            await db.flush()

        # Link the OAuth account
        oauth_link = OAuthAccount(
            user_id=user.id,
            provider="google",
            provider_id=google_id,
        )
        db.add(oauth_link)
        await db.flush()

    # Mark email as verified (Google verified it)
    if not user.email_verified:
        user.email_verified = True
        await db.flush()

    return await _create_token_pair(user, db)


# ---------- 6. POST /verify-email ----------
@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(token)
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token_hash == token_hash,
            VerificationToken.token_type == "email_verify",
            VerificationToken.used_at == None,  # noqa: E711
            VerificationToken.expires_at > datetime.now(timezone.utc),
        )
    )
    vtoken = result.scalar_one_or_none()

    if vtoken is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    vtoken.used_at = datetime.now(timezone.utc)

    user_result = await db.execute(
        select(User).where(User.id == vtoken.user_id)
    )
    user = user_result.scalar_one()
    user.email_verified = True

    await db.commit()
    return {"detail": "Email verified successfully"}


# ---------- 7. POST /forgot-password ----------
@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Always return 200 to prevent email enumeration
    if user is None:
        return {"detail": "If the email exists, a reset link has been sent"}

    # Generate a password reset token
    raw_token = generate_token()
    token_hash = hash_token(raw_token)

    vtoken = VerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        token_type="password_reset",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(vtoken)
    await db.commit()

    # TODO: Send password reset email via Resend
    # The raw_token should be included in the reset link sent to the user.
    # For now, this is a placeholder — the email service will be wired in later.

    return {"detail": "If the email exists, a reset link has been sent"}


# ---------- 8. POST /reset-password ----------
@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    token_hash = hash_token(body.token)
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token_hash == token_hash,
            VerificationToken.token_type == "password_reset",
            VerificationToken.used_at == None,  # noqa: E711
            VerificationToken.expires_at > datetime.now(timezone.utc),
        )
    )
    vtoken = result.scalar_one_or_none()

    if vtoken is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    vtoken.used_at = datetime.now(timezone.utc)

    user_result = await db.execute(
        select(User).where(User.id == vtoken.user_id)
    )
    user = user_result.scalar_one()
    user.password_hash = hash_password(body.new_password)
    user.updated_at = datetime.now(timezone.utc)

    await db.commit()
    return {"detail": "Password reset successfully"}


# ---------- 9. GET /me ----------
@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


# ---------- 10. PATCH /me ----------
@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.display_name is not None:
        user.display_name = body.display_name
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url

    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user
