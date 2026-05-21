"""
Monitoring service — scheduled background jobs that surface silent failures
in the sign-up + payment pipeline.

Two scheduled jobs:

1. `run_nightly_reconcile_sync()` — every night, list every active Stripe
   subscription, check it has a matching local Subscription row, and call
   reconcile-user for any drift. Catches webhooks that silently failed.

2. `run_daily_audit_digest_sync()` — every morning, query audit_log for any
   row with status='error' or 'warning' in the last 24h. Email a digest to
   the admin so silent failures surface within a day.

Both jobs are designed to be safe to run repeatedly (idempotent reconcile,
empty-digest = no email sent).

Both have *_sync wrappers because APScheduler with a SQLAlchemy job store
needs serializable, sync function references — we run the async work via
asyncio.run() inside the sync wrapper.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import resend
import stripe
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.config import settings
from api.models.audit_log import AuditLog
from api.models.purchase import StripeCustomer, Subscription
from api.models.user import User
from api.services.audit_service import log_event


# ---------------------------------------------------------------------------
# Cron-isolated DB session.
#
# The app's main `async_session` is tied to an engine whose asyncpg
# connections were created on the main FastAPI event loop. The APScheduler
# `BackgroundScheduler` runs jobs in WORKER THREADS, where we call
# `asyncio.run()` to create a *new* event loop. asyncpg connections are
# loop-bound; reusing the main pool from a different loop corrupts the
# pool and produces `InterfaceError: another operation is in progress`
# for every subsequent request on the affected connection. That bug was
# silently breaking login until this isolation was added.
#
# Each cron run gets its own engine + sessionmaker scoped to the new
# loop, and disposes the engine when the run completes.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def _cron_session():
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=2,
        max_overflow=0,
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as session:
            yield session
    finally:
        await engine.dispose()

resend.api_key = settings.RESEND_API_KEY
stripe.api_key = settings.STRIPE_SECRET_KEY

# Where digest + nightly-reconcile summary emails go.
ADMIN_EMAIL = "elijah@kingdombuilders.ai"


# =============================================================================
# Nightly reconcile — pull Stripe truth, fix any local drift
# =============================================================================
async def run_nightly_reconcile() -> dict:
    """List every active/trialing Stripe subscription, ensure local row exists.

    Returns a summary dict. Sends an email to ADMIN_EMAIL if any drift
    was found and fixed (or any failures occurred).
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    fixed: list[dict] = []
    missing_user: list[dict] = []
    failed: list[dict] = []
    scanned = 0

    try:
        subs_iter = stripe.Subscription.list(
            status="active",
            limit=100,
            expand=["data.items.data"],
        ).auto_paging_iter()
    except Exception as e:
        await log_event(
            event_type="cron.nightly_reconcile",
            status="error",
            message=f"Stripe list call failed: {e}",
        )
        return {"error": str(e), "scanned": 0, "fixed": [], "failed": [], "missing_user": []}

    async with _cron_session() as db:
        for sub_obj in subs_iter:
            scanned += 1
            try:
                sub = json.loads(str(sub_obj))
            except Exception as e:
                failed.append({"err": f"Could not parse sub: {e}"})
                continue

            sub_id = sub.get("id", "")
            customer_id = sub.get("customer", "")
            if not sub_id or not customer_id:
                continue

            # Already present? Skip.
            existing = await db.execute(
                select(Subscription).where(
                    Subscription.provider_subscription_id == sub_id
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Local row is missing. Find the user via Stripe customer email.
            try:
                customer = stripe.Customer.retrieve(customer_id)
                email = (getattr(customer, "email", "") or "").strip().lower()
            except Exception as e:
                failed.append({"sub_id": sub_id, "err": f"Customer retrieve failed: {e}"})
                continue

            if not email:
                failed.append({"sub_id": sub_id, "err": "Stripe customer has no email"})
                continue

            user_row = await db.execute(
                select(User).where(func.lower(User.email) == email)
            )
            user = user_row.scalar_one_or_none()
            if user is None:
                missing_user.append({"sub_id": sub_id, "email": email})
                continue

            # Ensure StripeCustomer link
            sc_row = await db.execute(
                select(StripeCustomer).where(StripeCustomer.user_id == user.id)
            )
            if sc_row.scalar_one_or_none() is None:
                db.add(StripeCustomer(
                    user_id=user.id, stripe_customer_id=customer_id,
                ))
                await db.flush()

            # Build Subscription row from Stripe truth
            items = (sub.get("items") or {}).get("data") or []
            first_price = (items[0].get("price") or {}) if items else {}
            price_id = first_price.get("id", "")
            if price_id == settings.STRIPE_PRICE_YEARLY:
                plan_type, default_price = "yearly", 10000
            elif price_id == settings.STRIPE_PRICE_MONTHLY:
                plan_type, default_price = "monthly", 1000
            else:
                plan_type, default_price = "monthly", 0
            price_cents = first_price.get("unit_amount") or default_price

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
            db_status = "active" if stripe_status in ("active", "trialing") else (
                "past_due" if stripe_status == "past_due" else "canceled"
            )

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

            fixed.append({"sub_id": sub_id, "email": email, "plan_type": plan_type})

            await log_event(
                event_type="cron.nightly_reconcile",
                email=email,
                user_id=user.id,
                provider_subscription_id=sub_id,
                stripe_customer_id=customer_id,
                status="warning",
                message="Nightly cron auto-created missing Subscription row",
                metadata={"plan_type": plan_type, "stripe_status": stripe_status},
            )

        await db.commit()

    summary = {
        "scanned": scanned,
        "fixed": fixed,
        "missing_user": missing_user,
        "failed": failed,
    }

    # Only email if there's actually something to flag.
    if fixed or missing_user or failed:
        _send_nightly_reconcile_email(summary)

    await log_event(
        event_type="cron.nightly_reconcile",
        status="success" if not failed else "warning",
        message=(
            f"Scanned {scanned} subs, auto-fixed {len(fixed)}, "
            f"{len(missing_user)} have no local user, {len(failed)} failed"
        ),
        metadata=summary,
    )

    return summary


def run_nightly_reconcile_sync() -> None:
    """APScheduler-compatible sync entry point."""
    try:
        asyncio.run(run_nightly_reconcile())
    except Exception as e:
        print(f"[monitoring] nightly reconcile crashed: {e}")


def _send_nightly_reconcile_email(summary: dict) -> None:
    rows_fixed = "".join(
        f"<tr><td>{f['email']}</td><td>{f['plan_type']}</td>"
        f"<td><code>{f['sub_id']}</code></td></tr>"
        for f in summary["fixed"]
    ) or "<tr><td colspan=3 style='color:#888'>None</td></tr>"

    rows_no_user = "".join(
        f"<tr><td>{m['email']}</td><td><code>{m['sub_id']}</code></td></tr>"
        for m in summary["missing_user"]
    ) or "<tr><td colspan=2 style='color:#888'>None</td></tr>"

    rows_failed = "".join(
        f"<tr><td><code>{f.get('sub_id','-')}</code></td><td>{f['err']}</td></tr>"
        for f in summary["failed"]
    ) or "<tr><td colspan=2 style='color:#888'>None</td></tr>"

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:700px;margin:0 auto;padding:24px;">
      <h2 style="font-family:Georgia,serif;color:#1A0A2E;">Nightly Reconcile Report</h2>
      <p style="color:#3A2A55;">Scanned {summary['scanned']} active Stripe subscriptions.
        Auto-fixed {len(summary['fixed'])} missing local rows.</p>

      <h3 style="color:#2D7D2D;">Fixed ({len(summary['fixed'])})</h3>
      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;">
        <tr><th>Email</th><th>Plan</th><th>Stripe Sub ID</th></tr>
        {rows_fixed}
      </table>

      <h3 style="color:#B87A20;">Missing local user ({len(summary['missing_user'])})</h3>
      <p style="font-size:13px;color:#6B5A8A;">These customers paid via Stripe but have no
        User row. They probably checked out as guests. Investigate or invite them to register.</p>
      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;">
        <tr><th>Stripe Email</th><th>Stripe Sub ID</th></tr>
        {rows_no_user}
      </table>

      <h3 style="color:#B83030;">Failures ({len(summary['failed'])})</h3>
      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;">
        <tr><th>Sub ID</th><th>Error</th></tr>
        {rows_failed}
      </table>

      <p style="font-size:12px;color:#888;margin-top:24px;">
        Admin lookup: <a href="{settings.BASE_URL}/playbooks/api/v1/admin/customer-lookup">
        {settings.BASE_URL}/playbooks/api/v1/admin/customer-lookup</a>
      </p>
    </div>
    """
    try:
        resend.Emails.send({
            "from": "Kingdom Builders AI <playbook@kingdombuilders.ai>",
            "to": ADMIN_EMAIL,
            "subject": f"[KB Playbooks] Nightly reconcile — {len(summary['fixed'])} fixed, "
                       f"{len(summary['missing_user'])} missing user, "
                       f"{len(summary['failed'])} failed",
            "html": html,
        })
    except Exception as e:
        print(f"[monitoring] nightly reconcile email failed: {e}")


# =============================================================================
# Daily audit_log error digest
# =============================================================================
async def run_daily_audit_digest() -> int:
    """Find audit_log rows with status='error' or 'warning' from the last 24h
    and email an admin digest. Returns the number of rows in the digest.

    No-op silently if there are no error/warning rows — no spam emails.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    async with _cron_session() as db:
        rows_q = await db.execute(
            select(AuditLog)
            .where(AuditLog.timestamp >= cutoff)
            .where(AuditLog.status.in_(["error", "warning"]))
            .order_by(desc(AuditLog.timestamp))
            .limit(500)
        )
        rows = rows_q.scalars().all()

    if not rows:
        # Quiet success — log so we know the cron ran, but no email
        await log_event(
            event_type="cron.audit_digest",
            status="success",
            message="No error/warning rows in last 24h — no digest sent",
        )
        return 0

    # Bucket by event_type for the email summary
    by_type: dict[str, int] = {}
    for r in rows:
        by_type[r.event_type] = by_type.get(r.event_type, 0) + 1

    summary_rows = "".join(
        f"<tr><td>{t}</td><td style='text-align:right;'>{c}</td></tr>"
        for t, c in sorted(by_type.items(), key=lambda kv: -kv[1])
    )

    detail_rows = "".join(
        f"""<tr>
          <td>{r.timestamp.strftime('%H:%M:%S')}</td>
          <td>{r.event_type}</td>
          <td style='color:{"#B83030" if r.status == "error" else "#B87A20"};'>{r.status}</td>
          <td>{(r.email or '')[:40]}</td>
          <td>{(r.message or '')[:160]}</td>
        </tr>"""
        for r in rows[:100]  # Cap email size at 100 detail rows
    )
    truncated_note = (
        f"<p style='color:#888;font-size:13px;'>"
        f"Showing 100 of {len(rows)} rows. See "
        f"<a href='{settings.BASE_URL}/playbooks/api/v1/admin/customer-lookup'>"
        f"admin lookup</a> for full audit log.</p>"
        if len(rows) > 100 else ""
    )

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:760px;margin:0 auto;padding:24px;">
      <h2 style="font-family:Georgia,serif;color:#1A0A2E;">Audit Log Digest — Last 24h</h2>
      <p style="color:#3A2A55;">
        <strong>{len(rows)}</strong> warning/error events recorded in the sign-up + payment pipeline.
      </p>

      <h3 style="color:#1A0A2E;">By event type</h3>
      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
        <tr><th>Event Type</th><th>Count</th></tr>
        {summary_rows}
      </table>

      <h3 style="color:#1A0A2E;">Detail</h3>
      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;font-size:13px;">
        <tr><th>Time UTC</th><th>Event</th><th>Status</th><th>Email</th><th>Message</th></tr>
        {detail_rows}
      </table>
      {truncated_note}

      <p style="font-size:12px;color:#888;margin-top:24px;">
        <a href="{settings.BASE_URL}/playbooks/api/v1/admin/customer-lookup">Admin lookup</a>
        — search by email, view full audit log, reconcile from Stripe.
      </p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": "Kingdom Builders AI <playbook@kingdombuilders.ai>",
            "to": ADMIN_EMAIL,
            "subject": f"[KB Playbooks] {len(rows)} audit warnings/errors in last 24h",
            "html": html,
        })
        await log_event(
            event_type="cron.audit_digest",
            status="success",
            message=f"Sent digest with {len(rows)} rows",
            metadata={"counts_by_type": by_type},
        )
    except Exception as e:
        print(f"[monitoring] audit digest email failed: {e}")
        await log_event(
            event_type="cron.audit_digest",
            status="error",
            message=f"Email send failed: {e}",
        )

    return len(rows)


def run_daily_audit_digest_sync() -> None:
    """APScheduler-compatible sync entry point."""
    try:
        asyncio.run(run_daily_audit_digest())
    except Exception as e:
        print(f"[monitoring] daily audit digest crashed: {e}")
