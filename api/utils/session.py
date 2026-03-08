"""
Cookie-based session management for server-rendered pages.

Uses itsdangerous (bundled with Starlette) to sign a user_id into a cookie.
"""

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request
from fastapi.responses import Response

from api.config import settings

_MAX_AGE = 30 * 24 * 3600  # 30 days
_COOKIE_NAME = "kb_session"


def _get_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.FLASK_SECRET_KEY)


def create_session_value(user_id: str) -> str:
    """Sign a user_id into a cookie-safe string."""
    return _get_serializer().dumps(user_id, salt="kb-session")


def read_session_value(cookie_value: str) -> str | None:
    """Unsign and return user_id, or None if invalid/expired."""
    try:
        return _get_serializer().loads(cookie_value, salt="kb-session", max_age=_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def set_session_cookie(response: Response, user_id: str) -> None:
    """Set the signed session cookie on a response."""
    response.set_cookie(
        _COOKIE_NAME,
        create_session_value(user_id),
        max_age=_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=not settings.BASE_URL.startswith("http://localhost"),
    )


def clear_session_cookie(response: Response) -> None:
    """Remove the session cookie."""
    response.delete_cookie(_COOKIE_NAME)


def get_session_user_id(request: Request) -> str | None:
    """Read the session cookie and return the user_id, or None."""
    cookie = request.cookies.get(_COOKIE_NAME)
    if not cookie:
        return None
    return read_session_value(cookie)
