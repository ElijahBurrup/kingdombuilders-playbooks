import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, Blueprint, send_from_directory, redirect, request, render_template, url_for, jsonify, session

import config
from database import initialize_db

# --- Version & Release Notes ---
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
        "title": "New Playbooks",
        "changes": [
            "Added The Bonsai Method — personal finance through the art of bonsai shaping",
            "Added The Fibonacci Trim — painless spending cuts using nature's ratio",
            "Catalog now features 44 playbooks",
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

# --- Blueprint for all routes (supports URL_PREFIX) ---
bp = Blueprint("main", __name__)


FREE_SLUGS = {
    "lay-it-down",
    "the-narrator",
    "the-crows-gambit",
    "the-salmon-journey",
    "the-wolfs-table",
}

ADMIN_CODE = os.environ.get("ADMIN_UNLOCK_CODE", "elijahsentme")


def get_all_slugs():
    """Return list of all playbook slugs (used by grant_all_playbook_access)."""
    return list(_slug_to_file().keys())


def _slug_to_title(slug):
    """Convert slug to display title."""
    return slug.replace("-", " ").title().replace("S ", "s ").replace("'S", "'s")


def _slug_to_file():
    """Central slug-to-filename mapping."""
    return {
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
        "the-mantis-shrimps-eye": "The_Mantis_Shrimps_Eye.html",
        "the-porcupines-quills": "The_Porcupines_Quills.html",
        "the-tardigrade-protocol": "The_Tardigrade_Protocol.html",
        "the-cuttlefishs-canvas": "The_Cuttlefishs_Canvas.html",
    }


# --- Product Catalog ---
@bp.route("/")
def catalog():
    return send_from_directory("static", "index.html")


# --- Playbook Landing Pages ---
@bp.route("/conductorsplaybook")
def conductors_playbook():
    return send_from_directory("static", "landing.html")


@bp.route("/layitdown")
def lay_it_down():
    return send_from_directory("static", "lay-it-down.html")


@bp.route("/theantnetwork")
def the_ant_network():
    return send_from_directory("static", "the-ant-network.html")


@bp.route("/thecostledger")
def the_cost_ledger():
    return send_from_directory("static", "the-cost-ledger.html")


@bp.route("/theghostframe")
def the_ghost_frame():
    return send_from_directory("static", "the-ghost-frame.html")


@bp.route("/thegravitywell")
def the_gravity_well():
    return send_from_directory("static", "the-gravity-well.html")


@bp.route("/thenarrator")
def the_narrator():
    return send_from_directory("static", "the-narrator.html")


@bp.route("/thesalmonjourney")
def the_salmon_journey():
    return send_from_directory("static", "the-salmon-journey.html")


@bp.route("/thesquirreleconomy")
def the_squirrel_economy():
    return send_from_directory("static", "the-squirrel-economy.html")


@bp.route("/thewolfstable")
def the_wolfs_table():
    return send_from_directory("static", "the-wolfs-table.html")


@bp.route("/thecrowsgambit")
def the_crows_gambit():
    return send_from_directory("static", "the-crows-gambit.html")


@bp.route("/theeagleslens")
def the_eagles_lens():
    return send_from_directory("static", "the-eagles-lens.html")


@bp.route("/thelighthousekeeperslog")
def the_lighthouse_keepers_log():
    return send_from_directory("static", "the-lighthouse-keepers-log.html")


@bp.route("/theoctopusprotocol")
def the_octopus_protocol():
    return send_from_directory("static", "the-octopus-protocol.html")


@bp.route("/thestarlingsmurmuration")
def the_starlings_murmuration():
    return send_from_directory("static", "the-starlings-murmuration.html")


@bp.route("/thechameleonscode")
def the_chameleons_code():
    return send_from_directory("static", "the-chameleons-code.html")


@bp.route("/thespidersloom")
def the_spiders_loom():
    return send_from_directory("static", "the-spiders-loom.html")


@bp.route("/thegeckosgrip")
def the_geckos_grip():
    return send_from_directory("static", "the-geckos-grip.html")


@bp.route("/thefireflyssignal")
def the_fireflys_signal():
    return send_from_directory("static", "the-fireflys-signal.html")


@bp.route("/thefoxstrail")
def the_foxs_trail():
    return send_from_directory("static", "the-foxs-trail.html")


@bp.route("/themothsflame")
def the_moths_flame():
    return send_from_directory("static", "the-moths-flame.html")


@bp.route("/thebearswinter")
def the_bears_winter():
    return send_from_directory("static", "the-bears-winter.html")


@bp.route("/thecoyoteslaugh")
def the_coyotes_laugh():
    return send_from_directory("static", "the-coyotes-laugh.html")


@bp.route("/thepangolinsarmor")
def the_pangolins_armor():
    return send_from_directory("static", "the-pangolins-armor.html")


@bp.route("/thehorsesgait")
def the_horses_gait():
    return send_from_directory("static", "the-horses-gait.html")


@bp.route("/thecompassrose")
def the_compass_rose():
    return send_from_directory("static", "the-compass-rose.html")


# --- Lay It Down Series (7 Deadly Sins) ---
@bp.route("/layitdownpride")
def lay_it_down_pride():
    return send_from_directory("static", "lay-it-down-pride.html")


@bp.route("/layitdownenvy")
def lay_it_down_envy():
    return send_from_directory("static", "lay-it-down-envy.html")


@bp.route("/layitdownwrath")
def lay_it_down_wrath():
    return send_from_directory("static", "lay-it-down-wrath.html")


# --- A Process Model Series ---
@bp.route("/thetidepoolsecho")
def the_tide_pools_echo():
    return send_from_directory("static", "the-tide-pools-echo.html")


@bp.route("/thewhalesbreath")
def the_whales_breath():
    return send_from_directory("static", "the-whales-breath.html")


@bp.route("/thebutterflyscrossing")
def the_butterflys_crossing():
    return send_from_directory("static", "the-butterflys-crossing.html")


@bp.route("/theeleophantsground")
def the_elephants_ground():
    return send_from_directory("static", "the-elephants-ground.html")


@bp.route("/thebeesdance")
def the_bees_dance():
    return send_from_directory("static", "the-bees-dance.html")


@bp.route("/theottersplay")
def the_otters_play():
    return send_from_directory("static", "the-otters-play.html")


@bp.route("/themockingbirdssong")
def the_mockingbirds_song():
    return send_from_directory("static", "the-mockingbirds-song.html")


# --- Dad Talks Series ---
@bp.route("/dadtalksthedopaminedrought")
def dad_talks_the_dopamine_drought():
    return send_from_directory("static", "dad-talks-the-dopamine-drought.html")


@bp.route("/dadtalksthemirrortest")
def dad_talks_the_mirror_test():
    return send_from_directory("static", "dad-talks-the-mirror-test.html")


# --- Additional Playbooks ---
@bp.route("/thearrival")
def the_arrival():
    return send_from_directory("static", "the-arrival.html")


@bp.route("/thebodylie")
def the_body_lie():
    return send_from_directory("static", "the-body-lie.html")


@bp.route("/themyceliumnetwork")
def the_mycelium_network():
    return send_from_directory("static", "the-mycelium-network.html")


@bp.route("/thetermitecathedral")
def the_termite_cathedral():
    return send_from_directory("static", "the-termite-cathedral.html")


@bp.route("/thebonsaimethod")
def the_bonsai_method():
    return send_from_directory("static", "the-bonsai-method.html")


@bp.route("/thefibonaccitrim")
def the_fibonacci_trim():
    return send_from_directory("static", "the-fibonacci-trim.html")


@bp.route("/layitdownsloth")
def lay_it_down_sloth():
    return send_from_directory("static", "lay-it-down-sloth.html")


@bp.route("/layitdowngreed")
def lay_it_down_greed():
    return send_from_directory("static", "lay-it-down-greed.html")

@bp.route("/layitdowngluttony")
def lay_it_down_gluttony():
    return send_from_directory("static", "lay-it-down-gluttony.html")

@bp.route("/layitdownlust")
def lay_it_down_lust():
    return send_from_directory("static", "lay-it-down-lust.html")


# --- Playbook Reader (serves full playbook HTML from assets) ---
@bp.route("/read/<slug>")
def read_playbook(slug):
    slug_to_file = _slug_to_file()
    filename = slug_to_file.get(slug)
    if not filename:
        return render_template("error.html",
            title="Playbook Not Found",
            message="The playbook you're looking for doesn't exist."
        ), 404

    # Check access: free playbooks, admin-unlocked sessions, or per-slug unlocks pass through
    if slug not in FREE_SLUGS:
        unlocked = session.get("admin_unlocked") or slug in session.get("unlocked_slugs", [])
        if not unlocked:
            return render_template("purchase_gate.html",
                slug=slug,
                title=_slug_to_title(slug),
                error=request.args.get("error"),
                prefix=config.URL_PREFIX or ""
            )

    # Read the HTML and inject tracking script before </body>
    file_path = Path(__file__).parent / "assets" / filename
    html = file_path.read_text(encoding="utf-8")
    # Inject back button (fixed position, triggers exit tracking on click)
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
<a class="pb-back" href="{config.URL_PREFIX or ''}/"><svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>Playbooks</a>
"""
    tracking_script = f"""
<script>
(function(){{
  var slug = '{slug}';
  var base = (document.querySelector('base') || {{}}).href || '';
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
    html = html.replace("</body>", back_button + tracking_script + "</body>")
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


# --- Playbook Unlock (admin code) ---
@bp.route("/read/<slug>/unlock", methods=["POST"])
def unlock_playbook(slug):
    code = request.form.get("code", "").strip()
    if code == ADMIN_CODE:
        session["admin_unlocked"] = True
        return redirect(url_for("main.read_playbook", slug=slug))
    return redirect(url_for("main.read_playbook", slug=slug, error="1"))


# --- Analytics Tracking ---
@bp.route("/api/track/view", methods=["POST"])
def track_view():
    data = request.get_json(silent=True) or {}
    slug = data.get("slug", "").strip()
    if not slug:
        return jsonify({"error": "slug required"}), 400
    from database import log_playbook_view
    log_playbook_view(slug, request.remote_addr, request.headers.get("User-Agent"))
    return jsonify({"ok": True})


@bp.route("/api/track/exit", methods=["POST"])
def track_exit():
    data = request.get_json(silent=True) or {}
    slug = data.get("slug", "").strip()
    scroll_percent = data.get("scroll_percent", 0)
    time_spent = data.get("time_spent_secs", 0)
    if not slug:
        return jsonify({"error": "slug required"}), 400
    from database import log_playbook_exit
    log_playbook_exit(slug, scroll_percent, time_spent, request.remote_addr)
    return jsonify({"ok": True})


# --- Admin Dashboard ---
@bp.route("/admin")
def admin_dashboard():
    from database import get_playbook_analytics
    analytics = get_playbook_analytics()
    return render_template("admin.html", analytics=analytics)


# --- Hot Playbooks API ---
@bp.route("/api/hot")
def api_hot():
    """Return top 3 most-read playbooks for a given time range."""
    period = request.args.get("period", "all")  # today, week, month, all
    from database import get_hot_playbooks
    hot = get_hot_playbooks(period, limit=3)
    return jsonify(hot)


# --- Version API ---
@bp.route("/api/version")
def api_version():
    return jsonify({
        "version": APP_VERSION,
        "notes": RELEASE_NOTES[:3],  # Last 3 releases
    })


# --- Health Check (keep-alive for Render free tier) ---
@bp.route("/health")
def health():
    return "ok", 200


# --- Email Capture / Lead Magnet ---
@bp.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip()
    source = request.form.get("source", "salmon-journey-ch1")
    if not email:
        return redirect(url_for("main.catalog"))
    from database import create_subscriber
    create_subscriber(email, source)
    try:
        from emails import send_lead_magnet_email
        send_lead_magnet_email(email)
    except Exception as e:
        print(f"Lead magnet email failed: {e}")
    return redirect(url_for("main.thanks"))


@bp.route("/thanks")
def thanks():
    return send_from_directory("static", "thanks.html")


@bp.route("/free/salmon-journey-ch1")
def free_salmon_ch1():
    return send_from_directory("static", "free-salmon-ch1.html")


# --- Stripe Checkout ---
@bp.route("/create-checkout-session", methods=["POST"])
def checkout():
    from stripe_checkout import create_checkout_session
    return create_checkout_session()


# --- Stripe Webhook ---
@bp.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    from stripe_checkout import handle_webhook
    return handle_webhook()


# --- Success Page ---
@bp.route("/success")
def success():
    session_id = request.args.get("session_id")
    if not session_id:
        return redirect(url_for("main.conductors_playbook"))

    from database import get_purchase_by_session_id
    purchase = get_purchase_by_session_id(session_id)
    if not purchase:
        return render_template("error.html",
            title="Purchase Not Found",
            message="We couldn't find your purchase. Your payment may still be processing — please check your email in a few minutes."
        ), 404

    # Grant session-level access so the user can read immediately
    session["admin_unlocked"] = True

    return render_template("success.html",
        download_token=purchase["download_token"],
        email=purchase["customer_email"],
        base_url=config.BASE_URL
    )


# --- Download ---
@bp.route("/download/<token>")
def download(token):
    from downloads import handle_download
    return handle_download(token)


# --- Legal Pages ---
@bp.route("/terms")
def terms():
    return send_from_directory("static", "terms.html")


@bp.route("/privacy")
def privacy():
    return send_from_directory("static", "privacy.html")


@bp.route("/refund")
def refund():
    return send_from_directory("static", "refund.html")


def create_app():
    static_path = f"{config.URL_PREFIX}/static" if config.URL_PREFIX else "/static"
    flask_app = Flask(__name__, static_folder="static", template_folder="templates",
                      static_url_path=static_path)
    flask_app.secret_key = config.FLASK_SECRET_KEY

    flask_app.register_blueprint(bp, url_prefix=config.URL_PREFIX or None)

    @flask_app.context_processor
    def inject_config():
        return {"config": config}

    @flask_app.after_request
    def rewrite_urls(response):
        if config.URL_PREFIX and response.content_type and "text/html" in response.content_type:
            content = response.get_data(as_text=True)
            content = content.replace('href="/', f'href="{config.URL_PREFIX}/')
            content = content.replace("href='/", f"href='{config.URL_PREFIX}/")
            content = content.replace('src="/', f'src="{config.URL_PREFIX}/')
            content = content.replace("src='/", f"src='{config.URL_PREFIX}/")
            content = content.replace('action="/', f'action="{config.URL_PREFIX}/')
            content = content.replace("action='/", f"action='{config.URL_PREFIX}/")
            response.set_data(content)
        return response

    initialize_db()

    return flask_app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
