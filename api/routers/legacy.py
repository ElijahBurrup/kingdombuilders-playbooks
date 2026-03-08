"""
Legacy backward-compatibility router.

Reproduces every route from the original Flask app.py so existing
URLs (landing pages, reader, checkout, downloads, legal pages) continue
to work without any changes on the client side.
"""

import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import stripe
from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from api.config import settings

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
APP_VERSION = "2.4.0"
RELEASE_NOTES = [
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
    return html.replace("</body>", back_button + tracking_script + "</body>")


@router.get("/read/{slug}", include_in_schema=False)
async def read_playbook(request: Request, slug: str):
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
        unlocked_slugs = request.cookies.get("unlocked_slugs", "").split(",")
        if not admin_unlocked and slug not in unlocked_slugs:
            prefix = settings.URL_PREFIX or ""
            return templates.TemplateResponse(
                "purchase_gate.html",
                {
                    "request": request,
                    "slug": slug,
                    "title": _slug_to_title(slug),
                    "error": request.query_params.get("error"),
                    "prefix": prefix,
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
    mode: str = Form("single"),
    slug: str = Form(""),
):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Pick the right price ID and Stripe mode
    if mode == "monthly":
        price_id = settings.STRIPE_PRICE_MONTHLY
        stripe_mode = "subscription"
        metadata = {"mode": "monthly"}
    elif mode == "yearly":
        price_id = settings.STRIPE_PRICE_YEARLY
        stripe_mode = "subscription"
        metadata = {"mode": "yearly"}
    else:
        price_id = settings.STRIPE_PRICE_SINGLE or settings.STRIPE_PRICE_ID
        stripe_mode = "payment"
        metadata = {"mode": "single", "slug": slug}

    if not price_id:
        return JSONResponse({"error": "Stripe price not configured"}, status_code=500)

    cancel_path = f"/read/{slug}" if slug else "/"
    base = settings.BASE_URL

    try:
        session_params = {
            "mode": stripe_mode,
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": f"{base}/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{base}{cancel_path}?payment=cancelled",
            "metadata": metadata,
        }
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


# ============================================================================
# Stripe webhook (legacy)
# ============================================================================
@router.post("/webhook/stripe", include_in_schema=False)
async def stripe_webhook(request: Request):
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

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        _handle_successful_purchase(session_obj)

    return {"status": "ok"}


def _handle_successful_purchase(session: dict) -> None:
    """Record purchase, generate download token, send delivery email, schedule follow-ups."""
    from database import create_purchase, get_purchase_by_session_id
    from api.services.email_service import send_delivery_email
    from api.services.scheduler_service import schedule_followup_emails

    session_id = session["id"]

    # Idempotency: skip if already processed
    if get_purchase_by_session_id(session_id):
        return

    customer_email = session["customer_details"]["email"]
    download_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    create_purchase(
        stripe_session_id=session_id,
        customer_email=customer_email,
        download_token=download_token,
        downloads_remaining=5,
        expires_at=expires_at,
        stripe_payment_intent=session.get("payment_intent"),
        amount_cents=session.get("amount_total", 6700),
    )

    send_delivery_email(customer_email, download_token)
    schedule_followup_emails(customer_email, download_token)


# ============================================================================
# Success page
# ============================================================================
@router.get("/success", include_in_schema=False)
async def success_page(request: Request, session_id: str | None = None):
    if not session_id:
        return RedirectResponse(url="/conductorsplaybook", status_code=303)

    from database import get_purchase_by_session_id

    purchase = get_purchase_by_session_id(session_id)
    if not purchase:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Purchase Not Found",
                "message": (
                    "We couldn't find your purchase. Your payment may still be "
                    "processing — please check your email in a few minutes."
                ),
            },
            status_code=404,
        )

    response = templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "download_token": purchase["download_token"],
            "email": purchase["customer_email"],
            "base_url": settings.BASE_URL,
        },
    )
    # Unlock all playbooks after successful purchase
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
