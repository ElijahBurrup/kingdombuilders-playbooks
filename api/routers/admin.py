"""
Admin router — CRUD for playbooks, categories, series, users, promo codes,
and a basic analytics dashboard endpoint.

All endpoints require admin role via ``get_admin_user`` dependency.
"""

import secrets
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.config import settings
from api.database import get_db
from api.dependencies import get_admin_user
from api.models.audit_log import AuditLog
from api.models.email import EmailCampaign, PromoCode, Subscriber
from api.models.playbook import Category, Playbook, PlaybookAsset, Series
from api.models.purchase import Purchase, StripeCustomer, Subscription
from api.models.user import User
from api.services.audit_service import log_event

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


# ============================================================================
# Audit log viewer
# ============================================================================
@router.get("/audit")
async def list_audit_events(
    email: str | None = Query(None, description="Filter by email (substring, case-insensitive)"),
    event_type: str | None = Query(None, description="Filter by event_type prefix"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status: success/warning/error"),
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Recent audit_log rows. Used by the customer-lookup HTML page."""
    stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    if email:
        stmt = stmt.where(AuditLog.email.ilike(f"%{email.strip()}%"))
    if event_type:
        stmt = stmt.where(AuditLog.event_type.like(f"{event_type}%"))
    if status_filter:
        stmt = stmt.where(AuditLog.status == status_filter)

    result = await db.execute(stmt)
    rows = result.scalars().all()
    return {
        "items": [
            {
                "id": str(r.id),
                "timestamp": r.timestamp.isoformat(),
                "event_type": r.event_type,
                "status": r.status,
                "email": r.email,
                "user_id": str(r.user_id) if r.user_id else None,
                "provider_session_id": r.provider_session_id,
                "provider_subscription_id": r.provider_subscription_id,
                "provider_payment_id": r.provider_payment_id,
                "stripe_customer_id": r.stripe_customer_id,
                "message": r.message,
                "metadata": r.metadata_json,
                "ip_address": r.ip_address,
            }
            for r in rows
        ],
        "count": len(rows),
    }


# ============================================================================
# Reconcile user from Stripe — fix customers whose webhook silently bailed
# ============================================================================
@router.post("/reconcile-user")
async def reconcile_user_from_stripe(
    email: str = Query(..., description="Email of the customer to reconcile"),
    send_delivery_email_now: bool = Query(False, description="Resend the playbook-delivery email"),
    create_user_if_missing: bool = Query(False, description="If no User row exists, create one"),
    request: Request = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Reconcile a customer's local state with Stripe.

    Used when a Stripe webhook silently bailed (e.g., missing user_id in
    metadata) and the customer can pay but the site doesn't grant access.

    Reads from Stripe (source of truth) and creates any missing local rows:
    StripeCustomer, Subscription, Purchase.
    """
    email = email.strip().lower()
    stripe.api_key = settings.STRIPE_SECRET_KEY

    summary: dict = {
        "email": email,
        "user": None,
        "stripe_customers": [],
        "subscriptions_created": [],
        "subscriptions_existing": [],
        "purchases_created": [],
        "purchases_existing": [],
        "warnings": [],
        "delivery_email_sent": False,
    }

    # 1. Find or optionally create the User row
    result = await db.execute(select(User).where(func.lower(User.email) == email))
    user = result.scalar_one_or_none()

    if user is None and create_user_if_missing:
        user = User(
            email=email,
            display_name=email.split("@")[0],
            email_verified=True,
        )
        db.add(user)
        await db.flush()
        summary["warnings"].append(
            "Created User row (no password set — customer must use forgot-password to log in)"
        )

    if user is None:
        await log_event(
            event_type="admin.reconcile_user",
            email=email,
            status="error",
            message="No User row exists for this email",
            request=request,
        )
        raise HTTPException(
            status_code=404,
            detail=f"No user with email {email}. Pass create_user_if_missing=true to create one.",
        )

    summary["user"] = {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "email_verified": user.email_verified,
        "is_active": user.is_active,
        "role": user.role,
    }

    # 2. Look up Stripe customers by email
    try:
        # search() requires a live key. Fall back to list+filter on test keys.
        try:
            customers_resp = stripe.Customer.search(query=f"email:'{email}'")
            stripe_customers = list(customers_resp.auto_paging_iter())
        except Exception:
            customers_resp = stripe.Customer.list(email=email, limit=100)
            stripe_customers = list(customers_resp.auto_paging_iter())
    except Exception as e:
        summary["warnings"].append(f"Stripe customer lookup failed: {e}")
        await log_event(
            event_type="admin.reconcile_user",
            email=email,
            user_id=user.id,
            status="error",
            message=f"Stripe customer lookup failed: {e}",
            request=request,
        )
        return summary

    if not stripe_customers:
        summary["warnings"].append("No Stripe customer found for this email")
        await log_event(
            event_type="admin.reconcile_user",
            email=email,
            user_id=user.id,
            status="warning",
            message="No Stripe customer found",
            request=request,
        )
        await db.commit()
        return summary

    # 3. For each Stripe customer, sync StripeCustomer + Subscriptions + Purchases
    for sc_obj in stripe_customers:
        stripe_customer_id = sc_obj["id"]
        summary["stripe_customers"].append(stripe_customer_id)

        # Ensure StripeCustomer row
        sc_result = await db.execute(
            select(StripeCustomer).where(StripeCustomer.user_id == user.id)
        )
        sc_row = sc_result.scalar_one_or_none()
        if sc_row is None:
            db.add(StripeCustomer(user_id=user.id, stripe_customer_id=stripe_customer_id))
            await db.flush()
        elif sc_row.stripe_customer_id != stripe_customer_id:
            summary["warnings"].append(
                f"User already linked to {sc_row.stripe_customer_id}; "
                f"additional Stripe customer {stripe_customer_id} not linked"
            )

        # Subscriptions
        try:
            subs = list(
                stripe.Subscription.list(
                    customer=stripe_customer_id,
                    status="all",
                    limit=100,
                    expand=["data.items.data"],
                ).auto_paging_iter()
            )
        except Exception as e:
            summary["warnings"].append(f"Sub list failed for {stripe_customer_id}: {e}")
            subs = []

        for sub in subs:
            sub_id = sub["id"]
            existing = await db.execute(
                select(Subscription).where(
                    Subscription.provider_subscription_id == sub_id
                )
            )
            if existing.scalar_one_or_none():
                summary["subscriptions_existing"].append(sub_id)
                continue

            items = sub.get("items", {}).get("data", [])
            price_id = items[0]["price"]["id"] if items else ""
            if price_id == settings.STRIPE_PRICE_YEARLY:
                plan_type = "yearly"
                price_cents = items[0]["price"].get("unit_amount", 10000) if items else 10000
            elif price_id == settings.STRIPE_PRICE_MONTHLY:
                plan_type = "monthly"
                price_cents = items[0]["price"].get("unit_amount", 1000) if items else 1000
            else:
                plan_type = "monthly"
                price_cents = items[0]["price"].get("unit_amount", 0) if items else 0

            ps = sub.get("current_period_start")
            pe = sub.get("current_period_end")
            if ps is None and items:
                ps = items[0].get("current_period_start")
            if pe is None and items:
                pe = items[0].get("current_period_end")
            now = datetime.now(timezone.utc)
            ps_dt = datetime.fromtimestamp(ps, tz=timezone.utc) if ps else now
            pe_dt = datetime.fromtimestamp(pe, tz=timezone.utc) if pe else now + timedelta(days=30)

            stripe_status = sub.get("status", "active")
            if stripe_status in ("active", "trialing"):
                db_status = "active"
            elif stripe_status == "past_due":
                db_status = "past_due"
            else:
                db_status = "canceled"

            db.add(Subscription(
                user_id=user.id,
                plan_type=plan_type,
                price_cents=price_cents,
                payment_provider="stripe",
                provider_subscription_id=sub_id,
                status=db_status,
                current_period_start=ps_dt,
                current_period_end=pe_dt,
                cancel_at_period_end=sub.get("cancel_at_period_end", False),
            ))
            await db.flush()
            summary["subscriptions_created"].append({
                "id": sub_id, "plan_type": plan_type, "status": db_status,
            })

        # One-time playbook purchases — pull checkout sessions for this customer
        try:
            sessions = list(
                stripe.checkout.Session.list(
                    customer=stripe_customer_id,
                    limit=100,
                ).auto_paging_iter()
            )
        except Exception as e:
            summary["warnings"].append(f"Session list failed for {stripe_customer_id}: {e}")
            sessions = []

        for sess in sessions:
            if sess.get("payment_status") != "paid":
                continue
            if sess.get("mode") != "payment":
                continue
            session_id = sess["id"]
            existing = await db.execute(
                select(Purchase).where(Purchase.provider_session_id == session_id)
            )
            if existing.scalar_one_or_none():
                summary["purchases_existing"].append(session_id)
                continue

            metadata = sess.get("metadata") or {}
            slug = metadata.get("slug", "") or metadata.get("playbook_slug", "")
            playbook_id = None
            if slug:
                pb_result = await db.execute(
                    select(Playbook.id).where(Playbook.slug == slug)
                )
                playbook_id = pb_result.scalar_one_or_none()

            db.add(Purchase(
                user_id=user.id,
                playbook_id=playbook_id,
                payment_provider="stripe",
                provider_payment_id=f"single:{slug}" if slug else sess.get("payment_intent"),
                provider_session_id=session_id,
                amount_cents=sess.get("amount_total", 0),
                status="completed",
                download_token=secrets.token_urlsafe(32),
                downloads_remaining=99,
                download_expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            ))
            await db.flush()
            summary["purchases_created"].append({
                "session_id": session_id, "slug": slug, "amount_cents": sess.get("amount_total"),
            })

    await db.commit()

    # 4. Optionally re-send delivery email so the customer gets confirmation
    if send_delivery_email_now:
        try:
            import asyncio as _aio
            from api.services.email_service import send_delivery_email
            # If they have a recent purchase, use that slug; else send the
            # generic subscription welcome.
            slug = ""
            title = ""
            if summary["purchases_created"]:
                slug = summary["purchases_created"][0].get("slug") or ""
                if slug:
                    pb_r = await db.execute(
                        select(Playbook.title).where(Playbook.slug == slug)
                    )
                    title = pb_r.scalar_one_or_none() or ""
            if not title:
                title = "Kingdom Builders AI"
            _aio.get_running_loop().run_in_executor(
                None, send_delivery_email, user.email, "", title, slug
            )
            summary["delivery_email_sent"] = True
        except Exception as e:
            summary["warnings"].append(f"Delivery email re-send failed: {e}")

    await log_event(
        event_type="admin.reconcile_user",
        email=email,
        user_id=user.id,
        status="success",
        message=(
            f"Reconciled: {len(summary['subscriptions_created'])} subs created, "
            f"{len(summary['purchases_created'])} purchases created, "
            f"{len(summary['warnings'])} warnings"
        ),
        metadata={
            "subscriptions_created": summary["subscriptions_created"],
            "purchases_created": summary["purchases_created"],
            "warnings": summary["warnings"],
            "admin_id": str(admin.id),
        },
        request=request,
    )

    return summary


# ============================================================================
# Customer lookup HTML page — quick admin UI for the reconcile + audit endpoints
# ============================================================================
@router.get("/customer-lookup", response_class=HTMLResponse, include_in_schema=False)
async def customer_lookup_page(admin: User = Depends(get_admin_user)):
    """Tiny admin UI: type email → see audit log + reconcile button."""
    prefix = settings.URL_PREFIX or ""
    html = f"""<!DOCTYPE html>
<html><head><title>Customer Lookup</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body {{ font-family: -apple-system,Segoe UI,Arial,sans-serif; background:#FAF6ED;
       margin:0; padding:24px; color:#1A0A2E; }}
h1 {{ font-family: Georgia,serif; font-weight:600; margin:0 0 16px; }}
.panel {{ background:#fff; border:1px solid rgba(74,45,122,0.12); border-radius:8px;
         padding:20px; margin-bottom:20px; }}
input[type=email] {{ width:320px; padding:10px; font-size:15px;
                    border:1px solid rgba(74,45,122,0.2); border-radius:4px; }}
button {{ padding:10px 20px; background:#7B4FBF; color:#fff; border:0;
         border-radius:4px; font-weight:600; cursor:pointer; margin-left:8px; }}
button.danger {{ background:#B85050; }}
table {{ width:100%; border-collapse:collapse; margin-top:12px; font-size:13px; }}
th, td {{ text-align:left; padding:6px 8px; border-bottom:1px solid rgba(74,45,122,0.08); vertical-align:top; }}
th {{ background:#F2EDE3; font-weight:600; }}
.s-success {{ color:#2D7D2D; }} .s-warning {{ color:#B87A20; }} .s-error {{ color:#B83030; font-weight:600; }}
pre {{ background:#1A0A2E; color:#E8C96A; padding:12px; border-radius:4px;
       overflow:auto; font-size:12px; max-height:480px; }}
label {{ display:inline-block; margin-right:14px; font-size:14px; }}
.muted {{ color:#6B5A8A; font-size:13px; }}
</style></head>
<body>
<h1>Customer Lookup</h1>
<p class="muted">Use this when a customer paid through Stripe but the site doesn't recognize them.</p>

<div class="panel">
  <input type="email" id="email" placeholder="customer@example.com" autofocus>
  <button onclick="loadAudit()">View audit log</button>
  <button class="danger" onclick="reconcile()">Reconcile from Stripe</button>
  <div style="margin-top:12px;">
    <label><input type="checkbox" id="sendEmail"> Resend delivery email</label>
    <label><input type="checkbox" id="createUser"> Create user if missing</label>
  </div>
</div>

<div class="panel">
  <h3 style="margin:0 0 8px;">Audit log (most recent 200)</h3>
  <div id="auditOut"><p class="muted">Enter an email and click "View audit log".</p></div>
</div>

<div class="panel">
  <h3 style="margin:0 0 8px;">Reconcile result</h3>
  <pre id="reconcileOut">No reconcile run yet.</pre>
</div>

<script>
const PREFIX = "{prefix}";
const API = PREFIX + "/api/v1/admin";

function getToken() {{
  return localStorage.getItem("access_token") || "";
}}

async function loadAudit() {{
  const email = document.getElementById("email").value.trim();
  if (!email) return alert("Enter an email");
  const r = await fetch(`${{API}}/audit?email=${{encodeURIComponent(email)}}&limit=200`, {{
    headers: {{ "Authorization": "Bearer " + getToken() }},
    credentials: "include",
  }});
  if (!r.ok) {{
    document.getElementById("auditOut").innerHTML =
      `<p class="s-error">Error ${{r.status}}: ${{await r.text()}}</p>`;
    return;
  }}
  const data = await r.json();
  if (!data.items.length) {{
    document.getElementById("auditOut").innerHTML =
      `<p class="muted">No audit rows for ${{email}}.</p>`;
    return;
  }}
  let html = "<table><tr><th>When</th><th>Event</th><th>Status</th><th>Message</th><th>Refs</th></tr>";
  for (const r of data.items) {{
    const refs = [
      r.provider_session_id && "sess:" + r.provider_session_id.slice(-8),
      r.provider_subscription_id && "sub:" + r.provider_subscription_id.slice(-8),
      r.stripe_customer_id && "cus:" + r.stripe_customer_id.slice(-8),
    ].filter(Boolean).join(" ");
    html += `<tr><td>${{r.timestamp.replace("T", " ").slice(0, 19)}}</td>
      <td>${{r.event_type}}</td>
      <td class="s-${{r.status}}">${{r.status}}</td>
      <td>${{(r.message || "").replace(/[<>]/g, "")}}</td>
      <td><code>${{refs}}</code></td></tr>`;
  }}
  html += "</table>";
  document.getElementById("auditOut").innerHTML = html;
}}

async function reconcile() {{
  const email = document.getElementById("email").value.trim();
  if (!email) return alert("Enter an email");
  if (!confirm(`Reconcile ${{email}} from Stripe? This will create missing local records.`)) return;
  const params = new URLSearchParams({{
    email,
    send_delivery_email_now: document.getElementById("sendEmail").checked,
    create_user_if_missing: document.getElementById("createUser").checked,
  }});
  const r = await fetch(`${{API}}/reconcile-user?` + params, {{
    method: "POST",
    headers: {{ "Authorization": "Bearer " + getToken() }},
    credentials: "include",
  }});
  const text = await r.text();
  let pretty = text;
  try {{ pretty = JSON.stringify(JSON.parse(text), null, 2); }} catch (e) {{}}
  document.getElementById("reconcileOut").textContent = pretty;
  if (r.ok) await loadAudit();
}}

document.getElementById("email").addEventListener("keypress", e => {{
  if (e.key === "Enter") loadAudit();
}});
</script>
</body></html>"""
    return HTMLResponse(content=html)
