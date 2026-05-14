"""Widget responses router: per-user persistence for interactive widgets.

Two modes:
- "latest" (default): upsert by (user_id, playbook_slug, widget_key). One row.
  Used for diagnostics, calculators, mappers that the user re-runs and
  the latest state is what matters.
- "history": append-only rows. Used for diary-style widgets (Ant Network
  Immune Diary, etc.) where the reader accumulates entries over time.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, desc, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.dependencies import get_current_user_optional
from api.models.user import User
from api.models.widget import WidgetResponse

router = APIRouter(tags=["widgets"])


_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{0,118}[a-z0-9]$")
_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9\-_]{0,78}[a-z0-9]$")
_MAX_BYTES = 32_000  # generous JSON size cap per response


def _validate_slug(slug: str) -> str:
    if not _SLUG_RE.match(slug):
        raise HTTPException(status_code=400, detail="Invalid playbook slug.")
    return slug


def _validate_key(key: str) -> str:
    if not _KEY_RE.match(key):
        raise HTTPException(status_code=400, detail="Invalid widget key.")
    return key


def _approximate_json_size(data: Any) -> int:
    """Cheap size estimate. We do not want to round-trip through json."""
    try:
        import json
        return len(json.dumps(data, default=str))
    except Exception:
        return _MAX_BYTES + 1


class WidgetSaveRequest(BaseModel):
    data: dict | list = Field(..., description="Widget response payload.")
    history: bool = Field(
        default=False,
        description=(
            "If true, append to the user's history for this widget. "
            "If false (default), upsert the user's latest response."
        ),
    )


class WidgetResponseOut(BaseModel):
    data: dict | list
    is_history: bool
    created_at: datetime
    updated_at: datetime


class WidgetHistoryOut(BaseModel):
    entries: list[WidgetResponseOut]


@router.post("/widgets/{slug}/{key}", status_code=status.HTTP_200_OK)
async def save_widget(
    slug: str,
    key: str,
    payload: WidgetSaveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> dict:
    """Save a widget response.

    Auth-optional: if no user is signed in, we return 204-style success with
    `persisted=False` so the client can keep using localStorage. We do not
    raise 401 — widgets must remain usable for anonymous readers.
    """
    slug = _validate_slug(slug)
    key = _validate_key(key)

    if _approximate_json_size(payload.data) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Widget payload too large.")

    if user is None:
        return {"persisted": False}

    now = datetime.now(timezone.utc)

    if payload.history:
        row = WidgetResponse(
            user_id=user.id,
            playbook_slug=slug,
            widget_key=key,
            is_history=True,
            data=payload.data,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return {
            "persisted": True,
            "mode": "history",
            "id": str(row.id),
            "created_at": row.created_at.isoformat(),
        }

    # Latest-only mode: upsert the single row for (user, slug, key, is_history=false)
    existing = (
        await db.execute(
            select(WidgetResponse).where(
                WidgetResponse.user_id == user.id,
                WidgetResponse.playbook_slug == slug,
                WidgetResponse.widget_key == key,
                WidgetResponse.is_history == False,  # noqa: E712
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        row = WidgetResponse(
            user_id=user.id,
            playbook_slug=slug,
            widget_key=key,
            is_history=False,
            data=payload.data,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
    else:
        existing.data = payload.data
        existing.updated_at = now
        await db.commit()
        row = existing

    return {
        "persisted": True,
        "mode": "latest",
        "updated_at": row.updated_at.isoformat(),
    }


@router.get("/widgets/{slug}/{key}")
async def load_widget(
    slug: str,
    key: str,
    request: Request,
    history: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> dict:
    """Load a widget response for the current user.

    If the user is not signed in, returns 200 with `signed_in=False` and
    no data so the client can fall back to localStorage without seeing
    an error in the console.
    """
    slug = _validate_slug(slug)
    key = _validate_key(key)

    if user is None:
        return {"signed_in": False, "data": None, "entries": []}

    if history:
        limit = max(1, min(limit, 200))
        rows = (
            await db.execute(
                select(WidgetResponse)
                .where(
                    WidgetResponse.user_id == user.id,
                    WidgetResponse.playbook_slug == slug,
                    WidgetResponse.widget_key == key,
                    WidgetResponse.is_history == True,  # noqa: E712
                )
                .order_by(desc(WidgetResponse.created_at))
                .limit(limit)
            )
        ).scalars().all()
        return {
            "signed_in": True,
            "entries": [
                {
                    "data": r.data,
                    "is_history": True,
                    "created_at": r.created_at.isoformat(),
                    "updated_at": r.updated_at.isoformat(),
                }
                for r in rows
            ],
        }

    row = (
        await db.execute(
            select(WidgetResponse).where(
                WidgetResponse.user_id == user.id,
                WidgetResponse.playbook_slug == slug,
                WidgetResponse.widget_key == key,
                WidgetResponse.is_history == False,  # noqa: E712
            )
        )
    ).scalar_one_or_none()

    if row is None:
        return {"signed_in": True, "data": None}

    return {
        "signed_in": True,
        "data": row.data,
        "updated_at": row.updated_at.isoformat(),
    }


@router.delete("/widgets/{slug}/{key}", status_code=status.HTTP_200_OK)
async def clear_widget(
    slug: str,
    key: str,
    request: Request,
    history: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> dict:
    """Clear a widget's saved state. Useful for reset buttons."""
    slug = _validate_slug(slug)
    key = _validate_key(key)

    if user is None:
        return {"cleared": False, "signed_in": False}

    stmt = delete(WidgetResponse).where(
        WidgetResponse.user_id == user.id,
        WidgetResponse.playbook_slug == slug,
        WidgetResponse.widget_key == key,
    )
    if not history:
        stmt = stmt.where(WidgetResponse.is_history == False)  # noqa: E712

    result = await db.execute(stmt)
    await db.commit()
    return {"cleared": True, "deleted": result.rowcount or 0}
