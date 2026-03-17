"""
Feedback router: topic suggestions and playbook ratings.
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import get_db
from api.models.activity import DownloadLog, ReadingProgress
from api.models.feedback import PlaybookFeedback, TopicSuggestion
from api.models.playbook import Playbook
from api.models.user import User
from api.utils.session import get_session_user_id

router = APIRouter(tags=["feedback"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def _require_admin_session(request: Request, db: AsyncSession) -> User:
    """Check session cookie for an admin user."""
    user_id = get_session_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class SuggestionRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    email: str | None = None
    detail: str | None = None


class FeedbackRequest(BaseModel):
    slug: str
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None
    email: str | None = None
    scroll_percent: int | None = None
    time_spent_secs: int | None = None


class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(created|saved|deleted)$")


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@router.post("/suggestions")
async def submit_suggestion(
    body: SuggestionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip = _get_client_ip(request)

    # Simple rate limit: 1 per IP per 5 minutes
    if ip:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        recent = await db.execute(
            select(func.count(TopicSuggestion.id)).where(
                TopicSuggestion.ip_address == ip,
                TopicSuggestion.created_at > cutoff,
            )
        )
        if (recent.scalar() or 0) > 0:
            return JSONResponse(
                {"ok": True, "message": "Thank you for your suggestion!"}
            )

    suggestion = TopicSuggestion(
        topic=body.topic.strip(),
        email=body.email.strip() if body.email else None,
        detail=body.detail.strip() if body.detail else None,
        ip_address=ip,
    )
    db.add(suggestion)
    await db.commit()

    return {"ok": True, "message": "Thank you for your suggestion!"}


@router.get("/feedback-summary")
async def feedback_summary(
    db: AsyncSession = Depends(get_db),
):
    """Return average rating and count per slug (public, no auth)."""
    result = await db.execute(
        select(
            PlaybookFeedback.slug,
            func.avg(PlaybookFeedback.rating),
            func.count(PlaybookFeedback.id),
        ).group_by(PlaybookFeedback.slug)
    )
    ratings = {}
    for slug, avg, count in result.all():
        ratings[slug] = {"avg": round(float(avg), 1), "count": count}
    return {"ratings": ratings}


@router.get("/user/progress")
async def user_progress(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return reading progress for all playbooks for the logged-in user."""
    user_id = get_session_user_id(request)
    if not user_id:
        return {"progress": {}}

    result = await db.execute(
        select(ReadingProgress, Playbook.slug)
        .join(Playbook, ReadingProgress.playbook_id == Playbook.id)
        .where(ReadingProgress.user_id == user_id)
    )
    progress = {}
    for rp, slug in result.all():
        if rp.completed:
            status = "completed"
        elif rp.downloaded:
            status = "downloaded"
        elif rp.last_chapter:
            status = rp.last_chapter
        elif rp.scroll_percent > 0:
            status = "opened"
        else:
            status = "not-started"
        progress[slug] = {
            "status": status,
            "scroll_percent": rp.scroll_percent,
            "last_chapter": rp.last_chapter,
            "completed": rp.completed,
            "downloaded": rp.downloaded,
        }
    return {"progress": progress}


class DownloadTrackRequest(BaseModel):
    slug: str


@router.post("/track-download")
async def track_download(
    body: DownloadTrackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Record a PDF download and mark progress as downloaded."""
    result = await db.execute(
        select(Playbook).where(Playbook.slug == body.slug)
    )
    pb = result.scalar_one_or_none()

    user_id = get_session_user_id(request)
    ip = _get_client_ip(request)
    ua = request.headers.get("user-agent")

    # Log the download
    dl = DownloadLog(
        user_id=user_id,
        playbook_id=pb.id if pb else None,
        ip_address=ip,
        user_agent=ua,
        platform="pdf",
    )
    db.add(dl)

    # Update reading progress for logged-in users
    if user_id and pb:
        rp_result = await db.execute(
            select(ReadingProgress)
            .where(ReadingProgress.user_id == user_id)
            .where(ReadingProgress.playbook_id == pb.id)
        )
        rp = rp_result.scalar_one_or_none()
        if rp:
            rp.downloaded = True
        else:
            rp = ReadingProgress(
                user_id=user_id,
                playbook_id=pb.id,
                downloaded=True,
            )
            db.add(rp)

    await db.commit()
    return {"ok": True}


@router.post("/feedback")
async def submit_feedback(
    body: FeedbackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Look up playbook_id from slug (optional — feedback still saved if not seeded)
    result = await db.execute(
        select(Playbook.id).where(Playbook.slug == body.slug)
    )
    playbook_id = result.scalar_one_or_none()

    ip = _get_client_ip(request)

    feedback = PlaybookFeedback(
        playbook_id=playbook_id,
        slug=body.slug,
        email=body.email.strip() if body.email else None,
        rating=body.rating,
        comment=body.comment.strip() if body.comment else None,
        scroll_percent=body.scroll_percent,
        time_spent_secs=body.time_spent_secs,
        ip_address=ip,
    )
    db.add(feedback)
    await db.commit()

    return {"ok": True}


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@router.get("/admin/suggestions")
async def list_suggestions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    await _require_admin_session(request, db)

    query = select(TopicSuggestion)
    count_query = select(func.count(TopicSuggestion.id))

    if status_filter:
        query = query.where(TopicSuggestion.status == status_filter)
        count_query = count_query.where(TopicSuggestion.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(TopicSuggestion.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    rows = result.scalars().all()

    items = [
        {
            "id": str(s.id),
            "email": s.email,
            "topic": s.topic,
            "detail": s.detail,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in rows
    ]

    return {"items": items, "total": total}


@router.patch("/admin/suggestions/{suggestion_id}")
async def update_suggestion_status(
    suggestion_id: uuid.UUID,
    body: StatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _require_admin_session(request, db)

    result = await db.execute(
        select(TopicSuggestion).where(TopicSuggestion.id == suggestion_id)
    )
    suggestion = result.scalar_one_or_none()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    suggestion.status = body.status
    await db.commit()

    return {"ok": True, "status": suggestion.status}


@router.get("/admin/feedback-list")
async def list_feedback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    await _require_admin_session(request, db)

    count_result = await db.execute(select(func.count(PlaybookFeedback.id)))
    total = count_result.scalar() or 0

    avg_result = await db.execute(select(func.avg(PlaybookFeedback.rating)))
    avg_rating = round(float(avg_result.scalar() or 0), 1)

    query = (
        select(PlaybookFeedback, Playbook.title)
        .outerjoin(Playbook, PlaybookFeedback.playbook_id == Playbook.id)
        .order_by(PlaybookFeedback.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)

    items = [
        {
            "id": str(fb.id),
            "playbook_title": title,
            "slug": fb.slug,
            "email": fb.email,
            "rating": fb.rating,
            "comment": fb.comment,
            "scroll_percent": fb.scroll_percent,
            "time_spent_secs": fb.time_spent_secs,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        }
        for fb, title in result.all()
    ]

    return {"items": items, "total": total, "avg_rating": avg_rating}


@router.delete("/admin/feedback-list/{feedback_id}")
async def delete_feedback(
    feedback_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _require_admin_session(request, db)

    result = await db.execute(
        select(PlaybookFeedback).where(PlaybookFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    await db.delete(feedback)
    await db.commit()

    return {"ok": True}


# NOTE: /admin/run-sql endpoint REMOVED (2026-03-13) — security risk.
# Arbitrary SQL execution with only a static code guard is a backdoor.
# Use proper admin endpoints or direct DB access for ad-hoc queries.
