import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Stripe
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Stripe Price IDs (set these from Stripe Dashboard > Products > Prices)
STRIPE_PRICE_SINGLE = os.environ.get("STRIPE_PRICE_SINGLE", "")       # $2.50 one-time
STRIPE_PRICE_MONTHLY = os.environ.get("STRIPE_PRICE_MONTHLY", "")     # $10/mo subscription
STRIPE_PRICE_YEARLY = os.environ.get("STRIPE_PRICE_YEARLY", "")       # $100/yr subscription

# Legacy single price ID (kept for backwards compatibility)
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")

# Resend
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

# App
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
URL_PREFIX = os.environ.get("URL_PREFIX", "")  # e.g. "/playbooks" for subpath deployment

# Paths — use Render persistent disk if available, else local data/
if os.environ.get("RENDER"):
    DATA_DIR = Path("/opt/render/project/src/data")
else:
    DATA_DIR = BASE_DIR / "data"

PDF_PATH = BASE_DIR / "assets" / "conductors_playbook.pdf"
