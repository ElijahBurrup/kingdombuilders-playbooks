# Kingdom Builders AI — Playbooks

## Project Overview
Interactive animal-parable sales playbooks for Kingdom Builders AI. Each playbook is a self-contained visual experience teaching business/leadership principles through animal metaphors.

## Tech Stack
- **Framework**: Flask (Python)
- **Database**: SQLite (data/playbook.db)
- **Payments**: Stripe Checkout
- **Email**: Resend API
- **Hosting**: Render (auto-deploy from master branch)
- **Tests**: Playwright (Node.js)

## Key Files
- `app.py` — Flask routes: catalog, playbook landing pages, reader, Stripe checkout, email subscribe
- `config.py` — Stripe, Resend, Flask config (env-driven)
- `database.py` — SQLite schema: subscribers, purchases, download tokens
- `stripe_checkout.py` — Stripe session creation and webhook handler
- `emails.py` — Lead magnet and purchase confirmation emails via Resend
- `downloads.py` — Token-based PDF download handler
- `scheduler.py` — APScheduler for background tasks
- `static/index.html` — Product catalog (main landing page)
- `static/*.html` — Individual playbook landing pages
- `assets/*.html` — Full playbook content (served via /read/<slug>)
- `tests/playbooks.spec.js` — Playwright test suite

## Deployment
- **Live URL**: https://kingdombuilders-playbooks.onrender.com
- **GitHub**: https://github.com/ElijahBurrup/kingdombuilders-playbooks (master branch)
- **GitHub Account**: ElijahBurrup (elijah@kingdombuilders.ai)
- **Render Service ID**: srv-d6h46uma2pns738affa0
- **Local dev**: `python app.py` → http://localhost:5000

## Pre-Commit Checklist
1. Update this CLAUDE.md if architecture, key files, or deployment details changed
2. Restart localhost: kill any running Flask process, then `cd "C:/Projects/KingdomBuilders.AI/Playbooks" && python app.py` (runs on port 5000)
3. Run Playwright tests: `npx playwright test`

## Architecture Notes
- Each playbook has a landing page (static/*.html) and a full reader page (assets/*.html)
- Playbook routes are manually registered in app.py — add a new route + slug mapping when creating a new playbook
- "SetHut" command generates new playbooks as visual experiences (not reading experiences)
- **After every local deploy/commit**: restart Flask dev server (`python app.py`) on localhost:5000 to verify changes locally
