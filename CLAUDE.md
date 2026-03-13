# Kingdom Builders AI — Playbooks

## Project Overview
Interactive animal-parable sales playbooks for Kingdom Builders AI. Each playbook is a self-contained visual experience teaching business/leadership principles through animal metaphors.

## Tech Stack
- **Framework**: FastAPI (Python) — migrated from Flask in Phase 1 rebuild
- **Database**: PostgreSQL (async via SQLAlchemy + asyncpg)
- **ORM**: SQLAlchemy 2.0 with async sessions
- **Migrations**: Alembic
- **Auth**: JWT (PyJWT) with refresh token rotation, bcrypt password hashing
- **Payments**: Stripe Checkout (individual $2.50 + subscription $10/mo) — LIVE mode configured on Render
- **Email**: Resend API (key configured on Render, from: elijah@kingdombuilders.ai)
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
    models/                     # SQLAlchemy ORM tables
      activity.py               # ReadingProgress (last_chapter, downloaded, completed)
      feedback.py               # TopicSuggestion, PlaybookFeedback
    schemas/                    # Pydantic request/response models
    routers/                    # FastAPI route modules
      auth.py                   # 10 endpoints (register, login, OAuth, etc.)
      catalog.py                # 6 endpoints (playbooks, categories, series)
      legacy.py                 # Reader, landing pages, checkout, admin, tracking
      feedback.py               # Suggestions, ratings, progress, downloads
      payments.py               # Stripe checkout + subscription + webhook
      subscribe.py              # Email subscription (JSON API)
      admin.py                  # Admin CRUD (playbooks, users, promo codes)
    services/                   # Business logic
    utils/security.py           # JWT, bcrypt, token generation
    migrations/                 # Alembic migrations
  scripts/
    seed_playbooks.py           # Seed 14 categories, 5 series, 51+ playbooks
    seed_discovery.py           # Tags + connections for all playbooks
    seed_paths.py               # Reading path definitions
    generate_pull_quotes.py     # Playwright-based pull quote image generator
    generate_pdfs.py            # Playwright-based PDF generator (standard + book-cut)
    pdf_quality_test.py         # Validates PDF whitespace waste and page breaks
    update_landing_pages.py     # Batch updater for landing page HTML
    migrate_sqlite_to_pg.py     # SQLite → PostgreSQL data migration (one-time)
  app.py                        # Legacy Flask app (kept for reference)
  static/                       # Landing pages + catalog
  assets/                       # Full playbook content HTML
    pdf/                        # Generated standard PDFs (8.5x11)
    pdf-bookcut/                # Generated book-cut PDFs (two 5.5x8.5 per sheet)
    pull-quotes/                # Generated pull quote images
  tests/
    playbooks.spec.js           # Playwright E2E test suite
    readability-check.js        # Color contrast + formatting validator
```

## Key Files
- `api/main.py` — FastAPI app factory with all router mounts, CORS, static files
- `api/routers/legacy.py` — Reader routes, landing pages, purchase gate, checkout, tracking, admin, PDF download
- `api/routers/feedback.py` — Topic suggestions, playbook ratings, user progress, download tracking
- `api/config.py` — All env vars via Pydantic Settings
- `api/database.py` — Async SQLAlchemy engine + Base class
- `api/models/activity.py` — ReadingProgress (scroll_percent, last_chapter, downloaded, completed)
- `api/models/feedback.py` — TopicSuggestion, PlaybookFeedback
- `static/index.html` — Product catalog (grid + table view with progress tracking, PDF download)
- `static/*.html` — Individual playbook landing pages (sales pages with floating CTA)
- `assets/*.html` — Full playbook content (served via /read/<slug>)
- `tests/playbooks.spec.js` — Playwright E2E test suite
- `tests/readability-check.js` — Pre-deploy color contrast and formatting validator
- `scripts/generate_pdfs.py` — Playwright PDF generator (standard + book-cut formats)
- `scripts/pdf_quality_test.py` — PDF whitespace waste validator
- `alembic.ini` + `api/migrations/` — Database migrations

## API Endpoints
- **Legacy routes** (no prefix): `/`, `/thesalmonjourney`, `/read/{slug}`, `/read/{slug}/pdf`, `/subscribe`, `/create-checkout-session`, etc.
- **Auth API**: `/api/v1/auth/` — register, login, refresh, logout, google, verify-email, forgot-password, reset-password, me
- **Catalog API**: `/api/v1/playbooks`, `/api/v1/categories`, `/api/v1/series`
- **Payments API**: `/api/v1/stripe/checkout`, `/api/v1/stripe/subscription`, `/api/v1/stripe/portal`
- **Feedback API**: `/api/v1/suggestions`, `/api/v1/feedback`, `/api/v1/feedback-summary`, `/api/v1/user/progress`, `/api/v1/track-download`
- **Admin API**: `/api/v1/admin/dashboard`, `/api/v1/admin/playbooks`, `/api/v1/admin/users`, `/api/v1/admin/suggestions`, `/api/v1/admin/feedback-list`
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
- **Seeding**: `python -m scripts.seed_playbooks` (14 categories, 6 series, 58+ playbooks, admin user)
- **Series**: AI Economy (3), Lay It Down (8), Dad Talks (7), A Process Model (6), plus standalone playbooks
- **SQLite migration**: `python -m scripts.migrate_sqlite_to_pg` (one-time migration from old data)

## Pre-Commit Checklist
1. Update this CLAUDE.md if architecture, key files, or deployment details changed
2. Run readability test: `node tests/readability-check.js` (checks ALL assets/*.html)
3. Run locally: `uvicorn api.main:app --reload --port 5000`
4. Run Playwright tests: `BASE_URL=http://localhost:5000 npx playwright test`

## Architecture Notes
- Each playbook has a landing page (static/*.html) and a full reader page (assets/*.html)
- Legacy routes are data-driven via `LANDING_ROUTES` and `SLUG_TO_FILE` dicts in `api/routers/legacy.py`
- New playbooks added via admin API or seed script (no more manual route registration)
- "SetHut" command generates new playbooks as visual experiences (see full checklist below)
- **NO HYPHENS/DASHES in playbook text**: Never use em dashes (—), en dashes (–), or hyphens (-) as punctuation in prose. Use commas, periods, or restructure sentences instead. This applies to ALL visible text content in assets/*.html files. CSS properties and HTML attributes with hyphens are fine.

## Reading Progress & Downloads
- **ReadingProgress** model tracks: `scroll_percent`, `last_chapter` (h2 heading text), `downloaded` (bool), `completed` (bool)
- Chapter detection: JS tracks which `<h2>` heading the user has scrolled past, sends via `navigator.sendBeacon()` on exit
- Completion: auto-set at 90%+ scroll depth
- Progress API: `GET /api/v1/user/progress` returns status for all playbooks (not-started, opened, chapter name, downloaded, completed)
- Table view in catalog shows chapter-level progress instead of generic "In Progress"

## PDF Generation System
- **Standard PDF** (8.5x11 portrait): `assets/pdf/{stem}.pdf` — preserves all visual formatting, smart page breaks
- **Book-cut PDF** (landscape letter, two 5.5x8.5 pages per sheet): `assets/pdf-bookcut/{stem}_bookcut.pdf` — includes instruction cover page with cut/stack/bind diagram and materials list
- Generated via Playwright `page.pdf()` with print CSS for `break-inside: avoid`, background preservation, animation removal
- Book-cut uses `pypdf` for page imposition (two half-letter pages per landscape sheet)
- Download route: `GET /read/{slug}/pdf?format=standard|bookcut` (respects purchase gate)
- Scripts: `python -m scripts.generate_pdfs [file.html] [--force]`, `python -m scripts.pdf_quality_test [file.html]`
- PDFs are committed to git (like pull quotes), not generated at runtime

## Landing Page Design (static/*.html)
- **Cover**: Shrunk to 60vh (not full-screen) so sales copy is visible sooner
- **No hero CTA button** on cover — removed to reduce clutter
- **Floating "Get the Playbook" button**: Fixed bottom-right gold pill (`class="fab-cta"`), always visible, links to `read/{slug}` (purchase gate)
- **Bottom CTA section**: Dual pricing ($2.50 single / $10/mo archive) without a separate "READ THE PLAYBOOK" button (the floating CTA handles this)
- **Purchase gate**: When non-free, non-purchased playbook accessed via `/read/{slug}`, serves the landing page (`static/{slug}.html`) if it exists, otherwise falls back to generic `purchase_gate.html`
- **Batch updates**: Use `scripts/update_landing_pages.py` to apply structural changes across all 61 landing pages

## Feedback & Suggestions System
- **Topic suggestions**: Users can suggest new playbook topics via `POST /api/v1/suggestions` (rate-limited)
- **Playbook ratings**: 1-5 star ratings + comments via `POST /api/v1/feedback`, triggered after 80%+ scroll
- **Admin management**: `/admin/manage` page with two tabs (suggestions + feedback), status updates via PATCH
- Models: `TopicSuggestion` (status: pending/created/saved/deleted), `PlaybookFeedback` (rating, comment, scroll_percent)

## Installation Videos (Cloudflare R2)
Playbook "installation videos" are short AI-generated clips embedded in `assets/*.html` reader pages. They reinforce key concepts visually.

### R2 Storage
- **Bucket**: `kb-playbook-videos` on Cloudflare account `81f3bf31ee69fe657517c485ad8f62b3`
- **Public URL prefix**: `https://pub-3be2b691e42247078311064d9672c978.r2.dev/`
- **Upload API**: `PUT https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/kb-playbook-videos/objects/{filename}`
- **Auth**: Bearer token via `CLOUDFLARE_R2_TOKEN` env var
- Videos are **never stored in git** — always served from R2 (zero egress fees, CDN-backed)

### Video Generation (Runway Gen-4.5)
- **Script**: `scripts/generate_videos.py` — generates videos via Runway API and auto-uploads to R2
- **SDK**: `runwayml` Python package
- **Key params**: `model='gen4.5'`, `prompt_text=` (NOT `prompt=`), `ratio='1280:720'` (NOT `16:9`), `duration=5`
- **API key**: env var `RUNWAYML_API_SECRET`
- **Cost**: Credits-based; check balance before bulk generation

### Embed Pattern in assets/*.html
```html
<div class="install-video">
<video src="https://pub-3be2b691e42247078311064d9672c978.r2.dev/{video-id}.mp4" autoplay muted loop playsinline></video>
<div class="iv-caption">
 <span class="iv-badge">Installation</span>
 <span class="iv-text">Caption describing what the viewer is seeing.</span>
</div>
</div>
```
Each playbook needs matching `.install-video` CSS using that playbook's color palette (border-color, badge background, caption gradient).

## Google Sign-In (GSI)
- Uses **client-side Google Identity Services** (ID token flow), NOT server-side OAuth redirect
- Frontend posts ID token → backend verifies via `https://oauth2.googleapis.com/tokeninfo`
- Only `GOOGLE_CLIENT_ID` env var is needed (no client secret required for this flow)
- Auth endpoints: `POST /auth/google` (legacy) and `POST /api/v1/auth/google` (API)
- Google Cloud Console must have: Authorized JS origins = `https://kingdombuilders.ai`, Authorized redirect URI = `https://kingdombuilders.ai/playbooks/auth/google`

## Catalog UI (static/index.html)
- **Grid view**: Card-based layout with cover gradients, descriptions, and pricing
- **Table view**: Sortable/filterable table with cover swatch, title (series label underneath), category, rating stars, reading status, PDF download button
- **Reading status**: Fetched from `GET /api/v1/user/progress`, shows chapter name (e.g., "The Lever Rats") instead of generic "In Progress"
- **PDF download**: Button in table calls `POST /api/v1/track-download` then opens `/read/{slug}/pdf`
- **Series display**: Title shown without series prefix, "(Series Name X of N)" shown underneath
- Filter panel auto-closes on selection via `closePanel()` JS function (critical for mobile UX)
- `closePanel()` is called after every filter click: category pills, sub-pills, series buttons, thread buttons
- Filter element sizes are intentionally large for touch targets (pills 0.92rem/12px 28px, series 0.88rem/12px 24px)

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
- [ ] **Run readability test**: `node tests/readability-check.js assets/The_Title.html` — fix ALL failures before proceeding

#### Formatting Rules (Mandatory)
1. **Consistent margins**: ALL visual blocks (`.memory`, `.scene`, `.viz`, `.wisdom`, `.reflect`, `.dad-voice`, `.root-ck`, `.compare-table`, `.prompt`, `.final-test`) must use `margin: 40px 0`. No exceptions.
2. **No deep nesting**: Maximum ONE level of card-in-card, and ONLY for small, contained content (under ~5 lines). For longer content, use a simple divider (border-top) instead of a nested card. Example: `.memory-lesson` uses `border-top` separator, NOT a bordered/backgrounded card inside `.memory-inner`.
3. **Ribbon/scripture readability**: Ribbon backgrounds must have enough opacity to be clearly distinguishable (minimum `rgba(..., 0.08)`). Ribbon text must use `var(--text-light)` (#3A3A3A) or darker, NEVER `var(--text-muted)` (#6A6A6A) which is too faint.
4. **No stacking 3+ heavy blocks**: Avoid placing more than 2 heavy visual blocks (`.memory`, `.viz`, `.scene`) back-to-back without a prose section or breathing room between them. Ribbons and root-checks are lightweight and do not count.
5. **Color contrast**: ALL text must have a contrast ratio of at least 4.5:1 against its background. Dark text on dark backgrounds is a show-stopping bug. Light text on light backgrounds is a show-stopping bug. When in doubt, run the readability test.

### Step 2: Create Landing Page (`static/`)
- [ ] Generate `static/the-slug.html` (sales page with cover, chapter previews, pricing CTA)
- [ ] Match the playbook's unique color palette from Step 1
- [ ] Cover: `min-height:60vh` (NOT 100vh), cover badge, title, tagline, author — NO hero CTA button, NO cover-price span
- [ ] Include: 4 chapter cards, insight quote, concept box, selling points grid
- [ ] Bottom CTA section: dual pricing ($2.50 single / $10/mo archive) — NO "READ THE PLAYBOOK" button
- [ ] Floating CTA: `<a href="read/the-slug" class="fab-cta">` with eye SVG icon, fixed bottom-right, gold pill (see `.fab-cta` CSS in existing landing pages)
- [ ] Footer with same scripture as the reader page
- [ ] Or run `python scripts/update_landing_pages.py` after creation to auto-apply the standard structure

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

### Step 8: Generate PDFs (`scripts/generate_pdfs.py`)
**Must run locally (requires Playwright browser). Generated PDFs must be committed and pushed with the code.**
- [ ] Run: `python -m scripts.generate_pdfs The_Title.html`
- [ ] Verify standard PDF in `assets/pdf/The_Title.pdf` (8.5x11 portrait, backgrounds preserved)
- [ ] Verify book-cut PDF in `assets/pdf-bookcut/The_Title_bookcut.pdf` (landscape, two half-letter pages per sheet, instruction cover page)
- [ ] Run quality test: `python -m scripts.pdf_quality_test The_Title.html` (must pass <20% whitespace waste)
- [ ] `git add assets/pdf/ assets/pdf-bookcut/` to include generated PDFs in the commit

### Step 9: Reading Paths (`scripts/seed_paths.py`)
- [ ] If part of a series: create a reading path for the series (slug, title, description, theme_tag, emoji, color)
- [ ] Each step: `(playbook_slug, transition_text)` — first step has `None` for transition
- [ ] Transition text explains WHY this playbook comes next in the journey
- [ ] If playbook fits an existing theme path: add it to that path's steps list
- [ ] If standalone: consider creating a new 3-4 step thematic path that includes it

### Step 10: Commit & Push
- [ ] `git add` all changed files: assets/*.html, assets/pull-quotes/*.png, assets/pdf/*.pdf, assets/pdf-bookcut/*.pdf, static/*.html, static/index.html, api/routers/legacy.py, all seed scripts, CLAUDE.md
- [ ] Commit with descriptive message
- [ ] `git push origin master`

### Step 11: Deploy & Seed Production
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

**Render API Key**: `rnd_GE9eGvcpwlHI7VDn3Km0Fyj1TsRS`. Service ID: `srv-d6iir8ngi27c738ip9i0`.

### Step 12: Verify Production
- [ ] `GET /theslug` — landing page loads with floating CTA (not 404)
- [ ] `GET /read/the-slug` — reader page loads (may show paywall/landing page, that's OK)
- [ ] `GET /read/the-slug/pdf` — standard PDF downloads (may require auth)
- [ ] `GET /read/the-slug/pdf?format=bookcut` — book-cut PDF downloads (may require auth)
- [ ] `GET /api/v1/discovery/chain/the-slug` — returns 3 recommendations (deeper, bridge, surprise)
- [ ] `GET /` — catalog page shows new card, series filter works, table view has download button
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
- `master` — production (FastAPI app, auto-deploys to Render)

## Render Env Vars (Production)
All 16+ env vars set on Render service `srv-d6iir8ngi27c738ip9i0`:
- `DATABASE_URL`, `URL_PREFIX=/playbooks`, `SECRET_KEY`, `ADMIN_PASSWORD`
- `STRIPE_SECRET_KEY` (live), `STRIPE_PUBLISHABLE_KEY` (live), `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_SINGLE`, `STRIPE_PRICE_SUBSCRIPTION`
- `RESEND_API_KEY`, `GOOGLE_CLIENT_ID`
- `CLOUDFLARE_R2_TOKEN` (for video uploads)
- `RUNWAYML_API_SECRET` (for video generation)
- **CRITICAL**: `PUT /v1/services/{id}/env-vars` REPLACES ALL env vars — always include ALL existing vars when adding new ones
