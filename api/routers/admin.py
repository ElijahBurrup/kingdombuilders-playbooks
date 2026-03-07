"""
Admin router — CRUD for playbooks, categories, series, users, promo codes,
and a basic analytics dashboard endpoint.

All endpoints require admin role via ``get_admin_user`` dependency.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.database import get_db
from api.dependencies import get_admin_user
from api.models.email import EmailCampaign, PromoCode, Subscriber
from api.models.playbook import Category, Playbook, PlaybookAsset, Series
from api.models.purchase import Purchase, Subscription
from api.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_admin_user)])


# ============================================================================
# Analytics dashboard
# ============================================================================
@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_playbooks = (await db.execute(select(func.count(Playbook.id)))).scalar() or 0
    total_purchases = (await db.execute(
        select(func.count(Purchase.id)).where(Purchase.status == "completed")
    )).scalar() or 0
    total_revenue = (await db.execute(
        select(func.coalesce(func.sum(Purchase.amount_cents), 0)).where(
            Purchase.status == "completed"
        )
    )).scalar() or 0
    total_subscribers = (await db.execute(
        select(func.count(Subscriber.id)).where(Subscriber.unsubscribed == False)  # noqa: E712
    )).scalar() or 0
    active_subscriptions = (await db.execute(
        select(func.count(Subscription.id)).where(Subscription.status == "active")
    )).scalar() or 0

    return {
        "total_users": total_users,
        "total_playbooks": total_playbooks,
        "total_purchases": total_purchases,
        "total_revenue_cents": total_revenue,
        "total_subscribers": total_subscribers,
        "active_subscriptions": active_subscriptions,
    }


# ============================================================================
# Playbook CRUD
# ============================================================================
@router.get("/playbooks")
async def list_all_playbooks(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    total = (await db.execute(select(func.count(Playbook.id)))).scalar() or 0
    result = await db.execute(
        select(Playbook)
        .options(joinedload(Playbook.category), joinedload(Playbook.series))
        .order_by(Playbook.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    playbooks = result.unique().scalars().all()
    return {
        "items": [
            {
                "id": str(pb.id),
                "slug": pb.slug,
                "title": pb.title,
                "status": pb.status,
                "pricing_type": pb.pricing_type,
                "price_cents": pb.price_cents,
                "category": pb.category.name if pb.category else None,
                "series": pb.series.name if pb.series else None,
                "view_count": pb.view_count,
                "purchase_count": pb.purchase_count,
                "published_at": pb.published_at.isoformat() if pb.published_at else None,
            }
            for pb in playbooks
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("/playbooks", status_code=status.HTTP_201_CREATED)
async def create_playbook(body: dict, db: AsyncSession = Depends(get_db)):
    playbook = Playbook(
        slug=body["slug"],
        title=body["title"],
        subtitle=body.get("subtitle"),
        description=body["description"],
        landing_html=body.get("landing_html", ""),
        content_html=body.get("content_html", ""),
        pricing_type=body.get("pricing_type", "paid"),
        price_cents=body.get("price_cents", 250),
        category_id=body["category_id"],
        series_id=body.get("series_id"),
        series_order=body.get("series_order"),
        cover_emoji=body.get("cover_emoji"),
        status=body.get("status", "draft"),
    )
    if body.get("status") == "published":
        playbook.published_at = datetime.now(timezone.utc)
    db.add(playbook)
    await db.commit()
    await db.refresh(playbook)
    return {"id": str(playbook.id), "slug": playbook.slug}


@router.patch("/playbooks/{playbook_id}")
async def update_playbook(
    playbook_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Playbook).where(Playbook.id == playbook_id))
    playbook = result.scalar_one_or_none()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    for field in [
        "title", "subtitle", "slug", "description", "landing_html",
        "content_html", "pricing_type", "price_cents", "category_id",
        "series_id", "series_order", "cover_emoji", "featured",
        "cover_gradient_start", "cover_gradient_end",
    ]:
        if field in body:
            setattr(playbook, field, body[field])

    if "status" in body:
        playbook.status = body["status"]
        if body["status"] == "published" and playbook.published_at is None:
            playbook.published_at = datetime.now(timezone.utc)

    playbook.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": str(playbook.id), "slug": playbook.slug}


@router.delete("/playbooks/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playbook(playbook_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Playbook).where(Playbook.id == playbook_id))
    playbook = result.scalar_one_or_none()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    await db.delete(playbook)
    await db.commit()


# ============================================================================
# Category CRUD
# ============================================================================
@router.get("/categories")
async def list_all_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.display_order))
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "slug": c.slug,
            "color_bg": c.color_bg,
            "color_text": c.color_text,
            "display_order": c.display_order,
        }
        for c in result.scalars().all()
    ]


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(body: dict, db: AsyncSession = Depends(get_db)):
    cat = Category(
        name=body["name"],
        slug=body["slug"],
        color_bg=body.get("color_bg", "rgba(123,79,191,0.08)"),
        color_text=body.get("color_text", "#7B4FBF"),
        display_order=body.get("display_order", 0),
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return {"id": str(cat.id), "name": cat.name}


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(cat)
    await db.commit()


# ============================================================================
# Series CRUD
# ============================================================================
@router.get("/series")
async def list_all_series(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Series).order_by(Series.display_order))
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "slug": s.slug,
            "description": s.description,
            "display_order": s.display_order,
        }
        for s in result.scalars().all()
    ]


@router.post("/series", status_code=status.HTTP_201_CREATED)
async def create_series(body: dict, db: AsyncSession = Depends(get_db)):
    s = Series(
        name=body["name"],
        slug=body["slug"],
        description=body.get("description"),
        display_order=body.get("display_order", 0),
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return {"id": str(s.id), "name": s.name}


# ============================================================================
# User management
# ============================================================================
@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    total = (await db.execute(select(func.count(User.id)))).scalar() or 0
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(per_page)
    )
    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "display_name": u.display_name,
                "role": u.role,
                "is_active": u.is_active,
                "email_verified": u.email_verified,
                "created_at": u.created_at.isoformat(),
            }
            for u in result.scalars().all()
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field in ["role", "is_active", "display_name"]:
        if field in body:
            setattr(user, field, body[field])

    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": str(user.id), "email": user.email, "role": user.role}


# ============================================================================
# Promo codes
# ============================================================================
@router.get("/promo-codes")
async def list_promo_codes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromoCode).order_by(PromoCode.created_at.desc()))
    return [
        {
            "id": str(p.id),
            "code": p.code,
            "discount_type": p.discount_type,
            "discount_value": p.discount_value,
            "max_uses": p.max_uses,
            "current_uses": p.current_uses,
            "valid_from": p.valid_from.isoformat(),
            "valid_until": p.valid_until.isoformat() if p.valid_until else None,
        }
        for p in result.scalars().all()
    ]


@router.post("/promo-codes", status_code=status.HTTP_201_CREATED)
async def create_promo_code(body: dict, db: AsyncSession = Depends(get_db)):
    promo = PromoCode(
        code=body["code"].upper(),
        discount_type=body.get("discount_type", "percent"),
        discount_value=body["discount_value"],
        max_uses=body.get("max_uses"),
        valid_from=body.get("valid_from", datetime.now(timezone.utc)),
        valid_until=body.get("valid_until"),
    )
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return {"id": str(promo.id), "code": promo.code}


@router.delete("/promo-codes/{promo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promo_code(promo_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromoCode).where(PromoCode.id == promo_id))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    await db.delete(promo)
    await db.commit()
