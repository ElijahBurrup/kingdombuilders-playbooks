"""
Seed script — populates the PostgreSQL database with categories, series,
playbooks, and an admin user.

Usage:
    python -m scripts.seed_playbooks
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

# Ensure we can import from the project root
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.config import settings
from api.database import Base, engine, async_session
from api.models.user import User
from api.models.playbook import Category, Series, Playbook
from api.utils.security import hash_password

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"

# ---------------------------------------------------------------------------
# Category definitions (from index.html filter bar)
# ---------------------------------------------------------------------------
CATEGORIES = [
    {"name": "Productivity", "slug": "productivity", "color_bg": "rgba(123,79,191,0.08)", "color_text": "#7B4FBF", "display_order": 1},
    {"name": "Faith", "slug": "faith", "color_bg": "rgba(218,165,32,0.08)", "color_text": "#DAA520", "display_order": 2},
    {"name": "Technology", "slug": "technology", "color_bg": "rgba(0,128,128,0.08)", "color_text": "#008080", "display_order": 3},
    {"name": "Mindset", "slug": "mindset", "color_bg": "rgba(70,130,180,0.08)", "color_text": "#4682B4", "display_order": 4},
    {"name": "Identity", "slug": "identity", "color_bg": "rgba(199,21,133,0.08)", "color_text": "#C71585", "display_order": 5},
    {"name": "Finance", "slug": "finance", "color_bg": "rgba(34,139,34,0.08)", "color_text": "#228B22", "display_order": 6},
    {"name": "Economics", "slug": "economics", "color_bg": "rgba(184,134,11,0.08)", "color_text": "#B8860B", "display_order": 7},
    {"name": "Relationships", "slug": "relationships", "color_bg": "rgba(220,20,60,0.08)", "color_text": "#DC143C", "display_order": 8},
    {"name": "Strategy", "slug": "strategy", "color_bg": "rgba(75,0,130,0.08)", "color_text": "#4B0082", "display_order": 9},
    {"name": "Leadership", "slug": "leadership", "color_bg": "rgba(0,100,0,0.08)", "color_text": "#006400", "display_order": 10},
    {"name": "Communication", "slug": "communication", "color_bg": "rgba(255,140,0,0.08)", "color_text": "#FF8C00", "display_order": 11},
    {"name": "Resilience", "slug": "resilience", "color_bg": "rgba(139,69,19,0.08)", "color_text": "#8B4513", "display_order": 12},
    {"name": "History", "slug": "history", "color_bg": "rgba(128,0,0,0.08)", "color_text": "#800000", "display_order": 13},
    {"name": "Philosophy", "slug": "philosophy", "color_bg": "rgba(85,107,47,0.08)", "color_text": "#556B2F", "display_order": 14},
]

# ---------------------------------------------------------------------------
# Series definitions
# ---------------------------------------------------------------------------
SERIES_DEFS = [
    {
        "name": "Lay It Down",
        "slug": "lay-it-down",
        "description": "A 7-part series on releasing the seven deadly sins through faith and surrender.",
        "display_order": 1,
    },
    {
        "name": "A Process Model",
        "slug": "a-process-model",
        "description": "A 6-part philosophy series exploring how natural processes teach us about living well.",
        "display_order": 2,
    },
    {
        "name": "The Shield Series",
        "slug": "the-shield-series",
        "description": "A 3-part series on recognizing, defending against, and surviving narcissistic abuse through animal parable.",
        "display_order": 3,
    },
]

# ---------------------------------------------------------------------------
# Playbook definitions (from Playwright PLAYBOOKS array + legacy routes)
# ---------------------------------------------------------------------------
PLAYBOOKS_DATA = [
    {"slug": "conductors-playbook", "title": "The Conductor's Playbook", "route": "/conductorsplaybook", "category": "productivity", "landing_file": "landing.html", "asset_file": "The_Conductors_Playbook.html", "pricing_type": "paid", "price_cents": 6700, "cover_emoji": "\U0001f3bc", "featured": True},
    {"slug": "lay-it-down", "title": "Lay It Down", "route": "/layitdown", "category": "faith", "series": "lay-it-down", "series_order": 0, "landing_file": "lay-it-down.html", "asset_file": "Lay_It_Down.html", "cover_emoji": "\u2694\ufe0f"},
    {"slug": "the-ant-network", "title": "The Ant Network", "route": "/theantnetwork", "category": "technology", "landing_file": "the-ant-network.html", "asset_file": "The_Ant_Network.html", "cover_emoji": "\U0001f41c"},
    {"slug": "the-cost-ledger", "title": "The Cost Ledger", "route": "/thecostledger", "category": "mindset", "landing_file": "the-cost-ledger.html", "asset_file": "The_Cost_Ledger.html", "cover_emoji": "\U0001f4d2"},
    {"slug": "the-ghost-frame", "title": "The Ghost Frame", "route": "/theghostframe", "category": "mindset", "landing_file": "the-ghost-frame.html", "asset_file": "The_Ghost_Frame.html", "cover_emoji": "\U0001f47b"},
    {"slug": "the-gravity-well", "title": "The Gravity Well", "route": "/thegravitywell", "category": "productivity", "landing_file": "the-gravity-well.html", "asset_file": "The_Gravity_Well.html", "cover_emoji": "\U0001fa90"},
    {"slug": "the-mockingbirds-song", "title": "The Mockingbird\u2019s Song", "route": "/themockingbirdssong", "category": "technology", "landing_file": "the-mockingbirds-song.html", "asset_file": "The_Mockingbirds_Song.html", "cover_emoji": "\U0001f426"},
    {"slug": "the-narrator", "title": "The Narrator", "route": "/thenarrator", "category": "identity", "landing_file": "the-narrator.html", "asset_file": "The_Narrator.html", "cover_emoji": "\U0001f4d6"},
    {"slug": "the-salmon-journey", "title": "The Salmon Journey", "route": "/thesalmonjourney", "category": "finance", "landing_file": "the-salmon-journey.html", "asset_file": "The_Salmon_Journey.html", "cover_emoji": "\U0001f41f"},
    {"slug": "the-squirrel-economy", "title": "The Squirrel Economy", "route": "/thesquirreleconomy", "category": "economics", "landing_file": "the-squirrel-economy.html", "asset_file": "The_Squirrel_Economy_Modified.html", "cover_emoji": "\U0001f43f\ufe0f"},
    {"slug": "the-wolfs-table", "title": "The Wolf's Table", "route": "/thewolfstable", "category": "relationships", "landing_file": "the-wolfs-table.html", "asset_file": "The_Wolfs_Table.html", "cover_emoji": "\U0001f43a"},
    {"slug": "the-crows-gambit", "title": "The Crow's Gambit", "route": "/thecrowsgambit", "category": "strategy", "landing_file": "the-crows-gambit.html", "asset_file": "The_Crows_Gambit.html", "cover_emoji": "\U0001f426\u200d\u2b1b"},
    {"slug": "the-eagles-lens", "title": "The Eagle's Lens", "route": "/theeagleslens", "category": "leadership", "landing_file": "the-eagles-lens.html", "asset_file": "The_Eagles_Lens.html", "cover_emoji": "\U0001f985"},
    {"slug": "the-lighthouse-keepers-log", "title": "The Lighthouse Keeper's Log", "route": "/thelighthousekeeperslog", "category": "mindset", "landing_file": "the-lighthouse-keepers-log.html", "asset_file": "The_Lighthouse_Keepers_Log.html", "cover_emoji": "\U0001f3e0"},
    {"slug": "the-octopus-protocol", "title": "The Octopus Protocol", "route": "/theoctopusprotocol", "category": "finance", "landing_file": "the-octopus-protocol.html", "asset_file": "The_Octopus_Protocol.html", "cover_emoji": "\U0001f419"},
    {"slug": "the-starlings-murmuration", "title": "The Starling's Murmuration", "route": "/thestarlingsmurmuration", "category": "leadership", "landing_file": "the-starlings-murmuration.html", "asset_file": "The_Starlings_Murmuration.html", "cover_emoji": "\U0001f426"},
    {"slug": "the-chameleons-code", "title": "The Chameleon's Code", "route": "/thechameleonscode", "category": "communication", "landing_file": "the-chameleons-code.html", "asset_file": "The_Chameleons_Code.html", "cover_emoji": "\U0001f98e"},
    {"slug": "the-spiders-loom", "title": "The Spider's Loom", "route": "/thespidersloom", "category": "productivity", "landing_file": "the-spiders-loom.html", "asset_file": "The_Spiders_Loom.html", "cover_emoji": "\U0001f577\ufe0f"},
    {"slug": "the-geckos-grip", "title": "The Gecko's Grip", "route": "/thegeckosgrip", "category": "resilience", "landing_file": "the-geckos-grip.html", "asset_file": "The_Geckos_Grip.html", "cover_emoji": "\U0001f98e"},
    {"slug": "the-fireflys-signal", "title": "The Firefly's Signal", "route": "/thefireflyssignal", "category": "strategy", "landing_file": "the-fireflys-signal.html", "asset_file": "The_Fireflys_Signal.html", "cover_emoji": "\u2728"},
    {"slug": "the-foxs-trail", "title": "The Fox's Trail", "route": "/thefoxstrail", "category": "strategy", "landing_file": "the-foxs-trail.html", "asset_file": "The_Foxs_Trail.html", "cover_emoji": "\U0001f98a"},
    {"slug": "the-moths-flame", "title": "The Moth's Flame", "route": "/themothsflame", "category": "mindset", "landing_file": "the-moths-flame.html", "asset_file": "The_Moths_Flame.html", "cover_emoji": "\U0001f525"},
    {"slug": "the-bears-winter", "title": "The Bear's Winter", "route": "/thebearswinter", "category": "mindset", "landing_file": "the-bears-winter.html", "asset_file": "The_Bears_Winter.html", "cover_emoji": "\U0001f43b"},
    {"slug": "the-coyotes-laugh", "title": "The Coyote's Laugh", "route": "/thecoyoteslaugh", "category": "resilience", "landing_file": "the-coyotes-laugh.html", "asset_file": "The_Coyotes_Laugh.html", "cover_emoji": "\U0001f43a"},
    {"slug": "the-pangolins-armor", "title": "The Pangolin's Armor", "route": "/thepangolinsarmor", "category": "mindset", "landing_file": "the-pangolins-armor.html", "asset_file": "The_Pangolins_Armor.html", "cover_emoji": "\U0001f9a5"},
    {"slug": "the-horses-gait", "title": "The Horse's Gait", "route": "/thehorsesgait", "category": "productivity", "landing_file": "the-horses-gait.html", "asset_file": "The_Horses_Gait.html", "cover_emoji": "\U0001f40e"},
    {"slug": "the-compass-rose", "title": "The Compass Rose", "route": "/thecompassrose", "category": "history", "landing_file": "the-compass-rose.html", "asset_file": "The_Compass_Rose.html", "cover_emoji": "\U0001f9ed"},
    {"slug": "lay-it-down-pride", "title": "Lay It Down: Pride", "route": "/layitdownpride", "category": "faith", "series": "lay-it-down", "series_order": 1, "landing_file": "lay-it-down-pride.html", "asset_file": "Lay_It_Down_Pride.html", "cover_emoji": "\U0001f451"},
    {"slug": "lay-it-down-envy", "title": "Lay It Down: Envy", "route": "/layitdownenvy", "category": "faith", "series": "lay-it-down", "series_order": 2, "landing_file": "lay-it-down-envy.html", "asset_file": "Lay_It_Down_Envy.html", "cover_emoji": "\U0001f49a"},
    {"slug": "lay-it-down-wrath", "title": "Lay It Down: Wrath", "route": "/layitdownwrath", "category": "faith", "series": "lay-it-down", "series_order": 3, "landing_file": "lay-it-down-wrath.html", "asset_file": "Lay_It_Down_Wrath.html", "cover_emoji": "\U0001f525"},
    {"slug": "the-tide-pools-echo", "title": "The Tide Pool's Echo", "route": "/thetidepoolsecho", "category": "philosophy", "series": "a-process-model", "series_order": 1, "landing_file": "the-tide-pools-echo.html", "asset_file": "The_Tide_Pools_Echo.html", "cover_emoji": "\U0001f30a"},
    {"slug": "the-whales-breath", "title": "The Whale's Breath", "route": "/thewhalesbreath", "category": "philosophy", "series": "a-process-model", "series_order": 2, "landing_file": "the-whales-breath.html", "asset_file": "The_Whales_Breath.html", "cover_emoji": "\U0001f433"},
    {"slug": "the-butterflys-crossing", "title": "The Butterfly's Crossing", "route": "/thebutterflyscrossing", "category": "philosophy", "series": "a-process-model", "series_order": 3, "landing_file": "the-butterflys-crossing.html", "asset_file": "The_Butterflys_Crossing.html", "cover_emoji": "\U0001f98b"},
    {"slug": "the-elephants-ground", "title": "The Elephant's Ground", "route": "/theeleophantsground", "category": "philosophy", "series": "a-process-model", "series_order": 4, "landing_file": "the-elephants-ground.html", "asset_file": "The_Elephants_Ground.html", "cover_emoji": "\U0001f418"},
    {"slug": "the-bees-dance", "title": "The Bee's Dance", "route": "/thebeesdance", "category": "philosophy", "series": "a-process-model", "series_order": 5, "landing_file": "the-bees-dance.html", "asset_file": "The_Bees_Dance.html", "cover_emoji": "\U0001f41d"},
    {"slug": "the-otters-play", "title": "The Otter's Play", "route": "/theottersplay", "category": "philosophy", "series": "a-process-model", "series_order": 6, "landing_file": "the-otters-play.html", "asset_file": "The_Otters_Play.html", "cover_emoji": "\U0001f9a6"},
    {"slug": "the-mantis-shrimps-eye", "title": "The Mantis Shrimp's Eye", "route": "/themantisshrimpseye", "category": "mindset", "series": "the-shield-series", "series_order": 1, "landing_file": "the-mantis-shrimps-eye.html", "asset_file": "The_Mantis_Shrimps_Eye.html", "cover_emoji": "\U0001f990"},
    {"slug": "the-porcupines-quills", "title": "The Porcupine's Quills", "route": "/theporcupinesquills", "category": "mindset", "series": "the-shield-series", "series_order": 2, "landing_file": "the-porcupines-quills.html", "asset_file": "The_Porcupines_Quills.html", "cover_emoji": "\U0001f994"},
    {"slug": "the-tardigrade-protocol", "title": "The Tardigrade Protocol", "route": "/thetardigradeprotocol", "category": "resilience", "series": "the-shield-series", "series_order": 3, "landing_file": "the-tardigrade-protocol.html", "asset_file": "The_Tardigrade_Protocol.html", "cover_emoji": "\U0001f9ec"},
]


def _read_html_file(directory: Path, filename: str) -> str:
    """Read an HTML file, returning empty string if not found."""
    path = directory / filename
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return f"<!-- {filename} not found -->"


async def seed():
    print("Seeding database...")

    async with async_session() as db:
        # --- Categories ---
        cat_map = {}
        for cat_data in CATEGORIES:
            existing = (await db.execute(
                select(Category).where(Category.slug == cat_data["slug"])
            )).scalar_one_or_none()
            if existing:
                cat_map[cat_data["slug"]] = existing
                print(f"  Category '{cat_data['name']}' already exists")
            else:
                cat = Category(**cat_data)
                db.add(cat)
                await db.flush()
                cat_map[cat_data["slug"]] = cat
                print(f"  Created category: {cat_data['name']}")

        # --- Series ---
        series_map = {}
        for series_data in SERIES_DEFS:
            existing = (await db.execute(
                select(Series).where(Series.slug == series_data["slug"])
            )).scalar_one_or_none()
            if existing:
                series_map[series_data["slug"]] = existing
                print(f"  Series '{series_data['name']}' already exists")
            else:
                s = Series(**series_data)
                db.add(s)
                await db.flush()
                series_map[series_data["slug"]] = s
                print(f"  Created series: {series_data['name']}")

        # --- Playbooks ---
        for pb_data in PLAYBOOKS_DATA:
            existing = (await db.execute(
                select(Playbook).where(Playbook.slug == pb_data["slug"])
            )).scalar_one_or_none()
            if existing:
                print(f"  Playbook '{pb_data['title']}' already exists")
                continue

            landing_html = _read_html_file(STATIC_DIR, pb_data["landing_file"])
            content_html = _read_html_file(ASSETS_DIR, pb_data["asset_file"])

            category = cat_map[pb_data["category"]]
            series = series_map.get(pb_data.get("series")) if pb_data.get("series") else None

            playbook = Playbook(
                slug=pb_data["slug"],
                title=pb_data["title"],
                description=f"{pb_data['title']} — a KingdomBuilders.AI playbook.",
                landing_html=landing_html,
                content_html=content_html,
                pricing_type=pb_data.get("pricing_type", "free"),
                price_cents=pb_data.get("price_cents", 0),
                category_id=category.id,
                series_id=series.id if series else None,
                series_order=pb_data.get("series_order"),
                cover_emoji=pb_data.get("cover_emoji"),
                featured=pb_data.get("featured", False),
                status="published",
                published_at=datetime.now(timezone.utc),
            )
            db.add(playbook)
            print(f"  Created playbook: {pb_data['title']}")

        await db.flush()

        # --- Admin user ---
        existing_admin = (await db.execute(
            select(User).where(User.email == "elijah@kingdombuilders.ai")
        )).scalar_one_or_none()
        if existing_admin:
            print("  Admin user already exists")
        else:
            admin = User(
                email="elijah@kingdombuilders.ai",
                password_hash=hash_password("changeme123"),
                display_name="Elijah",
                role="admin",
                email_verified=True,
            )
            db.add(admin)
            print("  Created admin user: elijah@kingdombuilders.ai")

        await db.commit()

    print(f"Seeding complete! {len(CATEGORIES)} categories, {len(SERIES_DEFS)} series, {len(PLAYBOOKS_DATA)} playbooks.")


if __name__ == "__main__":
    asyncio.run(seed())
