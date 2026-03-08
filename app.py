import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, Blueprint, send_from_directory, redirect, request, render_template, url_for, jsonify

import config
from database import initialize_db

# --- Blueprint for all routes (supports URL_PREFIX) ---
bp = Blueprint("main", __name__)


def get_all_slugs():
    """Return list of all playbook slugs (used by grant_all_playbook_access)."""
    return list(_slug_to_file().keys())


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

    # Read the HTML and inject tracking script before </body>
    file_path = Path(__file__).parent / "assets" / filename
    html = file_path.read_text(encoding="utf-8")
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
    html = html.replace("</body>", tracking_script + "</body>")
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


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
