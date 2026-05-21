"""Audit logging — fire-and-forget records for the sign-up + payment pipeline.

USAGE
-----
From inside an async handler that already has a db session:

    from api.services.audit_service import log_event
    await log_event(
        db,
        event_type="webhook.checkout_completed",
        email=customer_email,
        user_id=user_id,
        provider_session_id=session_id,
        message="Created Purchase row, granted access.",
        status="success",
    )

Safety contract
---------------
This function is designed to NEVER raise. If the audit write fails, we print
the failure and return — we never let logging take down a webhook handler.
Webhooks are user-facing; audit logs are observability. Observability must
never break the user-facing path.

We use a SEPARATE database session (independent of the caller's session) so:
  - An audit log commit happens even if the caller's transaction is about
    to roll back. (Useful for logging webhook failures BEFORE re-raising.)
  - We don't pollute the caller's session with our writes.
"""

import asyncio
import weakref
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.config import settings
from api.database import async_session as _main_async_session
from api.models.audit_log import AuditLog


# ---------------------------------------------------------------------------
# Per-event-loop session factory.
#
# `log_event` gets called from BOTH the main FastAPI event loop AND from
# BackgroundScheduler-spawned event loops in worker threads. asyncpg
# connections are loop-bound; sharing the main pool across loops corrupts
# it. We keep one engine per loop, weakly keyed so loops can be GC'd.
# The main loop uses the shared `async_session` from api.database.
# ---------------------------------------------------------------------------
_per_loop_factories: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, tuple]" = (
    weakref.WeakKeyDictionary()
)


def _session_factory_for_current_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return _main_async_session
    cached = _per_loop_factories.get(loop)
    if cached is not None:
        return cached[1]
    # Lazily create a small engine pinned to this loop. The cron jobs that
    # spin up a fresh loop only need a tiny pool; we keep pool_size small.
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=2,
        max_overflow=0,
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    _per_loop_factories[loop] = (engine, factory)
    return factory


async def log_event(
    db: Optional[AsyncSession] = None,
    *,
    event_type: str,
    email: Optional[str] = None,
    user_id: Optional[Any] = None,
    provider_session_id: Optional[str] = None,
    provider_subscription_id: Optional[str] = None,
    provider_payment_id: Optional[str] = None,
    stripe_customer_id: Optional[str] = None,
    message: Optional[str] = None,
    metadata: Optional[dict] = None,
    status: str = "success",
    request: Optional[Request] = None,
) -> None:
    """Write a single audit_log row. Never raises.

    db is accepted for callers that want to share their existing session, but
    we always open our OWN session for the write so the audit write is
    durable even when the caller's transaction rolls back. (We accept `db`
    only for API symmetry; we do not actually use it.)
    """
    ip = None
    ua = None
    if request is not None:
        try:
            ip = request.client.host if request.client else None
            ua = request.headers.get("user-agent")
            if ua and len(ua) > 510:
                ua = ua[:510]
        except Exception:
            pass

    try:
        factory = _session_factory_for_current_loop()
        async with factory() as session:
            row = AuditLog(
                event_type=event_type,
                status=status,
                email=(email or None),
                user_id=user_id,
                provider_session_id=provider_session_id,
                provider_subscription_id=provider_subscription_id,
                provider_payment_id=provider_payment_id,
                stripe_customer_id=stripe_customer_id,
                message=message,
                metadata_json=metadata,
                ip_address=ip,
                user_agent=ua,
                timestamp=datetime.now(timezone.utc),
            )
            session.add(row)
            await session.commit()
    except Exception as e:
        # Last resort: stdout. Never let logging break the user-facing path.
        print(f"[audit_service] Failed to write audit_log "
              f"event_type={event_type} email={email}: {e}")


def log_event_sync_safe(**kwargs) -> None:
    """Fire-and-forget audit log from a sync context.

    Schedules log_event on the running event loop without awaiting.
    Useful from sync code paths (e.g., email sender threads) where we
    can't await but still want the audit row written.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(log_event(**kwargs))
        else:
            asyncio.run(log_event(**kwargs))
    except Exception as e:
        print(f"[audit_service] sync wrapper failed: {e}")
