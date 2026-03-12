"""
Scheduler service — port of scheduler.py from the Flask app.

Uses APScheduler with a SQLAlchemy job store so that scheduled
follow-up emails survive process restarts.
"""

import hashlib
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from api.config import settings

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler | None:
    """Get or create the singleton APScheduler instance."""
    global _scheduler
    if _scheduler is None:
        try:
            db_path = settings.DATA_DIR / "scheduler.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)

            jobstores = {
                "default": SQLAlchemyJobStore(url=f"sqlite:///{db_path}")
            }

            _scheduler = BackgroundScheduler(jobstores=jobstores)
            _scheduler.start()
        except Exception as e:
            print(f"Scheduler init failed (non-fatal): {e}")
            _scheduler = None
    return _scheduler


def init_scheduler() -> None:
    """Initialize the scheduler on app startup."""
    try:
        scheduler = get_scheduler()
        if scheduler:
            # Monthly referral payout job — 1st of each month at 6 AM UTC
            scheduler.add_job(
                func="api.services.referral_service:run_monthly_payouts_sync",
                trigger="cron",
                day=1,
                hour=6,
                minute=0,
                id="monthly_referral_payouts",
                replace_existing=True,
            )
    except Exception as e:
        print(f"Scheduler startup failed (non-fatal): {e}")


def schedule_followup_emails(customer_email: str, download_token: str) -> None:
    """
    Schedule the 24-hour and 7-day follow-up emails for a purchase.

    Uses APScheduler ``date`` trigger with string-based function references
    so the jobs can be serialized to the SQLite job store.
    """
    scheduler = get_scheduler()

    # Email 2: Quick Start Guide — 24 hours later
    scheduler.add_job(
        func="api.services.email_service:send_quickstart_email",
        trigger="date",
        run_date=datetime.now(timezone.utc) + timedelta(hours=24),
        args=[customer_email, download_token],
        id=f"quickstart_{download_token}",
        replace_existing=True,
    )

    # Email 3: The Compound Effect — 7 days later
    scheduler.add_job(
        func="api.services.email_service:send_compound_email",
        trigger="date",
        run_date=datetime.now(timezone.utc) + timedelta(days=7),
        args=[customer_email, download_token],
        id=f"compound_{download_token}",
        replace_existing=True,
    )


def schedule_nurture_sequence(email: str) -> None:
    """
    Schedule the 4-email nurture drip sequence for a new subscriber.

    Email 1 (lead magnet) is sent immediately by the subscribe endpoint.
    This schedules emails 2-5 at day 2, 5, 8, and 12.
    """
    scheduler = get_scheduler()
    if scheduler is None:
        print(f"Scheduler unavailable — nurture sequence not scheduled for {email}")
        return

    email_hash = hashlib.sha256(email.encode()).hexdigest()[:12]

    # Nurture Email 2: "The Playbook You Didn't Expect" — 2 days later
    scheduler.add_job(
        func="api.services.email_service:send_nurture_day2",
        trigger="date",
        run_date=datetime.now(timezone.utc) + timedelta(days=2),
        args=[email],
        id=f"nurture_day2_{email_hash}",
        replace_existing=True,
    )

    # Nurture Email 3: "Why Animals?" — 5 days later
    scheduler.add_job(
        func="api.services.email_service:send_nurture_day5",
        trigger="date",
        run_date=datetime.now(timezone.utc) + timedelta(days=5),
        args=[email],
        id=f"nurture_day5_{email_hash}",
        replace_existing=True,
    )

    # Nurture Email 4: "The 3 Most Popular" — 8 days later
    scheduler.add_job(
        func="api.services.email_service:send_nurture_day8",
        trigger="date",
        run_date=datetime.now(timezone.utc) + timedelta(days=8),
        args=[email],
        id=f"nurture_day8_{email_hash}",
        replace_existing=True,
    )

    # Nurture Email 5: "Unlock Everything" — 12 days later
    scheduler.add_job(
        func="api.services.email_service:send_nurture_day12",
        trigger="date",
        run_date=datetime.now(timezone.utc) + timedelta(days=12),
        args=[email],
        id=f"nurture_day12_{email_hash}",
        replace_existing=True,
    )
