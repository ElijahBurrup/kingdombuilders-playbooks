"""User Saves router: explicit reader bookmarks of widget state.

Distinct from /widgets (auto-persisted live state). A Save is the reader's
deliberate "keep this snapshot" action. Used to power the My Saves page.

Auth model: REQUIRED. Unlike /widgets, anonymous users cannot save —
the client redirects to /auth?next=... when they hit the save button.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.dependencies import get_current_user_optional
from api.models.user import User
from api.models.user_save import UserSave

router = APIRouter(tags=["saves"])


_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{0,118}[a-z0-9]$")
_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9\-_]{0,78}[a-z0-9]$")
_MAX_PAYLOAD_BYTES = 32_000


def _validate_slug(slug: str) -> str:
    if not _SLUG_RE.match(slug):
        raise HTTPException(status_code=400, detail="Invalid playbook slug.")
    return slug


def _validate_key(key: str) -> str:
    if not _KEY_RE.match(key):
        raise HTTPException(status_code=400, detail="Invalid widget key.")
    return key


def _payload_size(data: Any) -> int:
    try:
        import json
        return len(json.dumps(data, default=str))
    except Exception:
        return _MAX_PAYLOAD_BYTES + 1


class SaveRequest(BaseModel):
    playbook_slug: str = Field(..., max_length=120)
    widget_key: str = Field(..., max_length=80)
    widget_title: str = Field(..., min_length=1, max_length=160)
    playbook_title: str = Field(..., min_length=1, max_length=200)
    preview_text: str = Field(default="", max_length=400)
    payload: dict | list = Field(..., description="Snapshot of widget state at save time.")


class SaveOut(BaseModel):
    id: str
    playbook_slug: str
    widget_key: str
    widget_title: str
    playbook_title: str
    preview_text: str
    payload: dict | list
    saved_at: datetime


class SaveListOut(BaseModel):
    saves: list[SaveOut]


@router.post("/saves", status_code=status.HTTP_200_OK, response_model=SaveOut)
async def create_or_update_save(
    body: SaveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> SaveOut:
    """Upsert a save for (current_user, playbook_slug, widget_key).

    Returns 401 if anonymous so the client can redirect to sign-in.
    Re-saving the same widget bumps saved_at and updates the snapshot.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to save.")

    slug = _validate_slug(body.playbook_slug)
    key = _validate_key(body.widget_key)

    if _payload_size(body.payload) > _MAX_PAYLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Payload too large.")

    now = datetime.now(timezone.utc)

    existing = (
        await db.execute(
            select(UserSave).where(
                UserSave.user_id == user.id,
                UserSave.playbook_slug == slug,
                UserSave.widget_key == key,
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        row = UserSave(
            user_id=user.id,
            playbook_slug=slug,
            widget_key=key,
            widget_title=body.widget_title.strip(),
            playbook_title=body.playbook_title.strip(),
            preview_text=(body.preview_text or "").strip(),
            payload=body.payload,
            saved_at=now,
        )
        db.add(row)
    else:
        existing.widget_title = body.widget_title.strip()
        existing.playbook_title = body.playbook_title.strip()
        existing.preview_text = (body.preview_text or "").strip()
        existing.payload = body.payload
        existing.saved_at = now
        row = existing

    await db.commit()
    await db.refresh(row)

    return SaveOut(
        id=str(row.id),
        playbook_slug=row.playbook_slug,
        widget_key=row.widget_key,
        widget_title=row.widget_title,
        playbook_title=row.playbook_title,
        preview_text=row.preview_text,
        payload=row.payload,
        saved_at=row.saved_at,
    )


@router.get("/saves", response_model=SaveListOut)
async def list_saves(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> SaveListOut:
    """List the current user's saves, newest first."""
    if user is None:
        return SaveListOut(saves=[])

    rows = (
        await db.execute(
            select(UserSave)
            .where(UserSave.user_id == user.id)
            .order_by(desc(UserSave.saved_at))
        )
    ).scalars().all()

    return SaveListOut(
        saves=[
            SaveOut(
                id=str(r.id),
                playbook_slug=r.playbook_slug,
                widget_key=r.widget_key,
                widget_title=r.widget_title,
                playbook_title=r.playbook_title,
                preview_text=r.preview_text,
                payload=r.payload,
                saved_at=r.saved_at,
            )
            for r in rows
        ]
    )


@router.get("/saves/check")
async def check_save(
    slug: str,
    key: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> dict:
    """Quick check: is this widget currently saved by the user?"""
    if user is None:
        return {"saved": False, "signed_in": False}
    slug = _validate_slug(slug)
    key = _validate_key(key)
    row = (
        await db.execute(
            select(UserSave.id).where(
                UserSave.user_id == user.id,
                UserSave.playbook_slug == slug,
                UserSave.widget_key == key,
            )
        )
    ).scalar_one_or_none()
    return {"saved": row is not None, "signed_in": True}


@router.delete("/saves/by-key")
async def delete_save_by_key(
    slug: str,
    key: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> dict:
    """Unsave by (slug, widget_key) — convenient for in-playbook unsave."""
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in.")
    slug = _validate_slug(slug)
    key = _validate_key(key)
    result = await db.execute(
        delete(UserSave).where(
            UserSave.user_id == user.id,
            UserSave.playbook_slug == slug,
            UserSave.widget_key == key,
        )
    )
    await db.commit()
    return {"deleted": result.rowcount or 0}


@router.delete("/saves/{save_id}")
async def delete_save(
    save_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> dict:
    """Unsave by row id — used by the My Saves page."""
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in.")
    try:
        sid = uuid.UUID(save_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid id.")
    result = await db.execute(
        delete(UserSave).where(
            UserSave.id == sid,
            UserSave.user_id == user.id,
        )
    )
    await db.commit()
    return {"deleted": result.rowcount or 0}
