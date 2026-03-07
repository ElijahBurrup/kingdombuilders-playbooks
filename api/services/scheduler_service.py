"""
Scheduler service — port of scheduler.py from the Flask app.

Uses APScheduler with a SQLAlchemy job store so that scheduled
follow-up emails survive process restarts.
"""

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
        get_scheduler()
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
