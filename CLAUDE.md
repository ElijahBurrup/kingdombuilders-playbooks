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
- **Production URL**: https://kingdombuilders.ai/playbooks (Cloudflare Worker → Render) — ALWAYS use this URL, never the onrender.com URL
- **Render internal URL**: https://kb-playbooks.onrender.com (URL_PREFIX=/playbooks) — internal only, never share
- **GitHub**: https://github.com/ElijahBurrup/kingdombuilders-playbooks (master branch, auto-deploys to Render)
- **GitHub Account**: ElijahBurrup (elijah@kingdombuilders.ai) — same login for GitHub, Cloudflare, and Render
- **Render Service ID**: srv-d6iir8ngi27c738ip9i0
- **Local dev**: `uvicorn api.main:app --reload --port 5000` → http://localhost:5000
- **Procfile**: `gunicorn api.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker`

## Database
- **Local**: `playbooks_development` (PostgreSQL, postgres:postgres123@localhost:5432)
- **Migrations**: `python -m alembic upgrade head`
- **Seeding**: `python -m scripts.seed_playbooks` (14 categories, 5 series, 51 playbooks, admin user)
- **SQLite migration**: `python -m scripts.migrate_sqlite_to_pg` (one-time migration from old data)

## Pre-Commit Checklist
1. Update this CLAUDE.md if architecture, key files, or deployment details changed
2. Run locally: `uvicorn api.main:app --reload --port 5000`
3. Run Playwright tests: `BASE_URL=http://localhost:5000 npx playwright test`

## Architecture Notes
- Each playbook has a landing page (static/*.html) and a full reader page (assets/*.html)
- Legacy routes are data-driven via `LANDING_ROUTES` and `SLUG_TO_FILE` dicts in `api/routers/legacy.py`
- New playbooks added via admin API or seed script (no more manual route registration)
- "SetHut" command generates new playbooks as visual experiences (see full checklist below)
- **NO HYPHENS/DASHES in playbook text**: Never use em dashes (—), en dashes (–), or hyphens (-) as punctuation in prose. Use commas, periods, or restructure sentences instead. This applies to ALL visible text content in assets/*.html files. CSS properties and HTML attributes with hyphens are fine.

## SetHut Checklist (New Playbook Creation)
Every new playbook requires ALL of these steps. Do not skip any.

### Step 1: Create Content (`assets/`)
- [ ] Generate `assets/The_Title.html` (full reader, 1000+ lines, all mandatory elements)
- [ ] Verify NO hyphens/dashes in prose text (run: `grep -P '[—–]' assets/The_Title.html`)
- [ ] If series: add series progress dots to finale (3 dots with active state, series label, "Part X of Y")
- [ ] If series: cross-reference other playbooks in the series (e.g., "Next: The Scorpion's Molt")
- [ ] Include: cover with animated particles, 4 chapter headers, scenes, viz boxes, think boxes, grand quotes, before/after pairs, breathe gates, final test (10 click-to-reveal questions), footer with scripture
- [ ] Include all standard JS: progress bar, chapter pill, scroll reveal (IntersectionObserver), final test click handlers
- [ ] Unique color palette per playbook (CSS custom properties)

### Step 2: Create Landing Page (`static/`)
- [ ] Generate `static/the-slug.html` (sales page with cover, chapter previews, pricing CTA)
- [ ] Match the playbook's unique color palette from Step 1
- [ ] Include: cover badge (series name + part number), 4 chapter cards, insight quote, concept box, selling points grid
- [ ] Include $2.50 single / $10/mo archive pricing + "READ THE PLAYBOOK" button linking to `read/the-slug`
- [ ] Footer with same scripture as the reader page

### Step 3: Register Routes (`api/routers/legacy.py`)
- [ ] Add to `LANDING_ROUTES` dict: `"/theslug": "the-slug.html"` (no hyphens in URL path)
- [ ] Add to `SLUG_TO_FILE` dict: `"the-slug": "The_Title.html"`
- [ ] Verify: URL path in LANDING_ROUTES has NO hyphens (e.g., `/thehermitcrabsshell` not `/the-hermit-crabs-shell`)

### Step 4: Add to Catalog Page (`static/index.html`)
**CRITICAL: The catalog page is hardcoded HTML, NOT dynamic from the database. Playbooks will NOT appear on the homepage unless manually added here.**
- [ ] Add `<a>` card to `static/index.html` inside `#playbook-grid` div
- [ ] Card requires: `href="read/the-slug"`, `class="card"`, `data-pillar`, `data-sub` attributes
- [ ] If part of a series: add `data-series="series-key"` attribute matching the series button
- [ ] Card HTML: `.card-cover` (title + subtitle), `.card-body` (tag + description + footer with price)
- [ ] If new series: add `<button class="series-btn" data-series="key">` to `.series-bar` div with icon and count
- [ ] Place card near related playbooks (same series or category)

### Step 5: Register in Database (`scripts/seed_playbooks.py`)
- [ ] Add entry to `PLAYBOOKS_DATA` list: slug, title, route, category, landing_file, asset_file, cover_emoji
- [ ] If part of a series: include `series` (slug) and `series_order` (1-based) fields
- [ ] If new series: add to `SERIES_DEFS` list with name, slug, description, display_order

### Step 6: Seed Discovery Engine (`scripts/seed_discovery.py`)
This powers three features: constellation map (`/constellation`), end-of-playbook chain panel (3 suggestion cards), and tag cloud filter.
- [ ] Add to `TAGS` dict: 8-10 tags with weights (0.3 to 1.0), keyed by playbook slug
- [ ] Add to `CONNECTIONS` dict: 3 connections per playbook, keyed by playbook slug:
  - 1 `deeper` (same domain, goes further into the topic)
  - 1 `bridge` (cross-domain, connects to different category)
  - 1 `surprise` (unexpected thematic link)
  - Each connection: `(type, target_slug, teaser_text, editorial_reason)`
  - Teaser is shown to the reader; reason is internal documentation only

### Step 7: Generate Pull Quotes (`scripts/generate_pull_quotes.py`)
**Must run locally (requires Playwright browser). Generated images must be committed and pushed with the code.**
- [ ] Add 3 curated quotes to `CURATED_QUOTES` dict, keyed by asset filename without extension (e.g., `"The_Hermit_Crabs_Shell"`)
- [ ] Quote selection: 1 hook (grabs attention), 1 reveal (core insight), 1 finale (closing punch)
- [ ] Run: `python -m scripts.generate_pull_quotes The_Title.html` (uses Playwright to screenshot the actual cover design)
- [ ] Verify 6 images generated in `assets/pull-quotes/` (3 quotes x 2 sizes: 1080x1080 square + 1200x675 wide)
- [ ] File naming: `"Title Words 1.png"`, `"Title Words 1 wide.png"`, `"Title Words 2.png"`, etc.
- [ ] `git add assets/pull-quotes/` to include generated images in the commit

### Step 8: Reading Paths (`scripts/seed_paths.py`)
- [ ] If part of a series: create a reading path for the series (slug, title, description, theme_tag, emoji, color)
- [ ] Each step: `(playbook_slug, transition_text)` — first step has `None` for transition
- [ ] Transition text explains WHY this playbook comes next in the journey
- [ ] If playbook fits an existing theme path: add it to that path's steps list
- [ ] If standalone: consider creating a new 3-4 step thematic path that includes it

### Step 9: Commit & Push
- [ ] `git add` all changed files: assets/*.html, assets/pull-quotes/*.png, static/*.html, static/index.html, api/routers/legacy.py, all seed scripts, CLAUDE.md
- [ ] Commit with descriptive message
- [ ] `git push origin master`

### Step 10: Deploy & Seed Production
**Use Render API to deploy and seed. Do NOT wait for auto-deploy or ask user to do it manually.**

Trigger deploy:
```bash
curl -s -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.render.com/v1/services/srv-d6iir8ngi27c738ip9i0/deploys" \
  -d '{"clearCache":"do_not_clear"}'
```

Poll deploy status until `"status":"live"`:
```bash
curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/srv-d6iir8ngi27c738ip9i0/deploys/{deploy_id}"
```

Run seed scripts as one-off job (can run during deploy, uses current DB):
```bash
curl -s -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.render.com/v1/services/srv-d6iir8ngi27c738ip9i0/jobs" \
  -d '{"startCommand":"python -m scripts.seed_playbooks && python -m scripts.seed_discovery && python -m scripts.seed_paths"}'
```

Poll job status until `"status":"succeeded"`:
```bash
curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/srv-d6iir8ngi27c738ip9i0/jobs/{job_id}"
```

**Render API Key is stored in auto-memory** (`memory/MEMORY.md`). Service ID: `srv-d6iir8ngi27c738ip9i0`.

### Step 11: Verify Production
- [ ] `GET /theslug` — landing page loads (not 404)
- [ ] `GET /read/the-slug` — reader page loads (may show paywall, that's OK)
- [ ] `GET /api/v1/discovery/chain/the-slug` — returns 3 recommendations (deeper, bridge, surprise)
- [ ] `GET /` — catalog page shows new card, series filter works
- [ ] `GET /constellation` — new node appears in graph
- [ ] `GET /paths` — reading path includes new playbook (if applicable)

Use `WebFetch` or `curl` against `https://kingdombuilders.ai/playbooks` to verify each endpoint.

## Thread System (Discovery Engine)
The discovery engine connects playbooks through invisible thematic "threads" to enable cross-pollination (e.g., AI reader discovers faith content).

### Database Tables
- **`playbook_tags`** — Multi-dimensional tags per playbook with weights (0.0 to 1.0). E.g., Ant Network: trust(1.0), decentralization(1.0), money(0.6), faith(0.3)
- **`playbook_connections`** — Curated relationships with 3 types: `deeper` (same domain), `bridge` (cross-domain), `surprise` (unexpected thematic link). Each has a `teaser` (shown to user) and `reason` (editorial note).
- **`journey_stamps`** — Achievement badges earned by users. Fields: user_id, stamp_type, stamp_data (JSONB), earned_at.

### API Endpoints
- `GET /api/v1/discovery/chain/{slug}` — Returns 3 recommendations (1 deeper, 1 bridge, 1 surprise). Falls back to tag-based matching if curated connections are missing.
- `POST /api/v1/discovery/chain-click` — Tracks recommendation clicks for analytics.
- `GET /api/v1/discovery/tags` — Top tags with counts and connected slugs (powers thread filter).
- `GET /api/v1/discovery/surprise` — Random playbook from unexplored category.
- `GET /api/v1/discovery/journey` — Reading passport: completed/in-progress playbooks, stamps, stats (requires auth).
- `POST /api/v1/discovery/journey/complete` — Mark playbook complete + check for new achievement stamps (requires auth).

### End-of-Playbook Chain Panel
Injected into every playbook reader page (via `_inject_back_button_and_tracking()` in `legacy.py`). Client-side JS fetches chain data and renders 3 visually distinct cards between the Finale and Footer. Also injects scroll-based completion tracking that fires POST to `/journey/complete` at 90% scroll for logged-in users.

### Journey Dashboard (`/journey`)
Reading passport page showing: completed/in-progress playbooks, category breakdown, progress bar, and 8 achievement stamps (earned vs locked). Fetches data client-side from `/api/v1/discovery/journey`. Redirects to `/auth` if not logged in.

### Achievement Stamps (8 types)
- `first_steps` — Complete first playbook
- `series_scholar` — Complete all playbooks in a series
- `category_explorer` — Read from 3+ categories
- `cross_pollinator` — Read from 5+ categories
- `deep_diver` — 5+ playbooks in one category
- `all_free` — Read all free playbooks
- `ten_complete` — Complete 10 playbooks
- `twenty_five` — Complete 25 playbooks

### Seed Script
`python -m scripts.seed_discovery` — Populates tags and connections for all playbooks. Idempotent (safe to re-run).

### Constellation View (`/constellation`)
Interactive force-directed graph of all playbooks as nodes and connections as edges. Canvas-based with vanilla JS physics simulation. Supports pan, zoom, touch, and category filtering via legend. Click any node to navigate to its playbook. API: `GET /api/v1/discovery/constellation` returns all nodes + edges.

### Reading Paths (`/paths`)
Pre-curated multi-playbook journeys that cross categories, each connected by a theme. Timeline UI with transition text between steps explaining why each playbook comes next. API: `GET /api/v1/discovery/paths` (list) and `GET /api/v1/discovery/paths/{slug}` (detail).

**Adding new paths**: Edit `scripts/seed_paths.py` — add a dict to the `PATHS` list with slug, title, description, theme_tag, emoji, color, and steps (list of playbook slug + transition text tuples). Run `python -m scripts.seed_paths` to upsert. Idempotent.

### Database Tables (Phase 4)
- **`reading_paths`** — slug, title, description, theme_tag, emoji, color, display_order
- **`reading_path_steps`** — path_id, playbook_id, step_order, transition_text

### Key Files
- `api/models/discovery.py` — PlaybookTag, PlaybookConnection, JourneyStamp, ReadingPath, ReadingPathStep
- `api/routers/discovery.py` — All discovery API endpoints (chain, tags, surprise, journey, constellation, paths)
- `api/schemas/discovery.py` — Pydantic response schemas (Phase 1-4)
- `api/services/journey_service.py` — Achievement checking logic (check_and_award_stamps)
- `templates/journey.html` — Reading passport UI
- `templates/constellation.html` — Force-directed graph visualization
- `templates/paths.html` — Reading paths UI with timeline view
- `scripts/seed_discovery.py` — Curated tag/connection data for all 48 playbooks
- `scripts/seed_paths.py` — Reading path definitions (6 paths, easy to add more)

## Branches
- `master` — production (current Flask app, auto-deploys to Render)
- `fastapi-rebuild` — Phase 1 FastAPI backend (DO NOT merge to master until Phase 3)
