"""
Legacy backward-compatibility router.

Reproduces every route from the original Flask app.py so existing
URLs (landing pages, reader, checkout, downloads, legal pages) continue
to work without any changes on the client side.
"""

import secrets
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlencode

import httpx
import stripe
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates

from api.config import settings
from api.database import get_db
from api.models.activity import ReadingProgress
from api.models.playbook import Playbook
from api.models.user import User, OAuthAccount, VerificationToken
from api.models.purchase import Purchase, Subscription, StripeCustomer
from api.utils.security import hash_password, verify_password, generate_token, hash_token
from api.utils.session import get_session_user_id, set_session_cookie, clear_session_cookie
from api.services.referral_service import (
    ensure_referral_code,
    process_referral_cookie,
    process_commissions,
    cancel_pending_commissions,
    handle_refund_commissions,
)

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
APP_VERSION = "2.7.0"
RELEASE_NOTES = [
    {
        "version": "2.7.0",
        "date": "2026-03-11",
        "title": "How AI Works Series Launch",
        "changes": [
            "New series: How AI Works (4 parts)",
            "New playbook: The Lyrebird\u2019s Echo (How AI Music Works, Part 4 of 4)",
            "New playbook: The Cuttlefish\u2019s Canvas (How AI Images Work, Part 2 of 4)",
            "New playbook: The Centipede\u2019s March (How AI Video Works, Part 3 of 4)",
            "The Mockingbird\u2019s Song now Part 1 of How AI Works series",
            "51 playbooks now live",
        ],
    },
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
    "conductors-playbook",
    "lay-it-down",
    "the-mockingbirds-song",
    "the-lifted-ceiling",
    "the-tide-pools-echo",
    "dad-talks-the-dopamine-drought",
    "the-mantis-shrimps-eye",
    "the-hermit-crabs-shell",
}

ADMIN_CODE = settings.ADMIN_UNLOCK_CODE

# Simple in-memory rate limiter for checkout (max 5 attempts per IP per 60s)
_checkout_attempts: dict[str, list[float]] = defaultdict(list)
_CHECKOUT_RATE_LIMIT = 5
_CHECKOUT_RATE_WINDOW = 60  # seconds


def _is_checkout_rate_limited(ip: str) -> bool:
    now = time.monotonic()
    attempts = _checkout_attempts[ip]
    # Prune old entries
    _checkout_attempts[ip] = [t for t in attempts if now - t < _CHECKOUT_RATE_WINDOW]
    if len(_checkout_attempts[ip]) >= _CHECKOUT_RATE_LIMIT:
        return True
    _checkout_attempts[ip].append(now)
    return False


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
    "/dadtalkstheflinch": "dad-talks-the-flinch.html",
    "/dadtalksthetwowallets": "dad-talks-the-two-wallets.html",
    "/dadtalkstheinvisiblecontract": "dad-talks-the-invisible-contract.html",
    "/dadtalksthescoreboardlie": "dad-talks-the-scoreboard-lie.html",
    "/dadtalksthefirstpunch": "dad-talks-the-first-punch.html",
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
    "/themantisshrimpseye": "the-mantis-shrimps-eye.html",
    "/theporcupinesquills": "the-porcupines-quills.html",
    "/thetardigradeprotocol": "the-tardigrade-protocol.html",
    "/thehermitcrabsshell": "the-hermit-crabs-shell.html",
    "/thescorpionsmolt": "the-scorpions-molt.html",
    "/thevampiresquidslight": "the-vampire-squids-light.html",
    "/thecuttlefishscanvas": "the-cuttlefishs-canvas.html",
    "/thelyrebirdsecho": "the-lyrebirds-echo.html",
    "/thecentipedesmarch": "the-centipedes-march.html",
    "/theravenstrial": "the-ravens-trial.html",
    "/theliftedceiling": "the-lifted-ceiling.html",
    "/thenewearning": "the-new-earning.html",
    "/thethreetables": "the-three-tables.html",
    "/thekintsugibow": "the-kintsugi-bowl.html",
    "/theunfinishedsong": "the-unfinished-song.html",
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
    "dad-talks-the-flinch": "Dad_Talks_The_Flinch.html",
    "dad-talks-the-two-wallets": "Dad_Talks_The_Two_Wallets.html",
    "dad-talks-the-invisible-contract": "Dad_Talks_The_Invisible_Contract.html",
    "dad-talks-the-scoreboard-lie": "Dad_Talks_The_Scoreboard_Lie.html",
    "dad-talks-the-first-punch": "Dad_Talks_The_First_Punch.html",
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
    "the-mantis-shrimps-eye": "The_Mantis_Shrimps_Eye.html",
    "the-porcupines-quills": "The_Porcupines_Quills.html",
    "the-tardigrade-protocol": "The_Tardigrade_Protocol.html",
    "the-hermit-crabs-shell": "The_Hermit_Crabs_Shell.html",
    "the-scorpions-molt": "The_Scorpions_Molt.html",
    "the-vampire-squids-light": "The_Vampire_Squids_Light.html",
    "the-cuttlefishs-canvas": "The_Cuttlefishs_Canvas.html",
    "the-lyrebirds-echo": "The_Lyrebirds_Echo.html",
    "the-centipedes-march": "The_Centipedes_March.html",
    "the-ravens-trial": "The_Ravens_Trial.html",
    "the-lifted-ceiling": "The_Lifted_Ceiling.html",
    "the-new-earning": "The_New_Earning.html",
    "the-three-tables": "The_Three_Tables.html",
    "the-kintsugi-bowl": "The_Kintsugi_Bowl_The_Wandering_Eye.html",
    "the-unfinished-song": "The_Unfinished_Song.html",
}


def _redirect_with_cookie(url: str, response: HTMLResponse = None) -> HTMLResponse:
    """Return a 200 HTML page that redirects via JS.

    Cloudflare follows 303 redirects server-side, which strips Set-Cookie
    headers before they reach the browser.  Returning a 200 with an HTML
    redirect preserves cookies reliably.
    """
    if response is None:
        response = HTMLResponse(content="", status_code=200)
    html = (
        '<!DOCTYPE html><html><head>'
        f'<meta http-equiv="refresh" content="0;url={url}">'
        f'<script>window.location.href="{url}";</script>'
        '</head><body></body></html>'
    )
    response.body = html.encode()
    response.headers["content-type"] = "text/html; charset=utf-8"
    response.headers["content-length"] = str(len(response.body))
    return response


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
  var lastChapter = null;

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

  /* Detect chapter headings (h2 elements) the user has scrolled past */
  function getCurrentChapter() {{
    var headings = document.querySelectorAll('.page h2, .section h2');
    var current = null;
    var scrollY = window.scrollY || window.pageYOffset;
    for (var i = 0; i < headings.length; i++) {{
      if (headings[i].getBoundingClientRect().top + scrollY <= scrollY + 120) {{
        current = headings[i].textContent.trim();
      }}
    }}
    return current;
  }}

  /* Update lastChapter on scroll */
  var chapterTimer = null;
  function trackChapter() {{
    if (chapterTimer) return;
    chapterTimer = setTimeout(function() {{
      chapterTimer = null;
      var ch = getCurrentChapter();
      if (ch) lastChapter = ch;
    }}, 300);
  }}
  window.addEventListener('scroll', trackChapter, {{passive: true}});

  function sendExit() {{
    if (tracked) return;
    tracked = true;
    var ch = getCurrentChapter();
    if (ch) lastChapter = ch;
    var data = JSON.stringify({{
      slug: slug,
      scroll_percent: getScrollPercent(),
      time_spent_secs: Math.round((Date.now() - startTime) / 1000),
      last_chapter: lastChapter
    }});
    if (navigator.sendBeacon) {{
      navigator.sendBeacon(prefix + '/api/track/exit', new Blob([data], {{type: 'application/json'}}));
    }} else {{
      fetch(prefix + '/api/track/exit', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: data, keepalive: true}}).catch(function(){{}});
    }}
  }}

  window.addEventListener('beforeunload', sendExit);
  document.addEventListener('visibilitychange', function() {{ if (document.visibilityState === 'hidden') sendExit(); }});

  // Journey completion tracking: mark complete when scroll >= 90%
  var completionSent = false;
  function checkCompletion() {{
    if (completionSent) return;
    var pct = getScrollPercent();
    if (pct >= 90) {{
      completionSent = true;
      fetch(prefix + '/api/v1/discovery/journey/complete', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        credentials: 'include',
        body: JSON.stringify({{slug: slug, scroll_percent: pct}})
      }}).catch(function(){{}});
    }}
  }}
  window.addEventListener('scroll', checkCompletion, {{passive: true}});
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
    ga_snippet = ""
    if settings.GA_MEASUREMENT_ID:
        ga_id = settings.GA_MEASUREMENT_ID
        ga_snippet = f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{ga_id}');</script>
"""
    # Email capture slide-in for free playbooks only
    is_free = slug in FREE_SLUGS
    email_slidein = ""
    if is_free:
        email_slidein = f"""
<style>
#pb-email-slide{{position:fixed;bottom:24px;right:24px;z-index:9998;width:320px;max-width:calc(100vw - 48px);
  background:rgba(10,6,20,0.95);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
  border:1px solid rgba(232,201,106,0.2);border-radius:16px;padding:24px 20px 20px;
  font-family:'Poppins',Helvetica,sans-serif;color:#fff;
  transform:translateY(120%);opacity:0;transition:transform 0.45s cubic-bezier(0.16,1,0.3,1),opacity 0.45s ease;
  box-shadow:0 8px 32px rgba(0,0,0,0.5)}}
#pb-email-slide.show{{transform:translateY(0);opacity:1}}
#pb-email-slide .pb-es-close{{position:absolute;top:10px;right:12px;background:none;border:none;color:rgba(255,255,255,0.4);
  font-size:1.1rem;cursor:pointer;padding:4px 8px;transition:color 0.2s}}
#pb-email-slide .pb-es-close:hover{{color:#fff}}
#pb-email-slide .pb-es-emoji{{font-size:1.4rem;margin-bottom:6px}}
#pb-email-slide .pb-es-heading{{font-size:0.95rem;font-weight:700;margin-bottom:4px;line-height:1.3}}
#pb-email-slide .pb-es-sub{{font-size:0.78rem;color:rgba(255,255,255,0.6);margin-bottom:14px;line-height:1.5;
  font-family:'Lora',Georgia,serif}}
#pb-email-slide .pb-es-form{{display:flex;gap:8px}}
#pb-email-slide .pb-es-input{{flex:1;padding:9px 12px;border-radius:8px;border:1px solid rgba(255,255,255,0.12);
  background:rgba(255,255,255,0.06);color:#fff;font-size:0.82rem;font-family:'Poppins',Helvetica,sans-serif;
  outline:none;transition:border-color 0.2s}}
#pb-email-slide .pb-es-input:focus{{border-color:rgba(212,168,67,0.4)}}
#pb-email-slide .pb-es-input::placeholder{{color:rgba(255,255,255,0.3)}}
#pb-email-slide .pb-es-btn{{padding:9px 16px;border-radius:8px;border:none;background:#D4A843;color:#0a0614;
  font-size:0.78rem;font-weight:700;font-family:'Poppins',Helvetica,sans-serif;cursor:pointer;
  transition:background 0.2s;white-space:nowrap}}
#pb-email-slide .pb-es-btn:hover{{background:#E8C96A}}
#pb-email-slide .pb-es-btn:disabled{{opacity:0.6;cursor:not-allowed}}
#pb-email-slide .pb-es-msg{{font-size:0.85rem;font-weight:600;text-align:center;padding:8px 0}}
@media(max-width:600px){{#pb-email-slide{{right:0;bottom:0;width:100%;max-width:100%;
  border-radius:16px 16px 0 0;border-bottom:none}}}}
@media print{{#pb-email-slide{{display:none}}}}
</style>
<div id="pb-email-slide">
  <button class="pb-es-close" onclick="document.getElementById('pb-email-slide').classList.remove('show');localStorage.setItem('pb_email_dismissed',Date.now().toString())" aria-label="Close">&times;</button>
  <div class="pb-es-emoji">\U0001F4EC</div>
  <div class="pb-es-heading">Enjoying this playbook?</div>
  <div class="pb-es-sub">Get more like this delivered to your inbox. Free.</div>
  <div id="pb-es-form-wrap">
    <form class="pb-es-form" id="pb-es-form" onsubmit="return false">
      <input class="pb-es-input" type="email" id="pb-es-email" placeholder="Your email" required>
      <button class="pb-es-btn" type="submit" id="pb-es-submit">Send</button>
    </form>
  </div>
</div>
<script>
(function(){{
  var panel = document.getElementById('pb-email-slide');
  if (!panel) return;

  // Check localStorage: skip if recently dismissed or already subscribed
  var dismissed = localStorage.getItem('pb_email_dismissed');
  if (dismissed) {{
    var ts = parseInt(dismissed, 10);
    if (!isNaN(ts) && Date.now() - ts < 7 * 24 * 60 * 60 * 1000) return;
  }}
  if (localStorage.getItem('pb_subscribed')) return;

  // Show panel after 60% scroll
  var slideShown = false;
  window.addEventListener('scroll', function() {{
    if (slideShown) return;
    var h = document.documentElement;
    var b = document.body;
    var st = h.scrollTop || b.scrollTop;
    var sh = (h.scrollHeight || b.scrollHeight) - h.clientHeight;
    var pct = sh > 0 ? (st / sh) * 100 : 0;
    if (pct >= 60) {{
      slideShown = true;
      panel.classList.add('show');
    }}
  }}, {{passive: true}});

  // Form submission
  var prefix = '';
  try {{ var m = location.pathname.match(/^(\\/[^\\/]+)\\/read\\//); if(m) prefix = m[1]; }} catch(e){{}}
  var form = document.getElementById('pb-es-form');
  var emailInput = document.getElementById('pb-es-email');
  var submitBtn = document.getElementById('pb-es-submit');
  var wrap = document.getElementById('pb-es-form-wrap');

  form.addEventListener('submit', function(e) {{
    e.preventDefault();
    var email = emailInput.value.trim();
    if (!email) return;
    submitBtn.disabled = true;
    submitBtn.textContent = '...';
    fetch(prefix + '/api/v1/subscribe', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{email: email, source: 'reader-slidein'}})
    }})
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      localStorage.setItem('pb_subscribed', '1');
      wrap.innerHTML = '<div class="pb-es-msg" style="color:#E8C96A">Check your inbox \u2709\uFE0F</div>';
      setTimeout(function() {{ panel.classList.remove('show'); }}, 4000);
    }})
    .catch(function() {{
      submitBtn.disabled = false;
      submitBtn.textContent = 'Send';
      wrap.insertAdjacentHTML('afterbegin', '<div style="color:#e57373;font-size:0.75rem;margin-bottom:8px">Something went wrong. Try again.</div>');
    }});
  }});
}})();
</script>
"""
    rating_popup = f"""
<style>
#pb-rate-popup{{position:fixed;bottom:24px;left:24px;z-index:9997;width:340px;max-width:calc(100vw - 48px);
  background:rgba(10,6,20,0.95);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
  border:1px solid rgba(232,201,106,0.2);border-radius:16px;padding:24px 20px 20px;
  font-family:'Poppins',Helvetica,sans-serif;color:#fff;
  transform:translateY(120%);opacity:0;transition:transform 0.45s cubic-bezier(0.16,1,0.3,1),opacity 0.45s ease;
  box-shadow:0 8px 32px rgba(0,0,0,0.5)}}
#pb-rate-popup.show{{transform:translateY(0);opacity:1}}
#pb-rate-popup .pb-rate-close{{position:absolute;top:10px;right:12px;background:none;border:none;color:rgba(255,255,255,0.4);
  font-size:1.1rem;cursor:pointer;padding:4px 8px;transition:color 0.2s}}
#pb-rate-popup .pb-rate-close:hover{{color:#fff}}
#pb-rate-popup .pb-rate-heading{{font-size:0.95rem;font-weight:700;margin-bottom:12px;line-height:1.3}}
#pb-rate-popup .pb-rate-stars{{display:flex;gap:4px;margin-bottom:14px}}
#pb-rate-popup .pb-rate-star{{cursor:pointer;transition:transform 0.15s}}
#pb-rate-popup .pb-rate-star:hover{{transform:scale(1.15)}}
#pb-rate-popup .pb-rate-star svg{{width:28px;height:28px}}
#pb-rate-popup .pb-rate-star svg path{{transition:fill 0.15s,stroke 0.15s}}
#pb-rate-popup .pb-rate-textarea{{width:100%;padding:10px 12px;border-radius:10px;border:1px solid rgba(255,255,255,0.1);
  background:rgba(255,255,255,0.05);color:#fff;font-size:0.78rem;font-family:'Poppins',Helvetica,sans-serif;
  outline:none;resize:vertical;min-height:70px;transition:border-color 0.2s;margin-bottom:12px}}
#pb-rate-popup .pb-rate-textarea:focus{{border-color:rgba(212,168,67,0.4)}}
#pb-rate-popup .pb-rate-textarea::placeholder{{color:rgba(255,255,255,0.25)}}
#pb-rate-popup .pb-rate-btn{{width:100%;padding:10px;border-radius:10px;border:none;background:#D4A843;color:#0a0614;
  font-size:0.78rem;font-weight:700;font-family:'Poppins',Helvetica,sans-serif;cursor:pointer;
  transition:background 0.2s;letter-spacing:0.5px}}
#pb-rate-popup .pb-rate-btn:hover{{background:#E8C96A}}
#pb-rate-popup .pb-rate-btn:disabled{{opacity:0.6;cursor:not-allowed}}
#pb-rate-popup .pb-rate-msg{{font-size:0.85rem;font-weight:600;text-align:center;padding:8px 0;color:#E8C96A}}
@media(max-width:600px){{#pb-rate-popup{{left:0;bottom:0;width:100%;max-width:100%;border-radius:16px 16px 0 0;border-bottom:none}}}}
@media print{{#pb-rate-popup{{display:none}}}}
</style>
<div id="pb-rate-popup">
  <button class="pb-rate-close" onclick="document.getElementById('pb-rate-popup').classList.remove('show');localStorage.setItem('pb_rate_dismissed_{slug}','1')" aria-label="Close">&times;</button>
  <div class="pb-rate-heading">Rate This Playbook</div>
  <div class="pb-rate-stars" id="pb-rate-stars"></div>
  <div id="pb-rate-form-wrap">
    <form id="pb-rate-form" onsubmit="return false">
      <textarea class="pb-rate-textarea" id="pb-rate-comment" placeholder="Please provide any edits, corrections, suggestions to extend or modify here and we'll review to improve the content."></textarea>
      <button class="pb-rate-btn" type="submit" id="pb-rate-submit">Submit Feedback</button>
    </form>
  </div>
</div>
<script>
(function(){{
  var popup = document.getElementById('pb-rate-popup');
  if (!popup) return;
  var slug = '{slug}';

  // Skip if already rated or dismissed
  if (localStorage.getItem('pb_rated_' + slug) || localStorage.getItem('pb_rate_dismissed_' + slug)) return;

  var prefix = '';
  try {{ var m = location.pathname.match(/^(\\/[^\\/]+)\\/read\\//); if(m) prefix = m[1]; }} catch(e){{}}

  // Build star SVGs
  var starsWrap = document.getElementById('pb-rate-stars');
  var selectedRating = 0;
  var starEls = [];
  for (var i = 1; i <= 5; i++) {{
    (function(n){{
      var span = document.createElement('span');
      span.className = 'pb-rate-star';
      span.innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 21 12 17.77 5.82 21 7 14.14l-5-4.87 6.91-1.01L12 2z" fill="rgba(255,255,255,0.1)" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/></svg>';
      span.onclick = function(){{
        selectedRating = n;
        updateStars();
      }};
      starsWrap.appendChild(span);
      starEls.push(span);
    }})(i);
  }}

  function updateStars(){{
    for (var j = 0; j < starEls.length; j++){{
      var path = starEls[j].querySelector('path');
      if (j < selectedRating){{
        path.setAttribute('fill', '#D4A843');
        path.setAttribute('stroke', '#E8C96A');
      }} else {{
        path.setAttribute('fill', 'rgba(255,255,255,0.1)');
        path.setAttribute('stroke', 'rgba(255,255,255,0.2)');
      }}
    }}
  }}

  // Show after 80% scroll with 3s delay
  var rateShown = false;
  window.addEventListener('scroll', function(){{
    if (rateShown) return;
    var h = document.documentElement;
    var b = document.body;
    var st = h.scrollTop || b.scrollTop;
    var sh = (h.scrollHeight || b.scrollHeight) - h.clientHeight;
    var pct = sh > 0 ? (st / sh) * 100 : 0;
    if (pct >= 80){{
      rateShown = true;
      setTimeout(function(){{
        // Skip if email slide-in is showing
        var emailSlide = document.getElementById('pb-email-slide');
        if (emailSlide && emailSlide.classList.contains('show')) {{
          // Wait for it to dismiss, then show
          var check = setInterval(function(){{
            if (!emailSlide.classList.contains('show')){{
              clearInterval(check);
              popup.classList.add('show');
            }}
          }}, 1000);
        }} else {{
          popup.classList.add('show');
        }}
      }}, 3000);
    }}
  }}, {{passive: true}});

  // Submit
  var form = document.getElementById('pb-rate-form');
  var submitBtn = document.getElementById('pb-rate-submit');
  var wrap = document.getElementById('pb-rate-form-wrap');

  form.addEventListener('submit', function(e){{
    e.preventDefault();
    if (selectedRating === 0) {{
      // Flash stars to indicate selection needed
      starsWrap.style.outline = '2px solid rgba(212,168,67,0.6)';
      starsWrap.style.borderRadius = '8px';
      setTimeout(function(){{ starsWrap.style.outline = 'none'; }}, 1500);
      return;
    }}
    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending...';

    var startTime = window._pbStartTime || Date.now();
    var h2 = document.documentElement;
    var b2 = document.body;
    var st2 = h2.scrollTop || b2.scrollTop;
    var sh2 = (h2.scrollHeight || b2.scrollHeight) - h2.clientHeight;
    var scrollPct = sh2 > 0 ? Math.round((st2 / sh2) * 100) : 0;

    fetch(prefix + '/api/v1/feedback', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        slug: slug,
        rating: selectedRating,
        comment: document.getElementById('pb-rate-comment').value.trim() || null,
        scroll_percent: scrollPct,
        time_spent_secs: Math.round((Date.now() - startTime) / 1000)
      }})
    }})
    .then(function(r){{ return r.json(); }})
    .then(function(data){{
      localStorage.setItem('pb_rated_' + slug, '1');
      wrap.innerHTML = '<div class="pb-rate-msg">Thank you for your feedback!</div>';
      document.querySelector('.pb-rate-stars').style.display = 'none';
      setTimeout(function(){{ popup.classList.remove('show'); }}, 3000);
    }})
    .catch(function(){{
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Feedback';
    }});
  }});
}})();
</script>
"""

    # ---- Print / PDF stylesheet + auto-print trigger ----
    print_css = """
<style id="pb-print-css">
@media print {
  @page {
    size: letter;
    margin: 16mm 14mm 20mm 14mm;
  }

  /* --- Hide interactive / overlay elements --- */
  .pb-back, .chain-panel, .email-slidein, .rating-popup,
  .pb-print-trigger, nav, .cookie-banner,
  script, .spark, .ghost-noise { display: none !important; }

  /* --- Base resets --- */
  html { font-size: 16px; }
  body { background: white !important; color: #1A1A1A !important;
         -webkit-print-color-adjust: exact !important;
         print-color-adjust: exact !important; }

  /* --- Cover: full first page --- */
  .cover { min-height: auto; padding: 60px 30px; break-after: page;
           background: linear-gradient(175deg,#0A1218,#1A2A38 40%,#2A3A48 70%,#1A2A38) !important;
           -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
  .cover-art svg { filter: none !important; }
  .cover * { animation: none !important; }

  /* --- Page layout --- */
  .page { max-width: 100%; padding: 0; }
  .section { padding: 28px 0; }

  /* --- Prevent these visual blocks from splitting across pages --- */
  .scene, .memory, .wisdom, .dad-voice, .viz, .adventure,
  .taste-recipe, .reflect, .compare-table, .final-test,
  .prompt, .think, .insight, .mission, .root-ck, .root-check,
  .gear, .meter, .cut, .ba-pair, .invert-pair, .gq,
  .tl-item, .rm-item, .dd, .deep-dive, .inst, .id-card,
  .ribbon, .flow { break-inside: avoid; }

  /* --- Chapter headers start new page --- */
  .ch-head { break-before: page; }

  /* --- Finale: own page --- */
  .finale { break-before: page; padding: 60px 20px;
            background: linear-gradient(175deg,#0A1218,#1A2A38) !important;
            -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
  .finale * { animation: none !important; }

  /* --- Footer --- */
  footer { break-before: avoid; margin-top: 20px; }

  /* --- Kill all animations --- */
  *, *::before, *::after {
    animation: none !important;
    transition: none !important;
  }

  /* --- Box styling: preserve backgrounds & borders --- */
  .memory { background: linear-gradient(135deg,#0A1218,#1A2838) !important;
             -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
  .memory-inner { border-color: rgba(200,74,48,0.25) !important; }

  .viz { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
  .viz-glow, .memory-glow { display: none !important; }

  .scene { box-shadow: none; border-left: 4px solid #C84A30; }
  .wisdom { box-shadow: none; }
  .dad-voice { box-shadow: none; }
  .compare-table { box-shadow: none; }
  .prompt { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
  .reflect { box-shadow: none; }

  .ribbon { break-inside: avoid; margin: 16px 0;
            -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }

  /* --- Breathing room between sections for natural page flow --- */
  .section + .memory, .section + .viz, .section + .scene,
  .section + .wisdom, .section + .compare-table,
  .section + .ribbon, .section + .reflect, .section + .prompt,
  .section + .dad-voice, .section + .root-ck {
    margin-top: 20px;
  }

  /* --- Decorative page-break transition borders --- */
  .memory, .viz, .scene, .wisdom, .dad-voice, .compare-table,
  .prompt, .reflect, .adventure, .insight, .mission, .gear,
  .think, .taste-recipe, .root-ck, .id-card, .ba-pair {
    border-bottom: 2px solid rgba(123,79,191,0.08);
    padding-bottom: 18px;
    margin-bottom: 18px;
  }

  /* --- Prose: orphans/widows control --- */
  .prose p { orphans: 3; widows: 3; }

  /* --- Links: no underline in print --- */
  a { text-decoration: none !important; }
}
</style>
"""

    pdf_trigger = """
<script>
(function(){
  if(location.search.indexOf('pdf=1') === -1) return;
  /* Hide injected overlays immediately */
  document.querySelectorAll('.pb-back,.chain-panel,.email-slidein,.rating-popup,.tts-fab').forEach(function(el){el.style.display='none'});
  /* Wait for fonts & images, then trigger print */
  window.addEventListener('load', function(){
    setTimeout(function(){ window.print(); }, 600);
  });
})();
</script>
"""

    tts_controls = """
<style>
.tts-fab{position:fixed;top:16px;right:16px;z-index:9999;display:flex;align-items:center;gap:0;
  background:rgba(10,6,20,0.75);backdrop-filter:blur(8px);
  border:1px solid rgba(255,255,255,0.1);border-radius:50px;
  font-family:'Poppins',Helvetica,sans-serif;font-size:0.7rem;font-weight:600;color:rgba(255,255,255,0.7);
  cursor:pointer;transition:all 0.25s;box-shadow:0 2px 12px rgba(0,0,0,0.3);overflow:hidden}
.tts-fab:hover{background:rgba(10,6,20,0.9);color:#E8C96A;border-color:rgba(212,168,67,0.3)}
.tts-fab.playing{border-color:rgba(232,201,106,0.4);color:#E8C96A}
.tts-fab.playing .tts-pulse{animation:tts-glow 1.5s ease-in-out infinite}
@keyframes tts-glow{0%,100%{box-shadow:0 2px 12px rgba(0,0,0,0.3)}50%{box-shadow:0 2px 12px rgba(232,201,106,0.5)}}
.tts-btn{display:flex;align-items:center;justify-content:center;padding:8px 12px;background:none;border:none;
  color:inherit;cursor:pointer;font-family:inherit;font-size:inherit;font-weight:inherit}
.tts-btn svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.tts-btn.active{color:#E8C96A}
.tts-divider{width:1px;height:20px;background:rgba(255,255,255,0.15)}
.tts-speed{padding:4px 10px;font-size:0.6rem;letter-spacing:1px;white-space:nowrap}
.tts-progress{position:fixed;top:0;left:0;height:2px;background:linear-gradient(90deg,#7b4fbf,#E8C96A);
  z-index:10000;transition:width 0.3s;pointer-events:none}
@media print{.tts-fab,.tts-progress{display:none}}
@media(max-width:600px){.tts-fab{top:auto;bottom:16px;right:16px}}
</style>
<div class="tts-progress" id="tts-progress" style="width:0"></div>
<div class="tts-fab" id="tts-fab">
  <button class="tts-btn" id="tts-play" title="Listen to playbook">
    <svg id="tts-icon-play" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
    <svg id="tts-icon-pause" viewBox="0 0 24 24" style="display:none"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
  </button>
  <div class="tts-divider"></div>
  <button class="tts-btn" id="tts-stop" title="Stop">
    <svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="1"/></svg>
  </button>
  <div class="tts-divider"></div>
  <button class="tts-btn" id="tts-skip" title="Skip forward">
    <svg viewBox="0 0 24 24"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
  </button>
  <div class="tts-divider"></div>
  <button class="tts-btn tts-speed" id="tts-rate">1x</button>
</div>
<script>
(function(){
  if(!window.speechSynthesis) { document.getElementById('tts-fab').style.display='none'; return; }
  var synth = window.speechSynthesis;
  var fab = document.getElementById('tts-fab');
  var playBtn = document.getElementById('tts-play');
  var stopBtn = document.getElementById('tts-stop');
  var skipBtn = document.getElementById('tts-skip');
  var rateBtn = document.getElementById('tts-rate');
  var iconPlay = document.getElementById('tts-icon-play');
  var iconPause = document.getElementById('tts-icon-pause');
  var progressBar = document.getElementById('tts-progress');

  var chunks = [];
  var currentIdx = 0;
  var rate = 1.0;
  var rates = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0];
  var rateIdx = 1;
  var isPlaying = false;
  var isPaused = false;
  var preferredVoice = null;

  /* Collect text chunks from playbook content */
  function collectChunks() {
    chunks = [];
    var selectors = '.page, .section, .prose, .scene, .think, .viz-body, .prompt-body, .memory, .wisdom, .reflect, .adventure, .insight, .mission, .gear, .root-ck, .cover-content';
    var sections = document.querySelectorAll(selectors);
    if (sections.length === 0) sections = document.querySelectorAll('body');
    sections.forEach(function(sec) {
      var els = sec.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, blockquote, .ribbon, .gq, .grand-quote, figcaption, dt, dd');
      els.forEach(function(el) {
        var text = el.textContent.trim();
        if (text.length > 2 && !text.startsWith('KingdomBuilders')) {
          chunks.push({ text: text, el: el });
        }
      });
    });
    /* Deduplicate by removing chunks whose text is identical to the previous */
    var deduped = [];
    var seen = {};
    chunks.forEach(function(c) {
      if (!seen[c.text]) { deduped.push(c); seen[c.text] = true; }
    });
    chunks = deduped;
  }

  /* Pick a good English voice */
  function pickVoice() {
    var voices = synth.getVoices();
    /* Prefer natural/enhanced voices */
    var pref = voices.filter(function(v) { return v.lang.startsWith('en') && /natural|enhanced|premium/i.test(v.name); });
    if (pref.length > 0) { preferredVoice = pref[0]; return; }
    /* Fallback to any English voice */
    var en = voices.filter(function(v) { return v.lang.startsWith('en'); });
    if (en.length > 0) preferredVoice = en[0];
  }
  synth.addEventListener('voiceschanged', pickVoice);
  pickVoice();

  function updateProgress() {
    if (chunks.length === 0) { progressBar.style.width = '0'; return; }
    var pct = Math.round((currentIdx / chunks.length) * 100);
    progressBar.style.width = pct + '%';
  }

  function highlightChunk(idx) {
    /* Remove previous highlight */
    var prev = document.querySelector('.tts-active');
    if (prev) { prev.style.outline = ''; prev.classList.remove('tts-active'); }
    if (idx < chunks.length && chunks[idx].el) {
      var el = chunks[idx].el;
      el.classList.add('tts-active');
      el.style.outline = '2px solid rgba(232,201,106,0.4)';
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function speakChunk(idx) {
    if (idx >= chunks.length) { stopAll(); return; }
    currentIdx = idx;
    updateProgress();
    highlightChunk(idx);

    var utt = new SpeechSynthesisUtterance(chunks[idx].text);
    utt.rate = rate;
    if (preferredVoice) utt.voice = preferredVoice;
    utt.onend = function() {
      if (isPlaying && !isPaused) speakChunk(idx + 1);
    };
    utt.onerror = function(e) {
      if (e.error !== 'canceled' && isPlaying) speakChunk(idx + 1);
    };
    synth.speak(utt);
  }

  function startPlaying() {
    if (chunks.length === 0) collectChunks();
    if (chunks.length === 0) return;
    isPlaying = true; isPaused = false;
    fab.classList.add('playing');
    iconPlay.style.display = 'none';
    iconPause.style.display = '';
    speakChunk(currentIdx);
  }

  function pausePlaying() {
    isPaused = true;
    synth.pause();
    fab.classList.remove('playing');
    iconPlay.style.display = '';
    iconPause.style.display = 'none';
  }

  function resumePlaying() {
    isPaused = false;
    fab.classList.add('playing');
    iconPlay.style.display = 'none';
    iconPause.style.display = '';
    synth.resume();
  }

  function stopAll() {
    isPlaying = false; isPaused = false;
    synth.cancel();
    currentIdx = 0;
    fab.classList.remove('playing');
    iconPlay.style.display = '';
    iconPause.style.display = 'none';
    updateProgress();
    highlightChunk(-1);
  }

  playBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    if (!isPlaying) { startPlaying(); }
    else if (isPaused) { resumePlaying(); }
    else { pausePlaying(); }
  });

  stopBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    stopAll();
  });

  skipBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    if (!isPlaying) return;
    synth.cancel();
    currentIdx = Math.min(currentIdx + 1, chunks.length);
    speakChunk(currentIdx);
  });

  rateBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    rateIdx = (rateIdx + 1) % rates.length;
    rate = rates[rateIdx];
    rateBtn.textContent = rate + 'x';
    /* Restart current chunk at new speed if playing */
    if (isPlaying && !isPaused) {
      synth.cancel();
      speakChunk(currentIdx);
    }
  });

  /* Chrome workaround: synth stops after ~15s, keep-alive */
  setInterval(function() {
    if (synth.speaking && !synth.paused) { synth.pause(); synth.resume(); }
  }, 10000);
})();
</script>
"""

    return html.replace("</body>", back_button + chain_panel + email_slidein + rating_popup + tts_controls + print_css + pdf_trigger + tracking_script + ga_snippet + "</body>")


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
            buy_mode = request.query_params.get("buy") == "1"
            # Serve the landing/sales page if one exists (unless ?buy=1 → go to purchase gate)
            landing_file = STATIC_DIR / f"{slug}.html"
            if landing_file.is_file() and not buy_mode:
                return FileResponse(landing_file)
            # Fallback to generic purchase gate
            return templates.TemplateResponse(
                "purchase_gate.html",
                {
                    "request": request,
                    "slug": slug,
                    "title": _slug_to_title(slug),
                    "error": request.query_params.get("error"),
                    "prefix": prefix,
                    "logged_in": user_id is not None,
                    "ga_id": settings.GA_MEASUREMENT_ID,
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
# PDF download — /read/{slug}/pdf
# ============================================================================
@router.get("/read/{slug}/pdf", include_in_schema=False)
async def download_pdf(request: Request, slug: str, format: str = "standard", db: AsyncSession = Depends(get_db)):
    filename = SLUG_TO_FILE.get(slug)
    if not filename:
        raise HTTPException(status_code=404, detail="Playbook not found")

    # Purchase gate for PDFs too
    if slug not in FREE_SLUGS:
        admin_unlocked = request.cookies.get("admin_unlocked") == "1"
        user_id = get_session_user_id(request)
        db_access = False
        if user_id:
            db_access = await _user_has_access(user_id, slug, db)
        if not admin_unlocked and not db_access:
            raise HTTPException(status_code=403, detail="Purchase required")

    stem = Path(filename).stem
    if format == "bookcut":
        pdf_path = ASSETS_DIR / "pdf-bookcut" / f"{stem}_bookcut.pdf"
    else:
        pdf_path = ASSETS_DIR / "pdf" / f"{stem}.pdf"

    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="PDF not yet generated")

    download_name = f"{stem.replace('_', '-')}-KingdomBuildersAI.pdf"
    if format == "bookcut":
        download_name = f"{stem.replace('_', '-')}-BookCut-KingdomBuildersAI.pdf"

    return FileResponse(
        path=pdf_path,
        filename=download_name,
        media_type="application/pdf",
    )


# ============================================================================
# Admin unlock — /read/{slug}/unlock
# ============================================================================
@router.post("/read/{slug}/unlock", include_in_schema=False)
async def unlock_playbook(request: Request, slug: str, code: str = Form("")):
    prefix = settings.URL_PREFIX or ""
    if code.strip() == ADMIN_CODE:
        response = HTMLResponse(content="", status_code=200)
        response.set_cookie("admin_unlocked", "1", max_age=86400, httponly=True, samesite="lax")
        return _redirect_with_cookie(f"{prefix}/read/{slug}", response)
    return _redirect_with_cookie(f"{prefix}/read/{slug}?buy=1&error=1")


# ============================================================================
# Authentication — server-rendered sign in / sign up
# ============================================================================

@router.get("/auth/status", include_in_schema=False)
async def auth_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Lightweight check: is the user signed in via session cookie?"""
    user_id = get_session_user_id(request)
    if not user_id:
        return JSONResponse({"signed_in": False, "is_admin": False})
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return JSONResponse({
        "signed_in": user is not None,
        "is_admin": user is not None and user.role == "admin",
    })


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
            "google_client_id": settings.GOOGLE_CLIENT_ID,
            "ga_id": settings.GA_MEASUREMENT_ID,
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

    # Referral attribution + code generation
    try:
        await ensure_referral_code(user.id, db)
        ref_code = request.cookies.get("ref")
        if ref_code:
            await process_referral_cookie(user.id, ref_code, db)
    except Exception as e:
        print(f"Referral processing failed (non-critical): {e}")

    response = HTMLResponse(content="", status_code=200)
    set_session_cookie(response, str(user.id))
    if request.cookies.get("ref"):
        response.delete_cookie("ref")
    return _redirect_with_cookie(next_url, response)


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

    response = HTMLResponse(content="", status_code=200)
    set_session_cookie(response, str(user.id))
    return _redirect_with_cookie(next_url, response)


@router.post("/auth/google", include_in_schema=False)
async def auth_google(
    request: Request,
    db: AsyncSession = Depends(get_db),
    credential: str = Form(""),
    next: str = Form(""),
):
    """Handle Google Sign-In callback (client-side GSI flow)."""
    prefix = settings.URL_PREFIX or ""
    next_url = next or f"{prefix}/"

    if not credential:
        return RedirectResponse(
            url=f"{prefix}/auth?error=Google+sign+in+failed&next={quote(next_url)}",
            status_code=303,
        )

    # Verify the id_token with Google
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": credential},
        )

    if resp.status_code != 200:
        return RedirectResponse(
            url=f"{prefix}/auth?error=Invalid+Google+token&next={quote(next_url)}",
            status_code=303,
        )

    token_info = resp.json()
    google_id = token_info.get("sub")
    email = token_info.get("email")
    name = token_info.get("name", "")
    picture = token_info.get("picture", "")

    if not google_id or not email:
        return RedirectResponse(
            url=f"{prefix}/auth?error=Could+not+read+Google+account&next={quote(next_url)}",
            status_code=303,
        )

    # Verify audience matches our client ID
    if settings.GOOGLE_CLIENT_ID and token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
        return RedirectResponse(
            url=f"{prefix}/auth?error=Google+token+mismatch&next={quote(next_url)}",
            status_code=303,
        )

    # Check if this Google account is already linked
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == "google",
            OAuthAccount.provider_id == google_id,
        )
    )
    oauth_account = result.scalar_one_or_none()

    if oauth_account is not None:
        user_result = await db.execute(
            select(User).where(User.id == oauth_account.user_id)
        )
        user = user_result.scalar_one()
        is_new_user = False
    else:
        # Check if a user with this email already exists
        user_result = await db.execute(
            select(User).where(User.email == email)
        )
        user = user_result.scalar_one_or_none()

        is_new_user = user is None
        if user is None:
            user = User(
                email=email,
                display_name=name,
                avatar_url=picture,
                email_verified=True,
            )
            db.add(user)
            await db.flush()

        # Link the OAuth account
        oauth_link = OAuthAccount(
            user_id=user.id,
            provider="google",
            provider_id=google_id,
        )
        db.add(oauth_link)
        await db.flush()

    if not user.email_verified:
        user.email_verified = True
        await db.flush()

    await db.commit()

    # Referral attribution for new users + ensure code for all
    try:
        await ensure_referral_code(user.id, db)
        if is_new_user:
            ref_code = request.cookies.get("ref")
            if ref_code:
                await process_referral_cookie(user.id, ref_code, db)
    except Exception as e:
        print(f"Referral processing failed (non-critical): {e}")

    response = HTMLResponse(content="", status_code=200)
    set_session_cookie(response, str(user.id))
    if is_new_user and request.cookies.get("ref"):
        response.delete_cookie("ref")
    return _redirect_with_cookie(next_url, response)


@router.post("/auth/logout", include_in_schema=False)
async def auth_logout():
    response = JSONResponse({"detail": "Logged out"})
    clear_session_cookie(response)
    response.delete_cookie("admin_unlocked")
    return response


# ============================================================================
# Referral link and dashboard
# ============================================================================
@router.get("/r/{code}", include_in_schema=False)
async def referral_redirect(code: str, db: AsyncSession = Depends(get_db)):
    """Set referral cookie and redirect to funnel.

    Only sets the cookie if the referral code actually exists in the DB,
    preventing poisoning with bogus codes that block legitimate attribution.
    """
    import re
    prefix = settings.URL_PREFIX or ""
    redirect_url = f"{prefix}/funnel"

    # Validate format and existence before setting cookie
    clean_code = code.strip().upper()
    if re.match(r"^[A-Z0-9]{6}$", clean_code):
        from api.models.referral import ReferralCode
        result = await db.execute(
            select(ReferralCode.id).where(ReferralCode.code == clean_code)
        )
        if result.scalar_one_or_none() is not None:
            response = HTMLResponse(content="", status_code=200)
            response.set_cookie(
                "ref", clean_code, max_age=30 * 24 * 3600,
                httponly=True, samesite="lax",
            )
            return _redirect_with_cookie(redirect_url, response)

    return _redirect_with_cookie(redirect_url)


@router.get("/referrals", include_in_schema=False)
async def referrals_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Serve the referral dashboard page."""
    prefix = settings.URL_PREFIX or ""
    user_id = get_session_user_id(request)
    if not user_id:
        return RedirectResponse(
            url=f"{prefix}/auth?next={quote(prefix + '/referrals')}",
            status_code=303,
        )
    return templates.TemplateResponse("referrals.html", {
        "request": request,
        "prefix": prefix,
        "config": settings,
    })


@router.get("/referrals/confirm-claim", include_in_schema=False)
async def confirm_claim_page(request: Request, token: str = "", db: AsyncSession = Depends(get_db)):
    """Handle the confirmation link clicked from the referrer's email.

    Security: requires the referrer to be logged in so a stolen/guessed
    token cannot be used by an unauthenticated attacker to hijack the
    referral tree.
    """
    from api.services.referral_service import confirm_referral_claim
    from api.models.referral import ReferralClaim

    prefix = settings.URL_PREFIX or ""

    # Must be logged in
    user_id = get_session_user_id(request)
    if not user_id:
        # Redirect to login, then back here
        return_url = f"{prefix}/referrals/confirm-claim?token={quote(token)}"
        return RedirectResponse(
            url=f"{prefix}/auth?next={quote(return_url)}",
            status_code=303,
        )

    if not token:
        return templates.TemplateResponse("claim_result.html", {
            "request": request,
            "prefix": prefix,
            "status": "invalid",
            "config": settings,
        })

    # Verify the logged-in user is actually the referrer on this claim
    claim_result = await db.execute(
        select(ReferralClaim).where(ReferralClaim.token == token)
    )
    claim = claim_result.scalar_one_or_none()
    if claim and str(claim.referrer_id) != str(user_id):
        return templates.TemplateResponse("claim_result.html", {
            "request": request,
            "prefix": prefix,
            "status": "invalid",
            "config": settings,
        })

    result = await confirm_referral_claim(token, db)

    return templates.TemplateResponse("claim_result.html", {
        "request": request,
        "prefix": prefix,
        "status": result,
        "config": settings,
    })


# ============================================================================
# Admin Management — /admin/manage
# ============================================================================
@router.get("/admin/manage", include_in_schema=False)
async def admin_manage_page(request: Request, db: AsyncSession = Depends(get_db)):
    prefix = settings.URL_PREFIX or ""
    user_id = get_session_user_id(request)
    if not user_id:
        return RedirectResponse(url=f"{prefix}/", status_code=303)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.role != "admin":
        return RedirectResponse(url=f"{prefix}/", status_code=303)
    return templates.TemplateResponse("admin_manage.html", {
        "request": request,
        "prefix": prefix,
    })


# ============================================================================
# Forgot / Reset Password — server-rendered flow
# ============================================================================
@router.get("/auth/forgot-password", include_in_schema=False)
async def forgot_password_page(request: Request):
    prefix = settings.URL_PREFIX or ""
    return templates.TemplateResponse(
        "forgot_password.html",
        {"request": request, "prefix": prefix, "error": None, "success": None, "ga_id": settings.GA_MEASUREMENT_ID},
    )


@router.post("/auth/forgot-password", include_in_schema=False)
async def forgot_password_submit(
    request: Request,
    db: AsyncSession = Depends(get_db),
    email: str = Form(""),
):
    import resend
    prefix = settings.URL_PREFIX or ""
    email = email.strip().lower()

    # Always show success to prevent email enumeration
    success_msg = "If an account with that email exists, we've sent a reset link. Check your inbox."

    if not email:
        return templates.TemplateResponse(
            "forgot_password.html",
            {"request": request, "prefix": prefix, "error": "Please enter your email.", "success": None, "ga_id": settings.GA_MEASUREMENT_ID},
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is not None:
        # Generate reset token
        raw_token = generate_token()
        token_hash_val = hash_token(raw_token)

        vtoken = VerificationToken(
            user_id=user.id,
            token_hash=token_hash_val,
            token_type="password_reset",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(vtoken)
        await db.commit()

        # Send reset email via Resend
        base = settings.BASE_URL.rstrip("/")
        reset_url = f"{base}{prefix}/auth/reset-password?token={raw_token}"

        try:
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": "Kingdom Builders AI <playbook@kingdombuilders.ai>",
                "to": [email],
                "subject": "Reset Your Password",
                "html": (
                    f'<div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:40px 24px">'
                    f'<h2 style="color:#1A0A2E;margin-bottom:16px">Reset Your Password</h2>'
                    f'<p style="color:#444;line-height:1.6;margin-bottom:24px">'
                    f'Someone requested a password reset for your Kingdom Builders account. '
                    f'Click the button below to set a new password. This link expires in 1 hour.</p>'
                    f'<a href="{reset_url}" style="display:inline-block;padding:14px 32px;'
                    f'background:linear-gradient(135deg,#D4A843,#E8C96A);color:#1A0A2E;'
                    f'text-decoration:none;border-radius:8px;font-weight:600;font-size:15px">'
                    f'Reset Password</a>'
                    f'<p style="color:#999;font-size:13px;margin-top:24px;line-height:1.5">'
                    f'If you didn\'t request this, you can safely ignore this email.</p></div>'
                ),
            })
        except Exception:
            pass  # Don't leak errors — user still sees success message

    return templates.TemplateResponse(
        "forgot_password.html",
        {"request": request, "prefix": prefix, "error": None, "success": success_msg, "ga_id": settings.GA_MEASUREMENT_ID},
    )


@router.get("/auth/reset-password", include_in_schema=False)
async def reset_password_page(request: Request):
    prefix = settings.URL_PREFIX or ""
    token = request.query_params.get("token", "")
    if not token:
        return RedirectResponse(
            url=f"{prefix}/auth/forgot-password", status_code=303
        )
    return templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "prefix": prefix, "token": token, "error": None, "ga_id": settings.GA_MEASUREMENT_ID},
    )


@router.post("/auth/reset-password", include_in_schema=False)
async def reset_password_submit(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str = Form(""),
    password: str = Form(""),
    password_confirm: str = Form(""),
):
    prefix = settings.URL_PREFIX or ""

    if not token:
        return RedirectResponse(
            url=f"{prefix}/auth/forgot-password", status_code=303
        )

    if len(password) < 8:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "prefix": prefix, "token": token, "error": "Password must be at least 8 characters.", "ga_id": settings.GA_MEASUREMENT_ID},
        )

    if password != password_confirm:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "prefix": prefix, "token": token, "error": "Passwords do not match.", "ga_id": settings.GA_MEASUREMENT_ID},
        )

    token_hash_val = hash_token(token)
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token_hash == token_hash_val,
            VerificationToken.token_type == "password_reset",
            VerificationToken.used_at == None,  # noqa: E711
            VerificationToken.expires_at > datetime.now(timezone.utc),
        )
    )
    vtoken = result.scalar_one_or_none()

    if vtoken is None:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "prefix": prefix, "token": token, "error": "This reset link is invalid or has expired. Please request a new one.", "ga_id": settings.GA_MEASUREMENT_ID},
        )

    vtoken.used_at = datetime.now(timezone.utc)

    user_result = await db.execute(select(User).where(User.id == vtoken.user_id))
    user = user_result.scalar_one()
    user.password_hash = hash_password(password)
    await db.commit()

    # Log the user in and redirect
    next_url = f"{prefix}/"
    response = RedirectResponse(
        url=f"{prefix}/auth?error=Password+reset+successfully.+Please+sign+in.", status_code=303
    )
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

    # Check single playbook purchase by playbook_id (via slug → playbook lookup)
    from api.models.playbook import Playbook
    playbook_result = await db.execute(
        select(Playbook.id).where(Playbook.slug == slug)
    )
    playbook_id = playbook_result.scalar_one_or_none()
    if playbook_id:
        result = await db.execute(
            select(Purchase).where(
                Purchase.user_id == uid,
                Purchase.playbook_id == playbook_id,
                Purchase.status == "completed",
            ).limit(1)
        )
        if result.scalar_one_or_none():
            return True

    # Fallback: check legacy purchases stored with "single:{slug}" in provider_payment_id
    result = await db.execute(
        select(Purchase).where(
            Purchase.user_id == uid,
            Purchase.provider_payment_id == f"single:{slug}",
            Purchase.status == "completed",
        ).limit(1)
    )
    if result.scalar_one_or_none():
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
async def api_hot(period: str = "all", db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Playbook.slug, Playbook.view_count)
        .where(Playbook.status == "published")
        .order_by(Playbook.view_count.desc())
        .limit(3)
    )
    hot = [{"slug": row.slug, "views": row.view_count} for row in result]
    return JSONResponse(hot)


@router.post("/api/track/view", include_in_schema=False)
async def track_view(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    slug = data.get("slug", "").strip()
    if not slug:
        return JSONResponse({"error": "slug required"}, status_code=400)
    result = await db.execute(select(Playbook).where(Playbook.slug == slug))
    pb = result.scalar_one_or_none()
    if pb:
        pb.view_count = (pb.view_count or 0) + 1
        await db.commit()
    return JSONResponse({"ok": True})


@router.post("/api/track/exit", include_in_schema=False)
async def track_exit(request: Request, db: AsyncSession = Depends(get_db)):
    """Save reading progress (scroll_percent, last_chapter) for logged-in users."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": True})

    slug = data.get("slug", "").strip()
    if not slug:
        return JSONResponse({"ok": True})

    user_id = get_session_user_id(request)
    if not user_id:
        return JSONResponse({"ok": True})

    scroll_pct = data.get("scroll_percent", 0)
    last_chapter = data.get("last_chapter")

    result = await db.execute(select(Playbook).where(Playbook.slug == slug))
    pb = result.scalar_one_or_none()
    if not pb:
        return JSONResponse({"ok": True})

    rp_result = await db.execute(
        select(ReadingProgress)
        .where(ReadingProgress.user_id == user_id)
        .where(ReadingProgress.playbook_id == pb.id)
    )
    rp = rp_result.scalar_one_or_none()

    if rp:
        rp.scroll_percent = max(rp.scroll_percent, float(scroll_pct))
        if last_chapter:
            rp.last_chapter = last_chapter
        if scroll_pct >= 90:
            rp.completed = True
    else:
        rp = ReadingProgress(
            user_id=user_id,
            playbook_id=pb.id,
            scroll_percent=float(scroll_pct),
            last_chapter=last_chapter,
            completed=scroll_pct >= 90,
        )
        db.add(rp)

    await db.commit()
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

    # Rate limit checkout attempts
    client_ip = request.client.host if request.client else "unknown"
    if _is_checkout_rate_limited(client_ip):
        return JSONResponse({"error": "Too many checkout attempts. Please wait a minute."}, status_code=429)

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

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(obj, db)
        elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
            await _handle_subscription_updated(obj, db)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(obj, db)
        elif event_type == "invoice.paid":
            # Subscription renewal — process referral commissions
            sub_id = obj.get("subscription")
            if sub_id:
                try:
                    result = await db.execute(
                        select(Subscription).where(
                            Subscription.provider_subscription_id == sub_id
                        )
                    )
                    sub = result.scalar_one_or_none()
                    if sub and sub.status == "active":
                        billing_month = datetime.now(timezone.utc).strftime("%Y-%m")
                        await process_commissions(
                            referred_user_id=sub.user_id,
                            billing_period=billing_month,
                            db=db,
                            subscription_id=sub.id,
                            plan_type=sub.plan_type,
                        )
                except Exception as e:
                    print(f"Invoice commission processing failed (non-critical): {e}")
        elif event_type == "charge.refunded":
            # Mark matching purchase as refunded
            payment_intent_id = obj.get("payment_intent")
            if payment_intent_id:
                result = await db.execute(
                    select(Purchase).where(
                        Purchase.provider_payment_id.contains(payment_intent_id)
                    )
                )
                for p in result.scalars().all():
                    p.status = "refunded"
                # Also check by provider_session_id → payment_intent mapping
                result2 = await db.execute(
                    select(Purchase).where(
                        Purchase.provider_payment_id == f"single:{payment_intent_id}"
                    )
                )
                for p in result2.scalars().all():
                    p.status = "refunded"
                await db.commit()
                # Handle referral commission refunds
                try:
                    billing_period = f"one-time:{payment_intent_id}"
                    await handle_refund_commissions(
                        purchase_id=None,
                        subscription_id=None,
                        billing_period=billing_period,
                        db=db,
                    )
                except Exception as e:
                    print(f"Refund commission handling failed (non-critical): {e}")
    except Exception as e:
        print(f"Stripe webhook handler error for {event_type}: {e}")

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
        # Look up playbook_id from slug
        from api.models.playbook import Playbook as _Playbook
        pb_result = await db.execute(
            select(_Playbook.id).where(_Playbook.slug == slug)
        )
        pb_id = pb_result.scalar_one_or_none()
        # Create Purchase record in PostgreSQL
        purchase = Purchase(
            user_id=uid,
            playbook_id=pb_id,
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

    # Process referral commissions
    try:
        if mode == "single":
            await process_commissions(
                referred_user_id=uid,
                billing_period=f"one-time:{session_id}",
                db=db,
                purchase_id=purchase.id if mode == "single" else None,
                plan_type="single",
            )
        elif mode in ("monthly", "yearly"):
            billing_month = datetime.now(timezone.utc).strftime("%Y-%m")
            await process_commissions(
                referred_user_id=uid,
                billing_period=billing_month,
                db=db,
                plan_type=mode,
            )
    except Exception as e:
        print(f"Commission processing failed (non-critical): {e}")

    # Send delivery email with playbook details (in background thread
    # so we don't block the event loop and cause Stripe webhook timeouts)
    try:
        import asyncio as _aio
        from api.services.email_service import send_delivery_email
        slug = metadata.get("slug", "")
        # Look up playbook title
        from api.models.playbook import Playbook as _PB
        pb_result = await db.execute(select(_PB.title).where(_PB.slug == slug))
        pb_title = pb_result.scalar_one_or_none() or _slug_to_title(slug)
        _aio.get_running_loop().run_in_executor(
            None, send_delivery_email, customer_email, "", pb_title, slug
        )
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
        # Cancel pending referral commissions
        try:
            await cancel_pending_commissions(sub.user_id, db)
        except Exception as e:
            print(f"Commission cancellation failed (non-critical): {e}")
        await db.commit()


# ============================================================================
# Success page
# ============================================================================
@router.get("/success", include_in_schema=False)
async def success_page(
    request: Request,
    session_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    prefix = settings.URL_PREFIX or ""
    if not session_id:
        return RedirectResponse(url=f"{prefix}/", status_code=303)

    # Try to retrieve the Stripe session to get metadata
    stripe.api_key = settings.STRIPE_SECRET_KEY
    slug = ""
    mode = "single"
    email = ""
    try:
        stripe_session = stripe.checkout.Session.retrieve(session_id)
        metadata = stripe_session.get("metadata", {})
        slug = metadata.get("slug", "") or metadata.get("playbook_slug", "")
        mode = metadata.get("mode", "single")
        # Get email from Stripe customer_details (always available after checkout)
        customer_details = stripe_session.get("customer_details", {})
        email = (customer_details or {}).get("email", "")
    except Exception:
        pass

    # Look up purchase in PostgreSQL database
    purchase_confirmed = False
    download_token = ""
    result = await db.execute(
        select(Purchase).where(Purchase.provider_session_id == session_id)
    )
    purchase = result.scalar_one_or_none()
    if purchase:
        purchase_confirmed = True
        download_token = purchase.download_token or ""
        # If we didn't get email from Stripe, try from the user record
        if not email and purchase.user_id:
            user_result = await db.execute(
                select(User).where(User.id == purchase.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                email = user.email or ""

    # For subscriptions, also check the subscription table
    if not purchase_confirmed and mode in ("monthly", "yearly"):
        # Subscription checkouts don't create Purchase records;
        # check if a Subscription was created via the webhook
        sub_result = await db.execute(
            select(Subscription).where(
                Subscription.status == "active"
            ).order_by(Subscription.created_at.desc()).limit(1)
        )
        sub = sub_result.scalar_one_or_none()
        if sub:
            purchase_confirmed = True

    response = templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "download_token": download_token,
            "email": email,
            "base_url": settings.BASE_URL,
            "slug": slug,
            "prefix": prefix,
            "purchase_confirmed": purchase_confirmed,
            "session_id": session_id,
            "ga_id": settings.GA_MEASUREMENT_ID,
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
@router.get("/journey", include_in_schema=False)
async def journey_page(request: Request):
    prefix = settings.URL_PREFIX or ""
    return templates.TemplateResponse(
        "journey.html",
        {"request": request, "prefix": prefix, "ga_id": settings.GA_MEASUREMENT_ID},
    )


@router.get("/constellation", include_in_schema=False)
async def constellation_page(request: Request):
    prefix = settings.URL_PREFIX or ""
    return templates.TemplateResponse(
        "constellation.html",
        {"request": request, "prefix": prefix, "ga_id": settings.GA_MEASUREMENT_ID},
    )


@router.get("/paths", include_in_schema=False)
async def paths_page(request: Request):
    prefix = settings.URL_PREFIX or ""
    return templates.TemplateResponse(
        "paths.html",
        {"request": request, "prefix": prefix, "ga_id": settings.GA_MEASUREMENT_ID},
    )


@router.get("/my-playbooks", include_in_schema=False)
async def my_playbooks_page(request: Request):
    prefix = settings.URL_PREFIX or ""
    return templates.TemplateResponse(
        "my_playbooks.html",
        {"request": request, "prefix": prefix, "ga_id": settings.GA_MEASUREMENT_ID},
    )


@router.post("/manage-subscription", include_in_schema=False)
async def manage_subscription(request: Request, db: AsyncSession = Depends(get_db)):
    """Redirect subscriber to Stripe Customer Portal to manage/cancel subscription."""
    prefix = settings.URL_PREFIX or ""
    user_id = get_session_user_id(request)
    if not user_id:
        return RedirectResponse(url=f"{prefix}/auth?next={prefix}/my-playbooks", status_code=303)

    # Find Stripe customer ID
    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.user_id == user_id)
    )
    sc = result.scalar_one_or_none()
    if not sc:
        return RedirectResponse(url=f"{prefix}/my-playbooks", status_code=303)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        portal = stripe.billing_portal.Session.create(
            customer=sc.stripe_customer_id,
            return_url=f"{settings.BASE_URL}/my-playbooks",
        )
        return RedirectResponse(url=portal.url, status_code=303)
    except Exception as e:
        print(f"Stripe portal error: {e}")
        return RedirectResponse(url=f"{prefix}/my-playbooks", status_code=303)


@router.get("/funnel", include_in_schema=False)
async def funnel_page(request: Request):
    prefix = settings.URL_PREFIX or ""
    return templates.TemplateResponse(
        "funnel.html",
        {"request": request, "prefix": prefix, "ga_id": settings.GA_MEASUREMENT_ID},
    )


@router.get("/funnel/thank-you", include_in_schema=False)
async def funnel_thank_you(request: Request):
    prefix = settings.URL_PREFIX or ""
    return templates.TemplateResponse(
        "funnel_thank_you.html",
        {"request": request, "prefix": prefix, "ga_id": settings.GA_MEASUREMENT_ID},
    )


@router.get("/terms", include_in_schema=False)
async def terms(request: Request):
    prefix = settings.URL_PREFIX or ""
    return templates.TemplateResponse(
        "terms.html",
        {"request": request, "prefix": prefix},
    )


@router.get("/privacy", include_in_schema=False)
async def privacy(request: Request):
    prefix = settings.URL_PREFIX or ""
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request, "prefix": prefix},
    )


@router.get("/refund", include_in_schema=False)
async def refund():
    return FileResponse(STATIC_DIR / "refund.html")
