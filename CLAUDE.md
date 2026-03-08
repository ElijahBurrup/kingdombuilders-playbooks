# Kingdom Builders AI — Playbooks

## Project Overview
Interactive animal-parable sales playbooks for Kingdom Builders AI. Each playbook is a self-contained visual experience teaching business/leadership principles through animal metaphors.

## Tech Stack
- **Framework**: FastAPI (Python) — migrated from Flask in Phase 1 rebuild
- **Database**: PostgreSQL (async via SQLAlchemy + asyncpg)
- **ORM**: SQLAlchemy 2.0 with async sessions
- **Migrations**: Alembic
- **Auth**: JWT (PyJWT) with refresh token rotation, bcrypt password hashing
- **Payments**: Stripe Checkout (individual + subscription)
- **Email**: Resend API
- **Scheduler**: APScheduler (background follow-up emails)
- **Hosting**: Render (auto-deploy from master branch via gunicorn + uvicorn)
- **Tests**: Playwright (Node.js)

## Directory Structure
```
Playbooks/
  api/                          # FastAPI application
    main.py                     # App factory, lifespan, router mounts
    config.py                   # Pydantic Settings (env-driven)
    database.py                 # Async SQLAlchemy engine + sessions
    dependencies.py             # get_db, get_current_user, get_admin_user
    models/                     # 19 SQLAlchemy ORM tables
    schemas/                    # Pydantic request/response models
    routers/                    # FastAPI route modules
      auth.py                   # 10 endpoints (register, login, OAuth, etc.)
      catalog.py                # 6 endpoints (playbooks, categories, series)
      legacy.py                 # Backward-compatible Flask routes
      payments.py               # Stripe checkout + subscription + webhook
      subscribe.py              # Email subscription (JSON API)
      admin.py                  # Admin CRUD (playbooks, users, promo codes)
    services/                   # Business logic
    utils/security.py           # JWT, bcrypt, token generation
    migrations/                 # Alembic migrations
  scripts/
    seed_playbooks.py           # Seed 14 categories, 2 series, 35 playbooks
    migrate_sqlite_to_pg.py     # SQLite → PostgreSQL data migration
  app.py                        # Legacy Flask app (kept for reference)
  static/                       # Landing pages + catalog
  assets/                       # Full playbook content HTML
  tests/                        # Playwright test suite
```

## Key Files
- `api/main.py` — FastAPI app factory with all router mounts, CORS, static files
- `api/routers/legacy.py` — Backward-compatible routes (all 35 landing pages, reader, checkout, etc.)
- `api/config.py` — All env vars via Pydantic Settings
- `api/database.py` — Async SQLAlchemy engine + Base class
- `api/models/` — 19 ORM tables (User, Playbook, Category, Series, Purchase, Subscription, etc.)
- `static/index.html` — Product catalog (main landing page)
- `static/*.html` — Individual playbook landing pages
- `assets/*.html` — Full playbook content (served via /read/<slug>)
- `tests/playbooks.spec.js` — Playwright test suite (173/173 passing)
- `alembic.ini` + `api/migrations/` — Database migrations

## API Endpoints
- **Legacy routes** (no prefix): `/`, `/thesalmonjourney`, `/read/{slug}`, `/subscribe`, `/create-checkout-session`, etc.
- **Auth API**: `/api/v1/auth/` — register, login, refresh, logout, google, verify-email, forgot-password, reset-password, me
- **Catalog API**: `/api/v1/playbooks`, `/api/v1/categories`, `/api/v1/series`
- **Payments API**: `/api/v1/stripe/checkout`, `/api/v1/stripe/subscription`, `/api/v1/stripe/portal`
- **Admin API**: `/api/v1/admin/dashboard`, `/api/v1/admin/playbooks`, `/api/v1/admin/users`, etc.
- **API Docs**: `/api/docs` (Swagger UI), `/api/redoc`

## Deployment
- **Live URL**: https://kingdombuilders-playbooks.onrender.com
- **GitHub**: https://github.com/ElijahBurrup/kingdombuilders-playbooks (master branch)
- **GitHub Account**: ElijahBurrup (elijah@kingdombuilders.ai)
- **Render Service ID**: srv-d6iir8ngi27c738ip9i0
- **Local dev**: `uvicorn api.main:app --reload --port 5000` → http://localhost:5000
- **Procfile**: `gunicorn api.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker`

## Database
- **Local**: `playbooks_development` (PostgreSQL, postgres:postgres123@localhost:5432)
- **Migrations**: `python -m alembic upgrade head`
- **Seeding**: `python -m scripts.seed_playbooks` (14 categories, 2 series, 35 playbooks, admin user)
- **SQLite migration**: `python -m scripts.migrate_sqlite_to_pg` (one-time migration from old data)

## Pre-Commit Checklist
1. Update this CLAUDE.md if architecture, key files, or deployment details changed
2. Run locally: `uvicorn api.main:app --reload --port 5000`
3. Run Playwright tests: `BASE_URL=http://localhost:5000 npx playwright test`

## Architecture Notes
- Each playbook has a landing page (static/*.html) and a full reader page (assets/*.html)
- Legacy routes are data-driven via `LANDING_ROUTES` and `SLUG_TO_FILE` dicts in `api/routers/legacy.py`
- New playbooks added via admin API or seed script (no more manual route registration)
- "SetHut" command generates new playbooks as visual experiences
- **NO HYPHENS/DASHES in playbook text**: Never use em dashes (—), en dashes (–), or hyphens (-) as punctuation in prose. Use commas, periods, or restructure sentences instead. This applies to ALL visible text content in assets/*.html files. CSS properties and HTML attributes with hyphens are fine.
- URL_PREFIX middleware supports subpath deployment (e.g., /playbooks on Cloudflare Worker)

## Branches
- `master` — production (current Flask app, auto-deploys to Render)
- `fastapi-rebuild` — Phase 1 FastAPI backend (DO NOT merge to master until Phase 3)
