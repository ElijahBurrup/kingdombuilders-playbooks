from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

import config

_scheduler = None


def get_scheduler():
    """Get or create the singleton scheduler."""
    global _scheduler
    if _scheduler is None:
        db_path = config.DATA_DIR / "scheduler.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        jobstores = {
            "default": SQLAlchemyJobStore(url=f"sqlite:///{db_path}")
        }

        _scheduler = BackgroundScheduler(jobstores=jobstores)
        _scheduler.start()
    return _scheduler


def init_scheduler():
    """Initialize the scheduler on app startup."""
    get_scheduler()


def schedule_followup_emails(customer_email, download_token):
    """Schedule the 24-hour and 7-day follow-up emails."""
    scheduler = get_scheduler()

    # Email 2: Quick Start Guide — 24 hours later
    scheduler.add_job(
        func="emails:send_quickstart_email",
        trigger="date",
        run_date=datetime.now(timezone.utc) + timedelta(hours=24),
        args=[customer_email, download_token],
        id=f"quickstart_{download_token}",
        replace_existing=True,
    )

    # Email 3: The Compound Effect — 7 days later
    scheduler.add_job(
        func="emails:send_compound_email",
        trigger="date",
        run_date=datetime.now(timezone.utc) + timedelta(days=7),
        args=[customer_email, download_token],
        id=f"compound_{download_token}",
        replace_existing=True,
    )
