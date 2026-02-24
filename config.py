import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Stripe
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Resend
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

# App
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

# Paths — use Render persistent disk if available, else local data/
if os.environ.get("RENDER"):
    DATA_DIR = Path("/opt/render/project/src/data")
else:
    DATA_DIR = BASE_DIR / "data"

PDF_PATH = BASE_DIR / "assets" / "conductors_playbook.pdf"
