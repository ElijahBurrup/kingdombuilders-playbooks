from datetime import datetime, timezone

from flask import send_file, render_template, request

import config
from database import get_purchase_by_token, decrement_download, log_download


def handle_download(token):
    """Validate download token and serve the PDF."""
    purchase = get_purchase_by_token(token)

    if not purchase:
        return render_template("error.html",
            title="Invalid Link",
            message="This download link is not valid. Please check your email for the correct link."
        ), 404

    # Check expiration
    expires_at = datetime.fromisoformat(purchase["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        return render_template("error.html",
            title="Link Expired",
            message="This download link has expired (30-day limit). Please contact support@kingdombuilders.ai for assistance."
        ), 410

    # Check remaining downloads
    if purchase["downloads_remaining"] <= 0:
        return render_template("error.html",
            title="Download Limit Reached",
            message="You've used all 5 downloads for this purchase. Please contact support@kingdombuilders.ai for assistance."
        ), 403

    # Check PDF exists
    if not config.PDF_PATH.exists():
        return render_template("error.html",
            title="File Unavailable",
            message="The file is temporarily unavailable. Please try again later or contact support@kingdombuilders.ai."
        ), 503

    # Decrement counter and log
    decrement_download(purchase["id"])
    log_download(
        purchase_id=purchase["id"],
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent", "")
    )

    return send_file(
        config.PDF_PATH,
        as_attachment=True,
        download_name="The-Conductors-Playbook-KingdomBuildersAI.pdf",
        mimetype="application/pdf"
    )
