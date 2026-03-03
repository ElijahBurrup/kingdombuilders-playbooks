"""
Migration script — reads data from the existing SQLite database and
writes it into the new PostgreSQL tables.

Migrates: purchases, download_logs, email_log, subscribers.

Usage:
    python -m scripts.migrate_sqlite_to_pg
"""

import asyncio
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.config import settings
from api.database import async_session
from api.models.purchase import Purchase
from api.models.activity import DownloadLog
from api.models.email import EmailLog, Subscriber


def _get_sqlite_connection() -> sqlite3.Connection:
    """Open the existing SQLite database."""
    db_path = settings.DATA_DIR / "playbook.db"
    if not db_path.exists():
        print(f"SQLite database not found at {db_path}")
        print("Nothing to migrate.")
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


async def migrate():
    conn = _get_sqlite_connection()
    if conn is None:
        return

    print("Starting SQLite → PostgreSQL migration...")

    async with async_session() as db:
        # ── Purchases ──────────────────────────────────────────────
        rows = conn.execute("SELECT * FROM purchases ORDER BY id").fetchall()
        print(f"\nMigrating {len(rows)} purchases...")
        purchase_id_map = {}  # sqlite_id → new uuid

        for row in rows:
            # Check for duplicates by stripe_session_id
            existing = (await db.execute(
                select(Purchase).where(
                    Purchase.provider_session_id == row["stripe_session_id"]
                )
            )).scalar_one_or_none()

            if existing:
                purchase_id_map[row["id"]] = existing.id
                print(f"  Purchase {row['id']} already migrated (session: {row['stripe_session_id'][:20]}...)")
                continue

            new_id = uuid4()
            purchase_id_map[row["id"]] = new_id

            # Parse expires_at
            try:
                expires_at = datetime.fromisoformat(row["expires_at"])
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                expires_at = datetime.now(timezone.utc) + timedelta(days=30)

            # Parse created_at
            try:
                created_at = datetime.fromisoformat(row["created_at"])
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                created_at = datetime.now(timezone.utc)

            purchase = Purchase(
                id=new_id,
                payment_provider="stripe",
                provider_payment_id=row["stripe_payment_intent"],
                provider_session_id=row["stripe_session_id"],
                amount_cents=row["amount_cents"],
                status="refunded" if row["refunded"] else "completed",
                download_token=row["download_token"],
                downloads_remaining=row["downloads_remaining"],
                download_expires_at=expires_at,
                created_at=created_at,
            )
            db.add(purchase)
            print(f"  Migrated purchase {row['id']} → {new_id}")

        await db.flush()

        # ── Download Logs ──────────────────────────────────────────
        rows = conn.execute("SELECT * FROM download_logs ORDER BY id").fetchall()
        print(f"\nMigrating {len(rows)} download logs...")

        for row in rows:
            purchase_uuid = purchase_id_map.get(row["purchase_id"])
            if not purchase_uuid:
                print(f"  Skipping download log {row['id']}: purchase {row['purchase_id']} not mapped")
                continue

            try:
                downloaded_at = datetime.fromisoformat(row["downloaded_at"])
                if downloaded_at.tzinfo is None:
                    downloaded_at = downloaded_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                downloaded_at = datetime.now(timezone.utc)

            log = DownloadLog(
                purchase_id=purchase_uuid,
                ip_address=row["ip_address"],
                user_agent=row["user_agent"],
                downloaded_at=downloaded_at,
            )
            db.add(log)

        await db.flush()
        print(f"  Done.")

        # ── Email Log ──────────────────────────────────────────────
        rows = conn.execute("SELECT * FROM email_log ORDER BY id").fetchall()
        print(f"\nMigrating {len(rows)} email log entries...")

        for row in rows:
            purchase_uuid = purchase_id_map.get(row["purchase_id"])
            if not purchase_uuid:
                print(f"  Skipping email log {row['id']}: purchase {row['purchase_id']} not mapped")
                continue

            try:
                sent_at = datetime.fromisoformat(row["sent_at"])
                if sent_at.tzinfo is None:
                    sent_at = sent_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                sent_at = datetime.now(timezone.utc)

            # Look up the purchase's email for recipient_email
            purchase_uuid = purchase_id_map.get(row["purchase_id"])
            purchase_email = ""
            if purchase_uuid:
                purchase_row = conn.execute(
                    "SELECT customer_email FROM purchases WHERE id = ?",
                    (row["purchase_id"],)
                ).fetchone()
                if purchase_row:
                    purchase_email = purchase_row["customer_email"]

            email_log = EmailLog(
                recipient_email=purchase_email or "unknown@migrated.local",
                email_type=row["email_type"],
                resend_id=row.get("resend_id"),
                sent_at=sent_at,
            )
            db.add(email_log)

        await db.flush()
        print(f"  Done.")

        # ── Subscribers ────────────────────────────────────────────
        rows = conn.execute("SELECT * FROM subscribers ORDER BY id").fetchall()
        print(f"\nMigrating {len(rows)} subscribers...")

        for row in rows:
            existing = (await db.execute(
                select(Subscriber).where(Subscriber.email == row["email"])
            )).scalar_one_or_none()

            if existing:
                print(f"  Subscriber '{row['email']}' already exists")
                continue

            try:
                created_at = datetime.fromisoformat(row["created_at"])
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                created_at = datetime.now(timezone.utc)

            subscriber = Subscriber(
                email=row["email"],
                source=row["source"],
                created_at=created_at,
            )
            db.add(subscriber)
            print(f"  Migrated subscriber: {row['email']}")

        await db.commit()

    conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())
