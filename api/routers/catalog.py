import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.database import get_db
from api.dependencies import get_current_user, get_current_user_from_session, get_current_user_optional
from api.models.playbook import Category, Playbook, Series
from api.models.purchase import Purchase, Subscription
from api.models.user import User
from api.schemas.playbook import (
    CategoryResponse,
    PlaybookContent,
    PlaybookDetail,
    PlaybookListResponse,
    PlaybookSummary,
    SeriesResponse,
)
from api.services.access_service import check_access

router = APIRouter(tags=["catalog"])


def _playbook_to_summary(playbook: Playbook) -> PlaybookSummary:
    """Convert a Playbook ORM instance to a PlaybookSummary schema."""
    category_resp = None
    if playbook.category is not None:
        category_resp = CategoryResponse(
            id=playbook.category.id,
            name=playbook.category.name,
            slug=playbook.category.slug,
            color_bg=playbook.category.color_bg,
            color_text=playbook.category.color_text,
            display_order=playbook.category.display_order,
            playbook_count=0,
        )

    series_name = None
    if playbook.series is not None:
        series_name = playbook.series.name

    return PlaybookSummary(
        id=playbook.id,
        slug=playbook.slug,
        title=playbook.title,
        subtitle=playbook.subtitle,
        description=playbook.description,
        pricing_type=playbook.pricing_type,
        price_cents=playbook.price_cents,
        category=category_resp,
        series_name=series_name,
        series_order=playbook.series_order,
        cover_emoji=playbook.cover_emoji,
        status=playbook.status,
        published_at=playbook.published_at,
        featured=playbook.featured,
        view_count=playbook.view_count,
        purchase_count=playbook.purchase_count,
    )


# ---------- 1. GET /playbooks ----------
@router.get("/playbooks", response_model=PlaybookListResponse)
async def list_playbooks(
    category: str | None = Query(None, description="Filter by category slug"),
    series: str | None = Query(None, description="Filter by series slug"),
    pricing: str | None = Query(
        None, description="Filter by pricing type: free, paid, or all"
    ),
    q: str | None = Query(None, description="Search query"),
    sort: str | None = Query(
        "newest", description="Sort order: newest, popular, or title"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    # Base query: only published playbooks, eagerly load category and series
    query = (
        select(Playbook)
        .options(joinedload(Playbook.category), joinedload(Playbook.series))
        .where(Playbook.status == "published")
    )

    # Category filter
    if category:
        query = query.join(Category).where(Category.slug == category)

    # Series filter
    if series:
        query = query.join(Series).where(Series.slug == series)

    # Pricing filter
    if pricing and pricing != "all":
        if pricing == "free":
            query = query.where(Playbook.pricing_type == "free")
        elif pricing == "paid":
            query = query.where(Playbook.pricing_type.in_(["paid", "subscriber_only"]))

    # Search filter
    if q:
        search_term = f"%{q}%"
        query = query.where(
            Playbook.title.ilike(search_term)
            | Playbook.description.ilike(search_term)
            | Playbook.subtitle.ilike(search_term)
        )

    # Count total before pagination
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sorting
    if sort == "popular":
        query = query.order_by(Playbook.view_count.desc())
    elif sort == "title":
        query = query.order_by(Playbook.title.asc())
    else:  # newest (default)
        query = query.order_by(Playbook.published_at.desc().nullslast())

    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    playbooks = result.unique().scalars().all()

    items = [_playbook_to_summary(pb) for pb in playbooks]
    pages = math.ceil(total / per_page) if per_page > 0 else 0

    return PlaybookListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


# ---------- 2. GET /playbooks/featured (MUST be before /playbooks/{slug}) ----------
@router.get("/playbooks/featured", response_model=list[PlaybookSummary])
async def list_featured_playbooks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Playbook)
        .options(joinedload(Playbook.category), joinedload(Playbook.series))
        .where(
            Playbook.status == "published",
            Playbook.featured == True,  # noqa: E712
        )
        .order_by(Playbook.published_at.desc().nullslast())
    )
    playbooks = result.unique().scalars().all()
    return [_playbook_to_summary(pb) for pb in playbooks]


# ---------- 3. GET /playbooks/{slug} ----------
@router.get("/playbooks/{slug}", response_model=PlaybookDetail)
async def get_playbook(
    slug: str,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playbook)
        .options(joinedload(Playbook.category), joinedload(Playbook.series))
        .where(Playbook.slug == slug)
    )
    playbook = result.unique().scalar_one_or_none()

    if playbook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playbook not found",
        )

    # Only show published playbooks to non-admin users
    if playbook.status != "published":
        if user is None or user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found",
            )

    # Build the summary fields
    summary = _playbook_to_summary(playbook)

    # Check access if user is authenticated
    has_access = False
    if user is not None:
        has_access = await check_access(user.id, playbook, db)

    return PlaybookDetail(
        **summary.model_dump(),
        landing_html=playbook.landing_html,
        has_access=has_access,
    )


# ---------- 4. GET /playbooks/{slug}/content ----------
@router.get("/playbooks/{slug}/content", response_model=PlaybookContent)
async def get_playbook_content(
    slug: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playbook).where(Playbook.slug == slug)
    )
    playbook = result.scalar_one_or_none()

    if playbook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playbook not found",
        )

    has_access = await check_access(user.id, playbook, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this playbook. Purchase it or subscribe to read.",
        )

    return PlaybookContent(
        content_html=playbook.content_html,
        content_version=playbook.content_version,
    )


# ---------- 5. GET /categories ----------
@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    # Count published playbooks per category
    count_subq = (
        select(
            Playbook.category_id,
            func.count(Playbook.id).label("playbook_count"),
        )
        .where(Playbook.status == "published")
        .group_by(Playbook.category_id)
        .subquery()
    )

    result = await db.execute(
        select(
            Category,
            func.coalesce(count_subq.c.playbook_count, 0).label("playbook_count"),
        )
        .outerjoin(count_subq, Category.id == count_subq.c.category_id)
        .order_by(Category.display_order.asc())
    )

    categories = []
    for row in result.all():
        cat = row[0]
        count = row[1]
        categories.append(
            CategoryResponse(
                id=cat.id,
                name=cat.name,
                slug=cat.slug,
                color_bg=cat.color_bg,
                color_text=cat.color_text,
                display_order=cat.display_order,
                playbook_count=count,
            )
        )

    return categories


# ---------- 6. GET /series ----------
@router.get("/series", response_model=list[SeriesResponse])
async def list_series(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Series).order_by(Series.display_order.asc())
    )
    series_list = result.scalars().all()
    return [
        SeriesResponse(
            id=s.id,
            name=s.name,
            slug=s.slug,
            description=s.description,
            display_order=s.display_order,
        )
        for s in series_list
    ]


# ---------- 7. GET /my-playbooks ----------
@router.get("/my-playbooks")
async def my_playbooks(
    user: User = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Return the playbooks owned by the current user (purchased or via subscription)."""
    now = datetime.now(timezone.utc)

    # Check for active subscription
    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            Subscription.current_period_end > now,
        ).limit(1)
    )
    subscription = sub_result.scalar_one_or_none()
    is_subscriber = subscription is not None

    if is_subscriber:
        # Subscriber gets all published playbooks
        result = await db.execute(
            select(Playbook)
            .options(joinedload(Playbook.category))
            .where(Playbook.status == "published")
            .order_by(Playbook.title.asc())
        )
        playbooks = result.unique().scalars().all()
    else:
        # Get individually purchased playbooks + free playbooks
        purchased_result = await db.execute(
            select(Playbook)
            .options(joinedload(Playbook.category))
            .join(Purchase, Purchase.playbook_id == Playbook.id)
            .where(
                Purchase.user_id == user.id,
                Purchase.status == "completed",
                Playbook.status == "published",
            )
            .order_by(Playbook.title.asc())
        )
        purchased = list(purchased_result.unique().scalars().all())

        # Also include free playbooks
        free_result = await db.execute(
            select(Playbook)
            .options(joinedload(Playbook.category))
            .where(
                Playbook.status == "published",
                Playbook.pricing_type == "free",
            )
            .order_by(Playbook.title.asc())
        )
        free_playbooks = list(free_result.unique().scalars().all())

        # Merge and deduplicate (preserving order)
        seen_ids = set()
        playbooks = []
        for pb in purchased + free_playbooks:
            if pb.id not in seen_ids:
                seen_ids.add(pb.id)
                playbooks.append(pb)

        playbooks.sort(key=lambda p: p.title)

    items = []
    for pb in playbooks:
        items.append({
            "slug": pb.slug,
            "title": pb.title,
            "cover_emoji": pb.cover_emoji or "",
            "category_name": pb.category.name if pb.category else None,
        })

    response = {
        "email": user.email,
        "is_subscriber": is_subscriber,
        "playbooks": items,
    }

    if subscription:
        response["subscription"] = {
            "plan_type": subscription.plan_type,
            "price_cents": subscription.price_cents,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }

    return response
