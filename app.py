import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, send_from_directory, redirect, request, render_template

import config
from database import initialize_db

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = config.FLASK_SECRET_KEY

# Initialize database on startup
initialize_db()


# --- Product Catalog ---
@app.route("/")
def catalog():
    return send_from_directory("static", "index.html")


# --- Playbook Landing Pages ---
@app.route("/conductorsplaybook")
def conductors_playbook():
    return send_from_directory("static", "landing.html")


@app.route("/layitdown")
def lay_it_down():
    return send_from_directory("static", "lay-it-down.html")


@app.route("/theantnetwork")
def the_ant_network():
    return send_from_directory("static", "the-ant-network.html")


@app.route("/thecostledger")
def the_cost_ledger():
    return send_from_directory("static", "the-cost-ledger.html")


@app.route("/theghostframe")
def the_ghost_frame():
    return send_from_directory("static", "the-ghost-frame.html")


@app.route("/thegravitywell")
def the_gravity_well():
    return send_from_directory("static", "the-gravity-well.html")


@app.route("/thenarrator")
def the_narrator():
    return send_from_directory("static", "the-narrator.html")


@app.route("/thesalmonjourney")
def the_salmon_journey():
    return send_from_directory("static", "the-salmon-journey.html")


@app.route("/thesquirreleconomy")
def the_squirrel_economy():
    return send_from_directory("static", "the-squirrel-economy.html")


@app.route("/thewolfstable")
def the_wolfs_table():
    return send_from_directory("static", "the-wolfs-table.html")


# --- Playbook Reader (serves full playbook HTML from assets) ---
@app.route("/read/<slug>")
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
    }
    filename = slug_to_file.get(slug)
    if not filename:
        return render_template("error.html",
            title="Playbook Not Found",
            message="The playbook you're looking for doesn't exist."
        ), 404
    return send_from_directory("assets", filename)


# --- Email Capture / Lead Magnet ---
@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip()
    source = request.form.get("source", "salmon-journey-ch1")
    if not email:
        return redirect("/")
    from database import create_subscriber
    create_subscriber(email, source)
    try:
        from emails import send_lead_magnet_email
        send_lead_magnet_email(email)
    except Exception as e:
        print(f"Lead magnet email failed: {e}")
    return redirect("/thanks")


@app.route("/thanks")
def thanks():
    return send_from_directory("static", "thanks.html")


@app.route("/free/salmon-journey-ch1")
def free_salmon_ch1():
    return send_from_directory("static", "free-salmon-ch1.html")


# --- Stripe Checkout ---
@app.route("/create-checkout-session", methods=["POST"])
def checkout():
    from stripe_checkout import create_checkout_session
    return create_checkout_session()


# --- Stripe Webhook ---
@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    from stripe_checkout import handle_webhook
    return handle_webhook()


# --- Success Page ---
@app.route("/success")
def success():
    session_id = request.args.get("session_id")
    if not session_id:
        return redirect("/conductorsplaybook")

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
@app.route("/download/<token>")
def download(token):
    from downloads import handle_download
    return handle_download(token)


# --- Legal Pages ---
@app.route("/terms")
def terms():
    return send_from_directory("static", "terms.html")


@app.route("/privacy")
def privacy():
    return send_from_directory("static", "privacy.html")


@app.route("/refund")
def refund():
    return send_from_directory("static", "refund.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
