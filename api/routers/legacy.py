"""
Legacy backward-compatibility router.

Reproduces every route from the original Flask app.py so existing
URLs (landing pages, reader, checkout, downloads, legal pages) continue
to work without any changes on the client side.
"""

import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlencode

import stripe
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates

from api.config import settings
from api.database import get_db
from api.models.user import User, OAuthAccount
from api.models.purchase import Purchase, Subscription, StripeCustomer
from api.utils.security import hash_password, verify_password
from api.utils.session import get_session_user_id, set_session_cookie, clear_session_cookie

# ---------------------------------------------------------------------------
# Directory paths — BASE_DIR is the Playbooks project root
# legacy.py lives at  api/routers/legacy.py
#   -> parent         api/routers/
#   -> parent.parent  api/
#   -> parent^3       Playbooks/
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["legacy"])

# ============================================================================
# Version & Release Notes
# ============================================================================
APP_VERSION = "2.6.0"
RELEASE_NOTES = [
    {
        "version": "2.6.0",
        "date": "2026-03-08",
        "title": "Lay It Down: 7 Deadly Sins Complete",
        "changes": [
            "New playbook: Lay It Down: Gluttony (Part 6 of 7)",
            "New playbook: Lay It Down: Lust (Part 7 of 7 — Series Finale)",
            "Complete 7 Deadly Sins series now live",
            "48 playbooks now live",
        ],
    },
    {
        "version": "2.5.0",
        "date": "2026-03-08",
        "title": "Lay It Down: Sloth & Greed",
        "changes": [
            "New playbook: Lay It Down: Sloth (Part 4 of 7)",
            "New playbook: Lay It Down: Greed (Part 5 of 7)",
            "46 playbooks now live",
        ],
    },
    {
        "version": "2.4.0",
        "date": "2026-03-07",
        "title": "Purchase Gate & Knowledge Layer",
        "changes": [
            "Purchase gate — paid playbooks now show pricing options before reading",
            "Three access tiers: single playbook ($2.50), monthly ($10/mo), yearly ($100/yr)",
            "Admin access codes for complimentary entry",
            "Knowledge Layer — hover any highlighted term to see its definition instantly",
            "The Bonsai Method: 22 domain terms with hover definitions",
        ],
    },
    {
        "version": "2.3.0",
        "date": "2026-03-06",
        "title": "Stripe Integration & Analytics",
        "changes": [
            "Full Stripe checkout for single, monthly, and yearly purchases",
            "Stripe webhook for automatic access provisioning",
            "Playbook analytics — tracks opens and scroll depth per playbook",
            "Admin dashboard at /admin with visual analytics",
        ],
    },
    {
        "version": "2.2.0",
        "date": "2026-03-06",
        "title": "Search & Bold Claims",
        "changes": [
            "Search bar — find playbooks instantly by title, description, or category",
            "Bold Claims added to all 44 playbooks",
            "Stage Setters added to all 44 playbooks",
        ],
    },
    {
        "version": "2.1.0",
        "date": "2026-03-05",
        "title": "Catalog Launch",
        "changes": [
            "5 free playbooks available without purchase",
            "Subscription pricing model introduced",
            "Email capture for free chapter previews",
        ],
    },
    {
        "version": "2.0.0",
        "date": "2026-03-04",
        "title": "The Grand Redesign",
        "changes": [
            "Completely redesigned catalog with category filtering",
            "5 free playbooks available without purchase",
            "Subscription pricing model introduced",
            "Email capture for free chapter previews",
        ],
    },
]

# ============================================================================
# Free slugs & admin access
# ============================================================================
FREE_SLUGS = {
    "lay-it-down",
    "the-narrator",
    "the-crows-gambit",
    "the-salmon-journey",
    "the-wolfs-table",
}

ADMIN_CODE = "elijahsentme"

# ============================================================================
# Landing-page routes — maps a URL path to a file inside static/
# ============================================================================
LANDING_ROUTES: dict[str, str] = {
    "/conductorsplaybook": "landing.html",
    "/layitdown": "lay-it-down.html",
    "/theantnetwork": "the-ant-network.html",
    "/thecostledger": "the-cost-ledger.html",
    "/theghostframe": "the-ghost-frame.html",
    "/thegravitywell": "the-gravity-well.html",
    "/thenarrator": "the-narrator.html",
    "/thesalmonjourney": "the-salmon-journey.html",
    "/thesquirreleconomy": "the-squirrel-economy.html",
    "/thewolfstable": "the-wolfs-table.html",
    "/thecrowsgambit": "the-crows-gambit.html",
    "/theeagleslens": "the-eagles-lens.html",
    "/thelighthousekeeperslog": "the-lighthouse-keepers-log.html",
    "/theoctopusprotocol": "the-octopus-protocol.html",
    "/thestarlingsmurmuration": "the-starlings-murmuration.html",
    "/thechameleonscode": "the-chameleons-code.html",
    "/thespidersloom": "the-spiders-loom.html",
    "/thegeckosgrip": "the-geckos-grip.html",
    "/thefireflyssignal": "the-fireflys-signal.html",
    "/thefoxstrail": "the-foxs-trail.html",
    "/themothsflame": "the-moths-flame.html",
    "/thebearswinter": "the-bears-winter.html",
    "/thecoyoteslaugh": "the-coyotes-laugh.html",
    "/thepangolinsarmor": "the-pangolins-armor.html",
    "/thehorsesgait": "the-horses-gait.html",
    "/thecompassrose": "the-compass-rose.html",
    "/layitdownpride": "lay-it-down-pride.html",
    "/layitdownenvy": "lay-it-down-envy.html",
    "/layitdownwrath": "lay-it-down-wrath.html",
    "/thetidepoolsecho": "the-tide-pools-echo.html",
    "/thewhalesbreath": "the-whales-breath.html",
    "/thebutterflyscrossing": "the-butterflys-crossing.html",
    "/theeleophantsground": "the-elephants-ground.html",
    "/thebeesdance": "the-bees-dance.html",
    "/theottersplay": "the-otters-play.html",
    "/themockingbirdssong": "the-mockingbirds-song.html",
    "/dadtalksthedopaminedrought": "dad-talks-the-dopamine-drought.html",
    "/dadtalksthemirrortest": "dad-talks-the-mirror-test.html",
    "/thearrival": "the-arrival.html",
    "/thebodylie": "the-body-lie.html",
    "/themyceliumnetwork": "the-mycelium-network.html",
    "/thetermitecathedral": "the-termite-cathedral.html",
    "/thebonsaimethod": "the-bonsai-method.html",
    "/thefibonaccitrim": "the-fibonacci-trim.html",
    "/layitdownsloth": "lay-it-down-sloth.html",
    "/layitdowngreed": "lay-it-down-greed.html",
    "/layitdowngluttony": "lay-it-down-gluttony.html",
    "/layitdownlust": "lay-it-down-lust.html",
}

# ============================================================================
# Reader route — maps a slug to an HTML file inside assets/
# ============================================================================
SLUG_TO_FILE: dict[str, str] = {
    "lay-it-down": "Lay_It_Down.html",
    "the-ant-network": "The_Ant_Network.html",
    "the-cost-ledger": "The_Cost_Ledger.html",
    "the-ghost-frame": "The_Ghost_Frame.html",
    "the-gravity-well": "The_Gravity_Well.html",
    "the-narrator": "The_Narrator.html",
    "the-salmon-journey": "The_Salmon_Journey.html",
    "the-squirrel-economy": "The_Squirrel_Economy_Modified.html",
    "conductors-playbook": "The_Conductors_Playbook.html",
    "the-wolfs-table": "The_Wolfs_Table.html",
    "the-crows-gambit": "The_Crows_Gambit.html",
    "the-eagles-lens": "The_Eagles_Lens.html",
    "the-lighthouse-keepers-log": "The_Lighthouse_Keepers_Log.html",
    "the-octopus-protocol": "The_Octopus_Protocol.html",
    "the-starlings-murmuration": "The_Starlings_Murmuration.html",
    "the-chameleons-code": "The_Chameleons_Code.html",
    "the-spiders-loom": "The_Spiders_Loom.html",
    "the-geckos-grip": "The_Geckos_Grip.html",
    "the-fireflys-signal": "The_Fireflys_Signal.html",
    "the-foxs-trail": "The_Foxs_Trail.html",
    "the-moths-flame": "The_Moths_Flame.html",
    "the-bears-winter": "The_Bears_Winter.html",
    "the-coyotes-laugh": "The_Coyotes_Laugh.html",
    "the-pangolins-armor": "The_Pangolins_Armor.html",
    "the-horses-gait": "The_Horses_Gait.html",
    "the-tide-pools-echo": "The_Tide_Pools_Echo.html",
    "the-whales-breath": "The_Whales_Breath.html",
    "the-butterflys-crossing": "The_Butterflys_Crossing.html",
    "the-elephants-ground": "The_Elephants_Ground.html",
    "the-bees-dance": "The_Bees_Dance.html",
    "the-otters-play": "The_Otters_Play.html",
    "the-compass-rose": "The_Compass_Rose.html",
    "lay-it-down-pride": "Lay_It_Down_Pride.html",
    "lay-it-down-envy": "Lay_It_Down_Envy.html",
    "lay-it-down-wrath": "Lay_It_Down_Wrath.html",
    "the-mockingbirds-song": "The_Mockingbirds_Song.html",
    "dad-talks-the-dopamine-drought": "Dad_Talks_The_Dopamine_Drought.html",
    "dad-talks-the-mirror-test": "Dad_Talks_The_Mirror_Test.html",
    "the-arrival": "The_Arrival.html",
    "the-body-lie": "The_Body_Lie.html",
    "the-mycelium-network": "The_Mycelium_Network.html",
    "the-termite-cathedral": "The_Termite_Cathedral.html",
    "the-bonsai-method": "The_Bonsai_Method.html",
    "the-fibonacci-trim": "The_Fibonacci_Trim.html",
    "lay-it-down-sloth": "Lay_It_Down_Sloth.html",
    "lay-it-down-greed": "Lay_It_Down_Greed.html",
    "lay-it-down-gluttony": "Lay_It_Down_Gluttony.html",
    "lay-it-down-lust": "Lay_It_Down_Lust.html",
}


# ============================================================================
# Catalog (index)
# ============================================================================
@router.get("/", include_in_schema=False)
async def catalog():
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/health", include_in_schema=False)
async def health():
    return HTMLResponse("ok", status_code=200)


# ============================================================================
# Landing pages — register each route via helper
# ============================================================================
def _make_landing_handler(filename: str):
    """Factory that returns an async handler serving a static landing page."""
    async def handler():
        file_path = STATIC_DIR / filename
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"Landing page not found: {filename}")
        return FileResponse(file_path)
    return handler


for _path, _filename in LANDING_ROUTES.items():
    router.add_api_route(
        _path,
        _make_landing_handler(_filename),
        methods=["GET"],
        include_in_schema=False,
    )


# ============================================================================
# Playbook reader — /read/{slug} (with purchase gate)
# ============================================================================
def _slug_to_title(slug: str) -> str:
    """Convert slug like 'the-eagles-lens' to 'The Eagle's Lens'."""
    return slug.replace("-", " ").title()


def _inject_back_button_and_tracking(html: str, slug: str) -> str:
    """Inject fixed back button and exit tracking script before </body>."""
    prefix = settings.URL_PREFIX or ""
    back_button = f"""
<style>
.pb-back{{position:fixed;top:16px;left:16px;z-index:9999;display:flex;align-items:center;gap:6px;
  padding:8px 16px 8px 12px;background:rgba(10,6,20,0.75);backdrop-filter:blur(8px);
  border:1px solid rgba(255,255,255,0.1);border-radius:50px;
  font-family:'Poppins',Helvetica,sans-serif;font-size:0.7rem;font-weight:600;color:rgba(255,255,255,0.7);
  text-decoration:none;cursor:pointer;transition:all 0.25s;box-shadow:0 2px 12px rgba(0,0,0,0.3)}}
.pb-back:hover{{background:rgba(10,6,20,0.9);color:#E8C96A;border-color:rgba(212,168,67,0.3)}}
.pb-back svg{{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}}
@media print{{.pb-back{{display:none}}}}
</style>
<a class="pb-back" href="{prefix}/"><svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>Playbooks</a>
"""
    tracking_script = f"""
<script>
(function(){{
  var slug = '{slug}';
  var prefix = '';
  try {{ var m = location.pathname.match(/^(\\/[^\\/]+)\\/read\\//); if(m) prefix = m[1]; }} catch(e){{}}
  var startTime = Date.now();
  var tracked = false;

  fetch(prefix + '/api/track/view', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{slug: slug}})
  }}).catch(function(){{}});

  function getScrollPercent() {{
    var h = document.documentElement;
    var b = document.body;
    var st = h.scrollTop || b.scrollTop;
    var sh = (h.scrollHeight || b.scrollHeight) - h.clientHeight;
    return sh > 0 ? Math.round((st / sh) * 100) : 0;
  }}

  function sendExit() {{
    if (tracked) return;
    tracked = true;
    var data = JSON.stringify({{
      slug: slug,
      scroll_percent: getScrollPercent(),
      time_spent_secs: Math.round((Date.now() - startTime) / 1000)
    }});
    if (navigator.sendBeacon) {{
      navigator.sendBeacon(prefix + '/api/track/exit', new Blob([data], {{type: 'application/json'}}));
    }} else {{
      fetch(prefix + '/api/track/exit', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: data, keepalive: true}}).catch(function(){{}});
    }}
  }}

  window.addEventListener('beforeunload', sendExit);
  document.addEventListener('visibilitychange', function() {{ if (document.visibilityState === 'hidden') sendExit(); }});
}})();
</script>
"""
    chain_panel = f"""
<style>
.pb-chain{{max-width:860px;margin:60px auto 0;padding:0 24px 40px;font-family:'Poppins',Helvetica,sans-serif}}
.pb-chain-label{{text-align:center;font-size:0.55rem;font-weight:700;letter-spacing:5px;
  color:rgba(255,255,255,0.35);margin-bottom:28px;text-transform:uppercase}}
.pb-chain-cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}}
.pb-chain-card{{position:relative;overflow:hidden;border-radius:14px;padding:28px 22px 22px;
  text-decoration:none;color:#fff;transition:transform 0.25s,box-shadow 0.25s;cursor:pointer;display:block}}
.pb-chain-card:hover{{transform:translateY(-3px);box-shadow:0 8px 32px rgba(0,0,0,0.4)}}
.pb-chain-type{{font-size:0.5rem;font-weight:700;letter-spacing:4px;text-transform:uppercase;
  margin-bottom:12px;display:flex;align-items:center;gap:6px}}
.pb-chain-type svg{{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
.pb-chain-emoji{{font-size:1.6rem;margin-bottom:8px}}
.pb-chain-title{{font-size:0.95rem;font-weight:700;margin-bottom:6px;line-height:1.3}}
.pb-chain-teaser{{font-size:0.78rem;font-weight:400;opacity:0.8;line-height:1.5;
  font-family:'Lora',Georgia,serif;font-style:italic}}
.pb-chain-badge{{display:inline-block;font-size:0.55rem;font-weight:700;letter-spacing:1px;
  padding:3px 10px;border-radius:50px;margin-top:12px;text-transform:uppercase}}
.pb-chain-cta{{display:inline-block;font-size:0.6rem;font-weight:700;letter-spacing:2px;
  padding:6px 16px;border-radius:50px;margin-top:14px;text-transform:uppercase;
  background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.15);transition:all 0.2s}}
.pb-chain-card:hover .pb-chain-cta{{background:rgba(255,255,255,0.2);border-color:rgba(255,255,255,0.3)}}
.pb-chain-card--deeper{{background:linear-gradient(135deg,#1a0a2e 0%,#2d1b4e 100%);
  border:1px solid rgba(232,201,106,0.25)}}
.pb-chain-card--deeper .pb-chain-type{{color:#E8C96A}}
.pb-chain-card--bridge{{border:1px solid rgba(255,255,255,0.1)}}
.pb-chain-card--surprise{{background:linear-gradient(135deg,#0a0a1a 0%,#1a1a2e 100%);
  border:1px solid rgba(255,255,255,0.08)}}
.pb-chain-card--surprise::before{{content:'';position:absolute;top:0;left:0;right:0;bottom:0;
  background:radial-gradient(circle at 30% 20%,rgba(232,201,106,0.06) 0%,transparent 60%),
  radial-gradient(circle at 70% 80%,rgba(123,79,191,0.06) 0%,transparent 60%);pointer-events:none}}
.pb-chain-card--surprise .pb-chain-type{{color:rgba(232,201,106,0.7)}}
@media(max-width:600px){{.pb-chain-cards{{grid-template-columns:1fr}}.pb-chain{{padding:0 16px 32px}}}}
@media print{{.pb-chain{{display:none}}}}
</style>
<section class="pb-chain" id="pb-chain" style="display:none">
  <div class="pb-chain-label">Continue Your Journey</div>
  <div class="pb-chain-cards" id="pb-chain-cards"></div>
</section>
<script>
(function(){{
  var slug = '{slug}';
  var prefix = '';
  try {{ var m = location.pathname.match(/^(\\/[^\\/]+)\\/read\\//); if(m) prefix = m[1]; }} catch(e){{}}

  var ICONS = {{
    deeper: '<svg viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg>',
    bridge: '<svg viewBox="0 0 24 24"><path d="M4 18c0-6 4-10 8-10s8 4 8 10"/><circle cx="4" cy="18" r="1.5"/><circle cx="20" cy="18" r="1.5"/></svg>',
    surprise: '<svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26"/></svg>'
  }};

  var LABELS = {{
    deeper: 'Go Deeper',
    bridge: 'The Bridge',
    surprise: 'The Surprise'
  }};

  fetch(prefix + '/api/v1/discovery/chain/' + slug)
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (!data.recommendations || data.recommendations.length === 0) return;

      var container = document.getElementById('pb-chain-cards');
      data.recommendations.forEach(function(rec) {{
        var card = document.createElement('a');
        card.href = prefix + '/read/' + rec.slug;
        card.className = 'pb-chain-card pb-chain-card--' + rec.connection_type;

        if (rec.connection_type === 'bridge') {{
          card.style.background = 'linear-gradient(135deg, #1a0a2e 0%, ' + rec.category_color + '22 100%)';
        }}

        var ctaText = rec.is_free ? 'Read Free' : '$2.50';
        card.innerHTML =
          '<div class="pb-chain-type">' + (ICONS[rec.connection_type] || '') + ' ' + (LABELS[rec.connection_type] || rec.connection_type) + '</div>' +
          '<div class="pb-chain-emoji">' + (rec.cover_emoji || '') + '</div>' +
          '<div class="pb-chain-title">' + rec.title + '</div>' +
          '<div class="pb-chain-teaser">' + rec.teaser + '</div>' +
          '<span class="pb-chain-badge" style="background:' + rec.category_color + '18;color:' + rec.category_color + '">' + rec.category_name + '</span>' +
          '<br><span class="pb-chain-cta">' + ctaText + '</span>';

        card.addEventListener('click', function() {{
          var clickData = JSON.stringify({{slug: slug, target_slug: rec.slug, connection_type: rec.connection_type}});
          if (navigator.sendBeacon) {{
            navigator.sendBeacon(prefix + '/api/v1/discovery/chain-click', new Blob([clickData], {{type: 'application/json'}}));
          }}
        }});

        container.appendChild(card);
      }});

      document.getElementById('pb-chain').style.display = 'block';
    }})
    .catch(function() {{}});
}})();
</script>
"""
    return html.replace("</body>", back_button + chain_panel + tracking_script + "</body>")


@router.get("/read/{slug}", include_in_schema=False)
async def read_playbook(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    filename = SLUG_TO_FILE.get(slug)
    if not filename:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Playbook Not Found",
                "message": "The playbook you're looking for doesn't exist.",
            },
            status_code=404,
        )

    # Purchase gate: check if playbook is free or session is unlocked
    if slug not in FREE_SLUGS:
        admin_unlocked = request.cookies.get("admin_unlocked") == "1"

        # Check if logged-in user has DB access (subscription or purchase)
        user_id = get_session_user_id(request)
        db_access = False
        if user_id:
            db_access = await _user_has_access(user_id, slug, db)

        if not admin_unlocked and not db_access:
            prefix = settings.URL_PREFIX or ""
            return templates.TemplateResponse(
                "purchase_gate.html",
                {
                    "request": request,
                    "slug": slug,
                    "title": _slug_to_title(slug),
                    "error": request.query_params.get("error"),
                    "prefix": prefix,
                    "logged_in": user_id is not None,
                },
            )

    file_path = ASSETS_DIR / filename
    if not file_path.is_file():
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Playbook Unavailable",
                "message": "This playbook file is temporarily unavailable.",
            },
            status_code=404,
        )

    html = file_path.read_text(encoding="utf-8")
    html = _inject_back_button_and_tracking(html, slug)
    return HTMLResponse(html)


# ============================================================================
# Admin unlock — /read/{slug}/unlock
# ============================================================================
@router.post("/read/{slug}/unlock", include_in_schema=False)
async def unlock_playbook(request: Request, slug: str, code: str = Form("")):
    prefix = settings.URL_PREFIX or ""
    if code.strip() == ADMIN_CODE:
        response = RedirectResponse(url=f"{prefix}/read/{slug}", status_code=303)
        response.set_cookie("admin_unlocked", "1", max_age=86400, httponly=True, samesite="lax")
        return response
    return RedirectResponse(url=f"{prefix}/read/{slug}?error=1", status_code=303)


# ============================================================================
# Authentication — server-rendered sign in / sign up
# ============================================================================
@router.get("/auth", include_in_schema=False)
async def auth_page(request: Request):
    prefix = settings.URL_PREFIX or ""
    # If already logged in, redirect to next or catalog
    user_id = get_session_user_id(request)
    next_url = request.query_params.get("next", f"{prefix}/")
    if user_id:
        return RedirectResponse(url=next_url, status_code=303)

    return templates.TemplateResponse(
        "auth.html",
        {
            "request": request,
            "prefix": prefix,
            "next_url": next_url,
            "error": request.query_params.get("error"),
            "tab": request.query_params.get("tab", "login"),
            "email": request.query_params.get("email", ""),
        },
    )


@router.post("/auth/register", include_in_schema=False)
async def auth_register(
    request: Request,
    db: AsyncSession = Depends(get_db),
    email: str = Form(""),
    password: str = Form(""),
    display_name: str = Form(""),
    next: str = Form(""),
):
    prefix = settings.URL_PREFIX or ""
    next_url = next or f"{prefix}/"
    email = email.strip().lower()

    if not email or not password:
        return RedirectResponse(
            url=f"{prefix}/auth?error=Email+and+password+required&tab=register&next={quote(next_url)}",
            status_code=303,
        )
    if len(password) < 8:
        return RedirectResponse(
            url=f"{prefix}/auth?error=Password+must+be+at+least+8+characters&tab=register&email={quote(email)}&next={quote(next_url)}",
            status_code=303,
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        return RedirectResponse(
            url=f"{prefix}/auth?error=Email+already+registered.+Please+sign+in.&email={quote(email)}&next={quote(next_url)}",
            status_code=303,
        )

    # Create user
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name.strip() or None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    response = RedirectResponse(url=next_url, status_code=303)
    set_session_cookie(response, str(user.id))
    return response


@router.post("/auth/login", include_in_schema=False)
async def auth_login(
    request: Request,
    db: AsyncSession = Depends(get_db),
    email: str = Form(""),
    password: str = Form(""),
    next: str = Form(""),
):
    prefix = settings.URL_PREFIX or ""
    next_url = next or f"{prefix}/"
    email = email.strip().lower()

    if not email or not password:
        return RedirectResponse(
            url=f"{prefix}/auth?error=Email+and+password+required&next={quote(next_url)}",
            status_code=303,
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        return RedirectResponse(
            url=f"{prefix}/auth?error=Invalid+email+or+password&email={quote(email)}&next={quote(next_url)}",
            status_code=303,
        )

    if not user.is_active:
        return RedirectResponse(
            url=f"{prefix}/auth?error=Account+is+inactive&next={quote(next_url)}",
            status_code=303,
        )

    response = RedirectResponse(url=next_url, status_code=303)
    set_session_cookie(response, str(user.id))
    return response


@router.post("/auth/logout", include_in_schema=False)
async def auth_logout():
    prefix = settings.URL_PREFIX or ""
    response = RedirectResponse(url=f"{prefix}/", status_code=303)
    clear_session_cookie(response)
    response.delete_cookie("admin_unlocked")
    return response


# ============================================================================
# Admin: delete user (protected by admin code)
# ============================================================================
@router.delete("/api/admin/user", include_in_schema=False)
async def admin_delete_user(request: Request, email: str = "", code: str = "", db: AsyncSession = Depends(get_db)):
    if code != ADMIN_CODE:
        return JSONResponse({"error": "unauthorized"}, status_code=403)
    if not email:
        return JSONResponse({"error": "email required"}, status_code=400)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return JSONResponse({"error": "user not found"}, status_code=404)

    # Delete related records (cascade should handle most, but be explicit)
    await db.execute(select(Purchase).where(Purchase.user_id == user.id))
    for table in [Purchase, Subscription, StripeCustomer]:
        del_result = await db.execute(select(table).where(table.user_id == user.id))
        for row in del_result.scalars().all():
            await db.delete(row)

    await db.delete(user)
    await db.commit()
    return JSONResponse({"deleted": email})


# ============================================================================
# Helper: check if user has access to a paid playbook (subscription or purchase)
# ============================================================================
async def _user_has_access(user_id: str, slug: str, db: AsyncSession) -> bool:
    """Check if user has an active subscription or has purchased this specific playbook."""
    import uuid as _uuid
    uid = _uuid.UUID(user_id)

    # Check active subscription
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == uid,
            Subscription.status == "active",
            Subscription.current_period_end > datetime.now(timezone.utc),
        )
    )
    if result.scalar_one_or_none():
        return True

    # Check single playbook purchase (by slug in metadata — stored in provider_payment_id field)
    # We store slug in Purchase metadata, so check by provider_session_id or a custom field
    # For now, check purchases where the slug matches
    result = await db.execute(
        select(Purchase).where(
            Purchase.user_id == uid,
            Purchase.status == "completed",
        )
    )
    purchases = result.scalars().all()
    # Check if any purchase metadata contains this slug
    # Since we don't have a slug column, we'll add slug to provider_payment_id as "single:{slug}"
    for p in purchases:
        if p.provider_payment_id and p.provider_payment_id == f"single:{slug}":
            return True

    return False


# ============================================================================
# Email capture / lead magnet
# ============================================================================
@router.post("/subscribe", include_in_schema=False)
async def subscribe_form(
    email: str = Form(""),
    source: str = Form("salmon-journey-ch1"),
):
    email = email.strip()
    if not email:
        return RedirectResponse(url="/", status_code=303)

    # Lazy import to avoid circular deps at module level
    from api.services.email_service import send_lead_magnet_email
    from database import create_subscriber

    create_subscriber(email, source)
    try:
        send_lead_magnet_email(email)
    except Exception as e:
        print(f"Lead magnet email failed: {e}")

    return RedirectResponse(url="/thanks", status_code=303)


@router.get("/thanks", include_in_schema=False)
async def thanks():
    return FileResponse(STATIC_DIR / "thanks.html")


@router.get("/free/salmon-journey-ch1", include_in_schema=False)
async def free_salmon_ch1():
    return FileResponse(STATIC_DIR / "free-salmon-ch1.html")


# ============================================================================
# API — Version, Hot, Tracking
# ============================================================================
@router.get("/api/version", include_in_schema=False)
async def api_version():
    return JSONResponse({"version": APP_VERSION, "notes": RELEASE_NOTES[:3]})


@router.get("/api/hot", include_in_schema=False)
async def api_hot(period: str = "all"):
    from database import get_hot_playbooks
    hot = get_hot_playbooks(period, limit=3)
    return JSONResponse(hot)


@router.post("/api/track/view", include_in_schema=False)
async def track_view(request: Request):
    data = await request.json()
    slug = data.get("slug", "").strip()
    if not slug:
        return JSONResponse({"error": "slug required"}, status_code=400)
    from database import log_playbook_view
    log_playbook_view(slug, request.client.host if request.client else None, request.headers.get("User-Agent"))
    return JSONResponse({"ok": True})


@router.post("/api/track/exit", include_in_schema=False)
async def track_exit(request: Request):
    data = await request.json()
    slug = data.get("slug", "").strip()
    scroll_percent = data.get("scroll_percent", 0)
    time_spent = data.get("time_spent_secs", 0)
    if not slug:
        return JSONResponse({"error": "slug required"}, status_code=400)
    from database import log_playbook_exit
    log_playbook_exit(slug, scroll_percent, time_spent, request.client.host if request.client else None)
    return JSONResponse({"ok": True})


# ============================================================================
# Stripe checkout (legacy — form-post flow)
# ============================================================================
@router.post("/create-checkout-session", include_in_schema=False)
async def checkout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    mode: str = Form("single"),
    slug: str = Form(""),
):
    prefix = settings.URL_PREFIX or ""
    base = settings.BASE_URL

    # Require authentication before checkout
    user_id = get_session_user_id(request)
    if not user_id:
        # Redirect to auth, then back to checkout
        next_url = f"{prefix}/checkout-redirect?mode={quote(mode)}&slug={quote(slug)}"
        return RedirectResponse(url=f"{prefix}/auth?next={quote(next_url)}", status_code=303)

    # Load user email for Stripe pre-fill
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    customer_email = user.email if user else None

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Pick the right price ID and Stripe mode
    if mode == "monthly":
        price_id = settings.STRIPE_PRICE_MONTHLY
        stripe_mode = "subscription"
        metadata = {"mode": "monthly", "user_id": user_id}
    elif mode == "yearly":
        price_id = settings.STRIPE_PRICE_YEARLY
        stripe_mode = "subscription"
        metadata = {"mode": "yearly", "user_id": user_id}
    else:
        price_id = settings.STRIPE_PRICE_SINGLE or settings.STRIPE_PRICE_ID
        stripe_mode = "payment"
        metadata = {"mode": "single", "slug": slug, "user_id": user_id}

    if not price_id:
        return JSONResponse({"error": "Stripe price not configured"}, status_code=500)

    cancel_path = f"/read/{slug}" if slug and slug != "all" else "/"

    try:
        session_params = {
            "mode": stripe_mode,
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": f"{base}/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{base}{cancel_path}?payment=cancelled",
            "metadata": metadata,
        }
        if customer_email:
            session_params["customer_email"] = customer_email
        if stripe_mode == "payment":
            session_params["customer_creation"] = "always"

        session = stripe.checkout.Session.create(**session_params)
        return RedirectResponse(url=session.url, status_code=303)
    except Exception as e:
        print(f"Stripe checkout error: {e}")
        return RedirectResponse(
            url=f"{base}{cancel_path}?payment=error",
            status_code=303,
        )


@router.get("/checkout-redirect", include_in_schema=False)
async def checkout_redirect(request: Request):
    """After auth, auto-submit the checkout form via a self-posting page."""
    prefix = settings.URL_PREFIX or ""
    mode = request.query_params.get("mode", "single")
    slug = request.query_params.get("slug", "")
    # Render a page that auto-submits a POST form
    html = f"""<!DOCTYPE html><html><body>
    <form id="f" method="POST" action="{prefix}/create-checkout-session">
      <input type="hidden" name="mode" value="{mode}">
      <input type="hidden" name="slug" value="{slug}">
    </form>
    <script>document.getElementById('f').submit();</script>
    </body></html>"""
    return HTMLResponse(html)


# ============================================================================
# Stripe webhook (legacy)
# ============================================================================
@router.post("/webhook/stripe", include_in_schema=False)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(obj, db)
    elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
        await _handle_subscription_updated(obj, db)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(obj, db)

    return {"status": "ok"}


async def _handle_checkout_completed(session: dict, db: AsyncSession) -> None:
    """Record purchase in PostgreSQL linked to the user, send delivery email."""
    import uuid as _uuid

    session_id = session["id"]
    metadata = session.get("metadata", {})
    mode = metadata.get("mode", "single")
    user_id_str = metadata.get("user_id")
    customer_email = session.get("customer_details", {}).get("email", "")
    amount_cents = session.get("amount_total", 0)

    # Also write to legacy SQLite for backward compatibility
    try:
        from database import create_purchase as legacy_create, get_purchase_by_session_id as legacy_get
        if not legacy_get(session_id):
            download_token = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(days=365)
            legacy_create(
                stripe_session_id=session_id,
                customer_email=customer_email,
                download_token=download_token,
                downloads_remaining=99,
                expires_at=expires_at,
                stripe_payment_intent=session.get("payment_intent"),
                amount_cents=amount_cents,
            )
    except Exception as e:
        print(f"Legacy SQLite write failed (non-critical): {e}")

    if not user_id_str:
        print(f"Webhook: no user_id in metadata for session {session_id}")
        return

    uid = _uuid.UUID(user_id_str)

    if mode == "single":
        slug = metadata.get("slug", "")
        # Create Purchase record in PostgreSQL
        purchase = Purchase(
            user_id=uid,
            payment_provider="stripe",
            provider_payment_id=f"single:{slug}",
            provider_session_id=session_id,
            amount_cents=amount_cents,
            status="completed",
            download_token=secrets.token_urlsafe(32),
            downloads_remaining=99,
            download_expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        )
        db.add(purchase)

    elif mode in ("monthly", "yearly"):
        # Subscription — record will be created by subscription.created webhook
        # But also create/link StripeCustomer
        stripe_customer_id = session.get("customer")
        if stripe_customer_id:
            result = await db.execute(
                select(StripeCustomer).where(StripeCustomer.user_id == uid)
            )
            if not result.scalar_one_or_none():
                db.add(StripeCustomer(user_id=uid, stripe_customer_id=stripe_customer_id))

    await db.commit()

    # Send delivery email
    try:
        from api.services.email_service import send_delivery_email
        send_delivery_email(customer_email, "")
    except Exception as e:
        print(f"Delivery email failed: {e}")


async def _handle_subscription_updated(subscription: dict, db: AsyncSession) -> None:
    """Create or update a Subscription record linked to the user."""
    import uuid as _uuid

    stripe_sub_id = subscription.get("id", "")
    stripe_status = subscription.get("status", "")
    stripe_customer_id = subscription.get("customer", "")
    period_start = subscription.get("current_period_start")
    period_end = subscription.get("current_period_end")

    # Map Stripe status
    if stripe_status in ("active", "trialing"):
        db_status = "active"
    elif stripe_status == "past_due":
        db_status = "past_due"
    else:
        db_status = "canceled"

    # Find user by StripeCustomer
    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.stripe_customer_id == stripe_customer_id)
    )
    sc = result.scalar_one_or_none()
    if not sc:
        print(f"Webhook: no StripeCustomer for {stripe_customer_id}")
        return

    # Check if subscription already exists
    result = await db.execute(
        select(Subscription).where(Subscription.provider_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    ps = datetime.fromtimestamp(period_start, tz=timezone.utc) if period_start else now
    pe = datetime.fromtimestamp(period_end, tz=timezone.utc) if period_end else now + timedelta(days=30)

    # Determine plan type from price
    plan_items = subscription.get("items", {}).get("data", [])
    price_id = plan_items[0]["price"]["id"] if plan_items else ""
    if price_id == settings.STRIPE_PRICE_YEARLY:
        plan_type = "yearly"
        price_cents = 10000
    else:
        plan_type = "monthly"
        price_cents = 1000

    if sub:
        sub.status = db_status
        sub.current_period_start = ps
        sub.current_period_end = pe
        sub.updated_at = now
    else:
        sub = Subscription(
            user_id=sc.user_id,
            plan_type=plan_type,
            price_cents=price_cents,
            payment_provider="stripe",
            provider_subscription_id=stripe_sub_id,
            status=db_status,
            current_period_start=ps,
            current_period_end=pe,
        )
        db.add(sub)

    await db.commit()


async def _handle_subscription_deleted(subscription: dict, db: AsyncSession) -> None:
    """Mark subscription as canceled."""
    stripe_sub_id = subscription.get("id", "")
    result = await db.execute(
        select(Subscription).where(Subscription.provider_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.status = "canceled"
        sub.updated_at = datetime.now(timezone.utc)
        await db.commit()


# ============================================================================
# Success page
# ============================================================================
@router.get("/success", include_in_schema=False)
async def success_page(request: Request, session_id: str | None = None):
    prefix = settings.URL_PREFIX or ""
    if not session_id:
        return RedirectResponse(url=f"{prefix}/", status_code=303)

    # Try to retrieve the Stripe session to get metadata
    stripe.api_key = settings.STRIPE_SECRET_KEY
    slug = ""
    mode = "single"
    try:
        stripe_session = stripe.checkout.Session.retrieve(session_id)
        metadata = stripe_session.get("metadata", {})
        slug = metadata.get("slug", "")
        mode = metadata.get("mode", "single")
    except Exception:
        pass

    # Try legacy DB lookup
    purchase = None
    try:
        from database import get_purchase_by_session_id
        purchase = get_purchase_by_session_id(session_id)
    except Exception:
        pass

    email = ""
    download_token = ""
    if purchase:
        email = purchase["customer_email"]
        download_token = purchase["download_token"]

    response = templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "download_token": download_token,
            "email": email,
            "base_url": settings.BASE_URL,
            "slug": slug,
            "prefix": prefix,
        },
    )

    # Only set admin_unlocked (all-access) for subscriptions.
    # Single purchases rely on per-slug DB access checked in read_playbook.
    if mode in ("monthly", "yearly"):
        response.set_cookie("admin_unlocked", "1", max_age=86400, httponly=True, samesite="lax")

    return response


# ============================================================================
# Download
# ============================================================================
@router.get("/download/{token}", include_in_schema=False)
async def download(request: Request, token: str):
    from database import get_purchase_by_token, decrement_download, log_download

    purchase = get_purchase_by_token(token)

    if not purchase:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Invalid Link",
                "message": "This download link is not valid. Please check your email for the correct link.",
            },
            status_code=404,
        )

    # Check expiration
    expires_at = datetime.fromisoformat(purchase["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Link Expired",
                "message": (
                    "This download link has expired (30-day limit). "
                    "Please contact support@kingdombuilders.ai for assistance."
                ),
            },
            status_code=410,
        )

    # Check remaining downloads
    if purchase["downloads_remaining"] <= 0:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Download Limit Reached",
                "message": (
                    "You've used all 5 downloads for this purchase. "
                    "Please contact support@kingdombuilders.ai for assistance."
                ),
            },
            status_code=403,
        )

    # Check PDF exists
    if not settings.PDF_PATH.exists():
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "File Unavailable",
                "message": (
                    "The file is temporarily unavailable. Please try again later "
                    "or contact support@kingdombuilders.ai."
                ),
            },
            status_code=503,
        )

    # Decrement counter and log
    decrement_download(purchase["id"])
    log_download(
        purchase_id=purchase["id"],
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent", ""),
    )

    return FileResponse(
        path=settings.PDF_PATH,
        filename="The-Conductors-Playbook-KingdomBuildersAI.pdf",
        media_type="application/pdf",
    )


# ============================================================================
# Legal pages
# ============================================================================
@router.get("/terms", include_in_schema=False)
async def terms():
    return FileResponse(STATIC_DIR / "terms.html")


@router.get("/privacy", include_in_schema=False)
async def privacy():
    return FileResponse(STATIC_DIR / "privacy.html")


@router.get("/refund", include_in_schema=False)
async def refund():
    return FileResponse(STATIC_DIR / "refund.html")
