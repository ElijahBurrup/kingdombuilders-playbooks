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
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
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
}


# ============================================================================
# Catalog (index)
# ============================================================================
@router.get("/", include_in_schema=False)
async def catalog():
    return FileResponse(STATIC_DIR / "index.html")


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
# Playbook reader — /read/{slug}
# ============================================================================
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
    return FileResponse(file_path)


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
# Stripe checkout (legacy — form-post flow)
# ============================================================================
@router.post("/create-checkout-session", include_in_schema=False)
async def checkout():
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price": settings.STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            success_url=f"{settings.BASE_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.BASE_URL}/conductorsplaybook?payment=cancelled",
            customer_creation="always",
            metadata={"product": "conductors_playbook"},
        )
        return RedirectResponse(url=session.url, status_code=303)
    except Exception as e:
        print(f"Stripe checkout error: {e}")
        return RedirectResponse(
            url=f"{settings.BASE_URL}/conductorsplaybook?payment=error",
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

    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "download_token": purchase["download_token"],
            "email": purchase["customer_email"],
            "base_url": settings.BASE_URL,
        },
    )


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
