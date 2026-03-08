import sqlite3
import threading
from datetime import datetime, timedelta, timezone

import config

_local = threading.local()

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS purchases (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    stripe_session_id     TEXT NOT NULL UNIQUE,
    stripe_payment_intent TEXT,
    customer_email        TEXT NOT NULL,
    download_token        TEXT NOT NULL UNIQUE,
    downloads_remaining   INTEGER NOT NULL DEFAULT 5,
    expires_at            TEXT NOT NULL,
    amount_cents          INTEGER NOT NULL,
    refunded              INTEGER NOT NULL DEFAULT 0,
    email_opted_out       INTEGER NOT NULL DEFAULT 0,
    created_at            TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS download_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id   INTEGER NOT NULL REFERENCES purchases(id),
    ip_address    TEXT,
    user_agent    TEXT,
    downloaded_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS email_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id),
    email_type  TEXT NOT NULL,
    sent_at     TEXT NOT NULL DEFAULT (datetime('now')),
    resend_id   TEXT
);

CREATE INDEX IF NOT EXISTS idx_purchases_token ON purchases(download_token);
CREATE INDEX IF NOT EXISTS idx_purchases_session ON purchases(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_purchases_email ON purchases(customer_email);
CREATE INDEX IF NOT EXISTS idx_download_logs_purchase ON download_logs(purchase_id);
CREATE INDEX IF NOT EXISTS idx_email_log_purchase ON email_log(purchase_id);

CREATE TABLE IF NOT EXISTS subscribers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT NOT NULL UNIQUE,
    source     TEXT NOT NULL DEFAULT 'salmon-journey-ch1',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);

CREATE TABLE IF NOT EXISTS playbook_views (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT NOT NULL,
    ip_address  TEXT,
    user_agent  TEXT,
    viewed_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_playbook_views_slug ON playbook_views(slug);

CREATE TABLE IF NOT EXISTS playbook_exits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT NOT NULL,
    scroll_percent  REAL NOT NULL DEFAULT 0,
    time_spent_secs INTEGER NOT NULL DEFAULT 0,
    ip_address      TEXT,
    exited_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_playbook_exits_slug ON playbook_exits(slug);
"""


def get_connection():
    """Get a thread-local SQLite connection."""
    if not hasattr(_local, "connection") or _local.connection is None:
        db_path = config.DATA_DIR / "playbook.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.connection = conn
    return _local.connection


def initialize_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)

    # Set schema version if not present
    row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    if row is None:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    conn.commit()


# --- Purchase Queries ---

def create_purchase(stripe_session_id, customer_email, download_token,
                    downloads_remaining, expires_at, stripe_payment_intent=None,
                    amount_cents=0):
    """Insert a new purchase record."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO purchases
           (stripe_session_id, stripe_payment_intent, customer_email,
            download_token, downloads_remaining, expires_at, amount_cents)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (stripe_session_id, stripe_payment_intent, customer_email,
         download_token, downloads_remaining, expires_at.isoformat(),
         amount_cents)
    )
    conn.commit()


def get_purchase_by_session_id(session_id):
    """Look up a purchase by Stripe session ID."""
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM purchases WHERE stripe_session_id = ?",
        (session_id,)
    ).fetchone()


def get_purchase_by_token(token):
    """Look up a purchase by download token."""
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM purchases WHERE download_token = ?",
        (token,)
    ).fetchone()


def decrement_download(purchase_id):
    """Decrement the download counter for a purchase."""
    conn = get_connection()
    conn.execute(
        """UPDATE purchases
           SET downloads_remaining = downloads_remaining - 1,
               updated_at = datetime('now')
           WHERE id = ?""",
        (purchase_id,)
    )
    conn.commit()


def log_download(purchase_id, ip_address, user_agent):
    """Record a download event."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO download_logs (purchase_id, ip_address, user_agent) VALUES (?, ?, ?)",
        (purchase_id, ip_address, user_agent)
    )
    conn.commit()


def log_email(purchase_id, email_type, resend_id=None):
    """Record a sent email."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO email_log (purchase_id, email_type, resend_id) VALUES (?, ?, ?)",
        (purchase_id, email_type, resend_id)
    )
    conn.commit()


# --- Subscriber Queries ---

def create_subscriber(email, source="salmon-journey-ch1"):
    """Insert a new subscriber (idempotent — ignores duplicates)."""
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO subscribers (email, source) VALUES (?, ?)",
        (email, source)
    )
    conn.commit()


def log_playbook_view(slug, ip_address=None, user_agent=None):
    """Record a playbook open event."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO playbook_views (slug, ip_address, user_agent) VALUES (?, ?, ?)",
        (slug, ip_address, user_agent)
    )
    conn.commit()


def log_playbook_exit(slug, scroll_percent, time_spent_secs, ip_address=None):
    """Record where a reader exited a playbook."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO playbook_exits (slug, scroll_percent, time_spent_secs, ip_address) VALUES (?, ?, ?, ?)",
        (slug, scroll_percent, time_spent_secs, ip_address)
    )
    conn.commit()


def get_playbook_analytics():
    """Get aggregated analytics for all playbooks."""
    conn = get_connection()
    views = conn.execute("""
        SELECT slug, COUNT(*) as total_views,
               COUNT(DISTINCT ip_address) as unique_visitors,
               MIN(viewed_at) as first_view,
               MAX(viewed_at) as last_view
        FROM playbook_views
        GROUP BY slug
        ORDER BY total_views DESC
    """).fetchall()

    exits = conn.execute("""
        SELECT slug,
               AVG(scroll_percent) as avg_scroll,
               AVG(time_spent_secs) as avg_time,
               COUNT(*) as exit_count,
               SUM(CASE WHEN scroll_percent >= 90 THEN 1 ELSE 0 END) as completions
        FROM playbook_exits
        GROUP BY slug
    """).fetchall()

    return {
        "views": [dict(r) for r in views],
        "exits": {r["slug"]: dict(r) for r in exits}
    }


def get_subscriber_by_email(email):
    """Look up a subscriber by email."""
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM subscribers WHERE email = ?",
        (email,)
    ).fetchone()
