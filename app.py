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


# --- Landing Page ---
@app.route("/")
@app.route("/conductorsplaybook")
def landing():
    return send_from_directory("static", "landing.html")


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
