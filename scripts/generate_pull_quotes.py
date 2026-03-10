#!/usr/bin/env python3
"""
Kingdom Builders AI — Pull Quote Generator v2

Generates social media pull quote images for playbook marketing.
Each playbook gets 3 quotes in 2 sizes (6 images total per playbook).

Output naming: "The Conductors Playbook 1.png" (square), "The Conductors Playbook 1 wide.png" (landscape)
Sorted alphabetically so all 3 quotes for a playbook appear together for review.

Usage:
  python -m scripts.generate_pull_quotes                    # All playbooks
  python -m scripts.generate_pull_quotes The_Arrival.html   # Single playbook
"""

import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_DIR = ASSETS_DIR / "pull-quotes"

# ---------------------------------------------------------------------------
# FONTS
# ---------------------------------------------------------------------------
SERIF_BOLD = "C:/Windows/Fonts/georgiab.ttf"
SERIF_ITALIC = "C:/Windows/Fonts/georgiai.ttf"
SERIF_REGULAR = "C:/Windows/Fonts/georgia.ttf"
SANS_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
SANS_REGULAR = "C:/Windows/Fonts/segoeui.ttf"
SANS_LIGHT = "C:/Windows/Fonts/segoeuil.ttf"

# ---------------------------------------------------------------------------
# IMAGE SIZES
# ---------------------------------------------------------------------------
SQUARE = (1080, 1080)     # Instagram, Facebook
WIDE = (1200, 675)        # X.com, LinkedIn
BRAND_TEXT = "KingdomBuilders.ai"

# ---------------------------------------------------------------------------
# CURATED QUOTES — 3 per playbook: [hook, reveal, finale]
# ---------------------------------------------------------------------------
CURATED_QUOTES = {
    "The_Conductors_Playbook": [
        "Taste is the only skill\nthat cannot be automated.",
        "You do not produce through effort.\nYou produce through orchestration.",
        "The blade is forged.\nNow go conduct.",
    ],
    "The_Narrator": [
        "You are performing for an audience\nthat is no longer watching.",
        "The story you are living\nwas written by someone else.",
        "Pick up the pen.\nRewrite the script.",
    ],
    "The_Ghost_Frame": [
        "You have never had a fight\nwith your partner.",
        "The frame was installed\nbefore you could speak.",
        "See the frame.\nNow step outside it.",
    ],
    "The_Gravity_Well": [
        "You did not choose your orbit.\nBut you can change it.",
        "Purpose is not a feeling.\nIt is a gravitational force.",
        "Escape velocity reached.\nNow build your own gravity.",
    ],
    "The_Squirrel_Economy_Modified": [
        "The crash does not punish recklessness.\nIt reveals it.",
        "Your grandmother was right\nabout saving.",
        "The economy is a forest.\nPlant accordingly.",
    ],
    "The_Salmon_Journey": [
        "The only direction that builds anything\nis upstream.",
        "Compound interest is not math.\nIt is patience made visible.",
        "Swim.\nThe current was never the enemy.",
    ],
    "The_Wolfs_Table": [
        "The table is always being set\nbefore you sit down.",
        "The wolf does not negotiate.\nThe wolf prepares.",
        "Set your own table.\nInvite deliberately.",
    ],
    "The_Crows_Gambit": [
        "Every relationship is a repeated game.\nPlay accordingly.",
        "The Nash equilibrium is not optimal.\nIt is just stable.",
        "Trust is a strategy.\nNot a feeling.",
    ],
    "The_Eagles_Lens": [
        "Clarity is not seeing more.\nIt is seeing less.",
        "Strip. Test. Commit. Correct.\nFour moves. Every decision.",
        "The lens is focused.\nNow act.",
    ],
    "The_Octopus_Protocol": [
        "One arm at a time.\nNever eight.",
        "Revenue streams are not built.\nThey are sequenced.",
        "Eight arms. One brain.\nThat is the protocol.",
    ],
    "The_Ant_Network": [
        "No single ant knows the plan.\nThe plan still works.",
        "Trust is not given.\nIt is networked.",
        "Build the network.\nThe network builds everything else.",
    ],
    "The_Lighthouse_Keepers_Log": [
        "The storm is not an interruption.\nThe storm is the curriculum.",
        "The light does not chase ships.\nIt simply stays on.",
        "Keep the light burning.\nThat is the only job.",
    ],
    "The_Cost_Ledger": [
        "Every yes has a price.\nMost people never read the bill.",
        "The hidden cost is always\nthe one you feel last.",
        "Read the ledger.\nPay what you owe.",
    ],
    "The_Spiders_Loom": [
        "The web does not chase.\nThe web waits.",
        "Every thread is a relationship.\nEvery node is a choice.",
        "Weave with intention.\nThe web holds.",
    ],
    "The_Chameleons_Code": [
        "Adaptation without identity is extinction.",
        "You are not pretending.\nYou are translating.",
        "Know your true color.\nThen shift with purpose.",
    ],
    "The_Geckos_Grip": [
        "Recovery is not returning.\nIt is rebuilding from a new surface.",
        "The grip works on any wall.\nEven the ones you did not choose.",
        "Fall. Grip. Climb.\nThe surface changed. You adapted.",
    ],
    "The_Fireflys_Signal": [
        "The wrong signal attracts\nthe wrong audience.",
        "Brightness without frequency\nis just noise.",
        "Signal clearly.\nThe right ones will come.",
    ],
    "The_Foxs_Trail": [
        "The best path is the one\nnothing else is using.",
        "The fox does not outrun.\nThe fox outthinks.",
        "Find your trail.\nWalk it alone if you must.",
    ],
    "The_Moths_Flame": [
        "Not everything that glows\nis worth burning for.",
        "The flame does not care\nwho it burns.",
        "Turn from the flame.\nFind your own light.",
    ],
    "The_Bears_Winter": [
        "Dormancy is not weakness.\nDormancy is strategy.",
        "The bear does not fight winter.\nThe bear prepares for it.",
        "Rest is not retreat.\nRest is reload.",
    ],
    "The_Coyotes_Laugh": [
        "The ones who laugh at the rules\nare the ones rewriting them.",
        "Chaos is not the enemy.\nRigidity is.",
        "Laugh.\nThen build something unexpected.",
    ],
    "The_Pangolins_Armor": [
        "The armor you built to survive\nis the weight slowing you down.",
        "Protection and isolation\nwear the same shell.",
        "Uncurl.\nThe threat has passed.",
    ],
    "The_Horses_Gait": [
        "Speed is not a gait.\nRhythm is.",
        "The horse that wins\nis the one that paces.",
        "Find your rhythm.\nThe race is long.",
    ],
    "The_Compass_Rose": [
        "You do not need more options.\nYou need a bearing.",
        "North is not a direction.\nNorth is a decision.",
        "Set the bearing.\nWalk.",
    ],
    "The_Mockingbirds_Song": [
        "She never wrote a single song.\nShe wrote all of them.",
        "Attention is not free.\nAttention is architecture.",
        "Listen to everything.\nSing what matters.",
    ],
    "The_Starlings_Murmuration": [
        "You become the average\nof your seven closest influences.",
        "The murmuration has no leader.\nIt has alignment.",
        "Choose your seven.\nThey are choosing your future.",
    ],
    "The_Body_Lie": [
        "Your body has been keeping score\nwhile your mind changed the subject.",
        "The truth lives in your posture.\nNot in your explanation.",
        "Listen to your body.\nIt never learned to lie.",
    ],
    "The_Bonsai_Method": [
        "The cut is not the wound.\nThe cut is the design.",
        "A budget is not restriction.\nA budget is sculpture.",
        "Prune with intention.\nGrow with purpose.",
    ],
    "The_Fibonacci_Trim": [
        "Growth without pruning\nis just accumulation.",
        "The golden ratio is not math.\nIt is nature voting.",
        "Trim to the ratio.\nBeauty follows structure.",
    ],
    "The_Arrival": [
        "You have been everywhere.\nYou have arrived nowhere.",
        "Presence is not location.\nPresence is attention.",
        "Arrive.\nFinally, completely, arrive.",
    ],
    "The_Mycelium_Network": [
        "The most connected organism on Earth\nhas no brain.",
        "The network does not think.\nThe network transfers.",
        "Connect. Transfer. Grow.\nThe forest depends on it.",
    ],
    "The_Termite_Cathedral": [
        "No architect. No blueprint.\nJust a cathedral.",
        "Emergence does not need a plan.\nIt needs a principle.",
        "Build your piece.\nThe cathedral builds itself.",
    ],
    "The_Bees_Dance": [
        "The dance is the data.\nThe hive is the network.",
        "Communication is not talking.\nCommunication is moving.",
        "Dance your discovery.\nThe hive will follow.",
    ],
    "The_Otters_Play": [
        "Play is not the break from work.\nPlay is the work.",
        "Joy is not the reward.\nJoy is the method.",
        "Play.\nThe serious ones burn out first.",
    ],
    "The_Butterflys_Crossing": [
        "The crossing is not optional.\nThe wings are.",
        "Transformation costs everything\nyou were.",
        "Cross.\nWhat you become is worth what you lose.",
    ],
    "The_Elephants_Ground": [
        "Memory is not nostalgia.\nMemory is navigation.",
        "The elephant never forgets\nbecause forgetting is fatal.",
        "Remember.\nYour history is your compass.",
    ],
    "The_Whales_Breath": [
        "The deepest dive\nrequires the longest breath.",
        "Silence is not emptiness.\nSilence is preparation.",
        "Breathe.\nThen go deeper than anyone expects.",
    ],
    "The_Tide_Pools_Echo": [
        "The edge is where\neverything interesting lives.",
        "The tide pool survives\nbecause it embraces the boundary.",
        "Live at the edge.\nThat is where growth happens.",
    ],
    "Lay_It_Down": [
        "You cannot carry it\nand be carried by Him.",
        "The altar is not punishment.\nThe altar is freedom.",
        "Lay it down.\nWalk away lighter.",
    ],
    "Lay_It_Down_Wrath": [
        "Anger is a fire.\nYou are the house.",
        "The rage cycle has one exit.\nSurrender.",
        "Put down the torch.\nYou are standing in gasoline.",
    ],
    "Lay_It_Down_Envy": [
        "Envy compares your backstage\nto their highlight reel.",
        "Celebration is the antidote.\nNot comparison.",
        "Stay in your lane.\nIt was built for you.",
    ],
    "Lay_It_Down_Pride": [
        "The grip feels like strength.\nIt is just fear holding on.",
        "Control is the illusion.\nSurrender is the power.",
        "Open your hands.\nSee what stays.",
    ],
    "Lay_It_Down_Greed": [
        "Enough was the first word\nyou forgot.",
        "Accumulation is not security.\nIt is anxiety with a lock.",
        "You have enough.\nNow live like it.",
    ],
    "Lay_It_Down_Sloth": [
        "Stillness chose you.\nYou did not choose it.",
        "Comfort is the slow poison\nthat tastes like rest.",
        "Move.\nThe resistance is the point.",
    ],
    "Lay_It_Down_Gluttony": [
        "The hunger was never\nin your stomach.",
        "Consumption without purpose\nis just noise with a receipt.",
        "Fast from the excess.\nFind what was hiding underneath.",
    ],
    "Lay_It_Down_Lust": [
        "What you chase consumes you\nbefore you catch it.",
        "Desire is not the enemy.\nDisorder is.",
        "Redirect the fire.\nIt was meant to build, not burn.",
    ],
    "Dad_Talks_The_Dopamine_Drought": [
        "Your phone is a slot machine.\nYou are the pigeon.",
        "Every notification is a negotiation\nfor your attention.",
        "Guard your focus.\nIt is the last thing they cannot buy.",
    ],
    "Dad_Talks_The_Mirror_Test": [
        "Someone told you who you were.\nYou believed them.",
        "The mirror shows the outside.\nIdentity lives underneath.",
        "Look again.\nThis time, decide for yourself.",
    ],
}


# ---------------------------------------------------------------------------
# TITLE EXTRACTION
# ---------------------------------------------------------------------------
def extract_title(html: str, filename: str) -> str:
    """Extract the display title from the playbook."""
    # Try to get from <title> tag
    m = re.search(r'<title>([^<]+)</title>', html)
    if m:
        title = m.group(1)
        # Clean up common suffixes
        for suffix in [". Kingdom Builders AI", " | Kingdom Builders", " - Kingdom Builders"]:
            title = title.replace(suffix, "")
        title = title.strip().rstrip(".")
        if title and len(title) < 60:
            return title

    # Fallback: convert filename
    name = filename.replace(".html", "").replace("_", " ")
    if name.startswith("The "):
        name = "The " + name[4:]
    return name


# ---------------------------------------------------------------------------
# COLOR EXTRACTION
# ---------------------------------------------------------------------------
def hex_to_rgb(hex_str: str) -> tuple:
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


def extract_colors(html: str) -> dict:
    colors = {
        "dark": (20, 10, 40),
        "dark2": (30, 20, 60),
        "accent": (212, 168, 67),
        "accent2": (180, 140, 60),
        "light": (250, 248, 240),
    }

    root_match = re.search(r':root\s*\{([^}]+)\}', html)
    if not root_match:
        return colors

    root_css = root_match.group(1)

    def find_color(pattern_list):
        for pattern in pattern_list:
            m = re.search(pattern + r'\s*:\s*(#[0-9A-Fa-f]{3,8})', root_css)
            if m:
                return hex_to_rgb(m.group(1))
        return None

    dark = find_color([
        r'--ink', r'--iron-dark', r'--purple-deep', r'--indigo-deep',
        r'--indigo', r'--navy', r'--deep', r'--forest', r'--canopy',
        r'--midnight', r'--obsidian', r'--sea', r'--ocean', r'--dusk',
        r'--soil', r'--saddle', r'--night', r'--ridge', r'--dirt-dark',
        r'--terra-dark',
    ])
    if dark:
        colors["dark"] = dark
        colors["dark2"] = tuple(min(c + 25, 255) for c in dark)

    accent = find_color([
        r'--gold', r'--amber', r'--ember', r'--compass-gold',
        r'--teal', r'--amber-glow', r'--fire', r'--acorn',
        r'--ember-glow',
    ])
    if accent:
        colors["accent"] = accent
        colors["accent2"] = tuple(max(c - 30, 0) for c in accent)

    light = find_color([
        r'--cream', r'--bone', r'--stone', r'--white',
        r'--cream-warm', r'--silver-pale',
    ])
    if light:
        colors["light"] = light

    return colors


# ---------------------------------------------------------------------------
# IMAGE GENERATION
# ---------------------------------------------------------------------------
def create_background(w: int, h: int, colors: dict) -> Image.Image:
    """Gradient + radial glow + vignette + grain."""
    dark = np.array(colors["dark"], dtype=np.float32)
    dark2 = np.array(colors["dark2"], dtype=np.float32)
    accent = np.array(colors["accent"], dtype=np.float32)

    y_coords, x_coords = np.mgrid[0:h, 0:w].astype(np.float32)

    # Diagonal gradient
    t = (x_coords / w * 0.3 + y_coords / h * 0.7)
    t = t * t * (3 - 2 * t)
    img_arr = dark[None, None, :] + (dark2 - dark)[None, None, :] * t[:, :, None]

    # Radial glow
    cx, cy = w / 2, h * 0.35
    max_r = max(w, h) * 0.6
    dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
    glow_t = np.clip(1 - dist / max_r, 0, 1)
    glow_t = glow_t * glow_t * 0.08
    img_arr += accent[None, None, :] * glow_t[:, :, None]

    # Vignette
    cx2, cy2 = w / 2, h / 2
    max_dist = math.sqrt(cx2 * cx2 + cy2 * cy2)
    dist2 = np.sqrt((x_coords - cx2) ** 2 + (y_coords - cy2) ** 2)
    darken = (dist2 / max_dist) ** 2 * 0.4
    img_arr *= (1 - darken)[:, :, None]

    # Film grain
    rng = np.random.RandomState(42)
    noise = rng.randint(-5, 6, size=(h, w, 1)).astype(np.float32)
    img_arr += noise

    img_arr = np.clip(img_arr, 0, 255).astype(np.uint8)
    return Image.fromarray(img_arr, "RGB")


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            test = current + " " + word
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_accent_line(draw, cx, y, width, color):
    """Draw a thin decorative line with center diamond."""
    muted = tuple(int(c * 0.3) for c in color)
    half = width // 2
    draw.line([(cx - half, y), (cx + half, y)], fill=muted, width=1)
    d = 3
    draw.polygon([(cx, y - d), (cx + d, y), (cx, y + d), (cx - d, y)], fill=muted)


def generate_quote_image(
    title: str,
    quote_text: str,
    colors: dict,
    size: tuple,
    output_path: Path,
):
    """Generate a single pull quote image."""
    w, h = size
    is_wide = w > h
    padding_x = int(w * 0.1)
    text_width = w - (padding_x * 2)

    img = create_background(w, h, colors)
    draw = ImageDraw.Draw(img)

    accent = colors["accent"]
    text_color = (250, 245, 230)
    title_color = tuple(int(c * 0.85 + 40) for c in accent)

    # --- BADGE ---
    try:
        badge_font = ImageFont.truetype(SANS_REGULAR, 11)
    except OSError:
        badge_font = ImageFont.load_default()
    badge_text = "KINGDOM BUILDERS AI"
    badge_bbox = badge_font.getbbox(badge_text)
    badge_w = badge_bbox[2] - badge_bbox[0]
    badge_x = (w - badge_w) // 2
    badge_y = int(h * 0.08) if not is_wide else int(h * 0.08)
    badge_color = tuple(int(c * 0.5) for c in accent)
    draw.text((badge_x, badge_y), badge_text, font=badge_font, fill=badge_color)

    # --- TITLE ---
    title_size = 22 if not is_wide else 20
    try:
        title_font = ImageFont.truetype(SANS_BOLD, title_size)
    except OSError:
        title_font = ImageFont.load_default()

    # Wrap title if needed
    title_lines = wrap_text(title, title_font, text_width)
    title_line_h = int(title_size * 1.4)
    title_y = badge_y + 30
    for tl in title_lines:
        tl_bbox = title_font.getbbox(tl)
        tl_w = tl_bbox[2] - tl_bbox[0]
        draw.text(((w - tl_w) // 2, title_y), tl, font=title_font, fill=title_color)
        title_y += title_line_h

    # --- DECORATIVE LINE ---
    line_y = title_y + 16
    draw_accent_line(draw, w // 2, line_y, 180, accent)

    # --- QUOTE ---
    quote_size = 48 if not is_wide else 38
    try:
        quote_font = ImageFont.truetype(SERIF_BOLD, quote_size)
    except OSError:
        try:
            quote_font = ImageFont.truetype(SERIF_ITALIC, quote_size)
        except OSError:
            quote_font = ImageFont.load_default()

    quote_lines = wrap_text(quote_text, quote_font, text_width)
    line_height = int(quote_size * 1.55)
    total_quote_h = len(quote_lines) * line_height

    # Center quote in remaining space
    space_top = line_y + 20
    space_bottom = h - int(h * 0.1)
    quote_start_y = space_top + (space_bottom - space_top - total_quote_h) // 2

    for i, line in enumerate(quote_lines):
        bbox = quote_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        x = (w - lw) // 2
        y = quote_start_y + i * line_height
        # Shadow
        shadow = tuple(max(0, c - 50) for c in colors["dark"])
        draw.text((x + 2, y + 2), line, font=quote_font, fill=shadow)
        # Text
        draw.text((x, y), line, font=quote_font, fill=text_color)

    # --- DECORATIVE LINE below quote ---
    below_y = quote_start_y + total_quote_h + 20
    if below_y < h - 60:
        draw_accent_line(draw, w // 2, below_y, 180, accent)

    # --- BRAND ---
    try:
        brand_font = ImageFont.truetype(SANS_REGULAR, 13)
    except OSError:
        brand_font = ImageFont.load_default()
    brand_color = tuple(int(c * 0.35 + colors["dark"][i] * 0.65) for i, c in enumerate(text_color[:3]))
    brand_bbox = brand_font.getbbox(BRAND_TEXT)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text(((w - brand_w) // 2, h - 45), BRAND_TEXT, font=brand_font, fill=brand_color)

    # --- SAVE ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG", optimize=True)


# ---------------------------------------------------------------------------
# FILE PROCESSING
# ---------------------------------------------------------------------------
def stem_to_display(stem: str) -> str:
    """Convert file stem to display name: The_Conductors_Playbook -> The Conductors Playbook"""
    name = stem.replace("_Modified", "")
    return name.replace("_", " ")


def process_playbook(filepath: Path) -> list:
    """Process a single playbook. Returns list of output paths."""
    stem = filepath.stem  # e.g. "The_Conductors_Playbook"
    display_name = stem_to_display(stem)

    html = filepath.read_text(encoding="utf-8", errors="replace")
    colors = extract_colors(html)
    title = extract_title(html, filepath.name)

    # Get quotes
    quotes = CURATED_QUOTES.get(stem)
    if not quotes:
        # Fallback: use filename as a single quote
        print(f"  WARNING: No curated quotes for {stem}, skipping")
        return []

    outputs = []
    for idx, quote in enumerate(quotes, 1):
        # Square (1080x1080)
        sq_path = OUTPUT_DIR / f"{display_name} {idx}.png"
        generate_quote_image(title, quote, colors, SQUARE, sq_path)
        outputs.append(sq_path)

        # Wide (1200x675)
        wide_path = OUTPUT_DIR / f"{display_name} {idx} wide.png"
        generate_quote_image(title, quote, colors, WIDE, wide_path)
        outputs.append(wide_path)

    return outputs


def get_active_playbooks() -> list:
    playbooks = []
    for f in ASSETS_DIR.iterdir():
        if f.is_file() and f.suffix == ".html":
            playbooks.append(f)
    playbooks.sort(key=lambda p: p.name)
    return playbooks


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            target = ASSETS_DIR / arg
            if not target.exists():
                target = ASSETS_DIR / (arg + ".html")
            if not target.exists():
                print(f"  NOT FOUND: {arg}")
                continue
            results = process_playbook(target)
            for r in results:
                print(f"  GENERATED: {r.name}")
    else:
        playbooks = get_active_playbooks()
        print(f"Found {len(playbooks)} active playbooks.\n")

        total = 0
        for i, pb in enumerate(playbooks, 1):
            name = pb.stem
            print(f"  [{i:2d}/{len(playbooks)}] {name}...", end=" ", flush=True)
            try:
                results = process_playbook(pb)
                total += len(results)
                print(f"OK ({len(results)} images)")
            except Exception as e:
                print(f"ERROR: {e}")

        print(f"\nDone. {total} images saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
