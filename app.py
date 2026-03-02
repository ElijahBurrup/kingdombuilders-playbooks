import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, Blueprint, send_from_directory, redirect, request, render_template, url_for

import config
from database import initialize_db

# --- Blueprint for all routes (supports URL_PREFIX) ---
bp = Blueprint("main", __name__)


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


# --- Playbook Reader (serves full playbook HTML from assets) ---
@bp.route("/read/<slug>")
def read_playbook(slug):
    slug_to_file = {
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
    }
    filename = slug_to_file.get(slug)
    if not filename:
        return render_template("error.html",
            title="Playbook Not Found",
            message="The playbook you're looking for doesn't exist."
        ), 404
    return send_from_directory("assets", filename)


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
