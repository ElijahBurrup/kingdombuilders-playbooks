#!/usr/bin/env python3
"""
Kingdom Builders AI — Pull Quote Generator v3

Uses Playwright to screenshot each playbook's actual cover design (condensed),
then composites the quote text below the title. This ensures the pull quote
images match the real cover look — fonts, gradients, animations and all.

Each playbook gets 3 quotes in 2 sizes (6 images total per playbook).

Output naming: "The Conductors Playbook 1.png" (square), "The Conductors Playbook 1 wide.png" (wide)

Usage:
  python -m scripts.generate_pull_quotes                    # All playbooks
  python -m scripts.generate_pull_quotes The_Arrival.html   # Single playbook
"""

import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_DIR = ASSETS_DIR / "pull-quotes"

# ---------------------------------------------------------------------------
# IMAGE SIZES
# ---------------------------------------------------------------------------
SQUARE = (1080, 1080)     # Instagram, Facebook
WIDE = (1200, 675)        # X.com, LinkedIn

# ---------------------------------------------------------------------------
# CURATED QUOTES — 3 per playbook: [hook, reveal, finale]
# ---------------------------------------------------------------------------
CURATED_QUOTES = {
    "The_Conductors_Playbook": [
        "Taste is the only skill that cannot be automated.",
        "You do not produce through effort. You produce through orchestration.",
        "The blade is forged. Now go conduct.",
    ],
    "The_Narrator": [
        "You are performing for an audience that is no longer watching.",
        "The story you are living was written by someone else.",
        "Pick up the pen. Rewrite the script.",
    ],
    "The_Ghost_Frame": [
        "You have never had a fight with your partner.",
        "The frame was installed before you could speak.",
        "See the frame. Now step outside it.",
    ],
    "The_Gravity_Well": [
        "You did not choose your orbit. But you can change it.",
        "Purpose is not a feeling. It is a gravitational force.",
        "Escape velocity reached. Now build your own gravity.",
    ],
    "The_Squirrel_Economy_Modified": [
        "The crash does not punish recklessness. It reveals it.",
        "Your grandmother was right about saving.",
        "The economy is a forest. Plant accordingly.",
    ],
    "The_Salmon_Journey": [
        "The only direction that builds anything is upstream.",
        "Compound interest is not math. It is patience made visible.",
        "Swim. The current was never the enemy.",
    ],
    "The_Wolfs_Table": [
        "The table is always being set before you sit down.",
        "The wolf does not negotiate. The wolf prepares.",
        "Set your own table. Invite deliberately.",
    ],
    "The_Crows_Gambit": [
        "Every relationship is a repeated game. Play accordingly.",
        "The Nash equilibrium is not optimal. It is just stable.",
        "Trust is a strategy. Not a feeling.",
    ],
    "The_Eagles_Lens": [
        "Clarity is not seeing more. It is seeing less.",
        "Strip. Test. Commit. Correct. Four moves. Every decision.",
        "The lens is focused. Now act.",
    ],
    "The_Octopus_Protocol": [
        "One arm at a time. Never eight.",
        "Revenue streams are not built. They are sequenced.",
        "Eight arms. One brain. That is the protocol.",
    ],
    "The_Ant_Network": [
        "No single ant knows the plan. The plan still works.",
        "Trust is not given. It is networked.",
        "Build the network. The network builds everything else.",
    ],
    "The_Lighthouse_Keepers_Log": [
        "The storm is not an interruption. The storm is the curriculum.",
        "The light does not chase ships. It simply stays on.",
        "Keep the light burning. That is the only job.",
    ],
    "The_Cost_Ledger": [
        "Every yes has a price. Most people never read the bill.",
        "The hidden cost is always the one you feel last.",
        "Read the ledger. Pay what you owe.",
    ],
    "The_Spiders_Loom": [
        "The web does not chase. The web waits.",
        "Every thread is a relationship. Every node is a choice.",
        "Weave with intention. The web holds.",
    ],
    "The_Chameleons_Code": [
        "Adaptation without identity is extinction.",
        "You are not pretending. You are translating.",
        "Know your true color. Then shift with purpose.",
    ],
    "The_Geckos_Grip": [
        "Recovery is not returning. It is rebuilding from a new surface.",
        "The grip works on any wall. Even the ones you did not choose.",
        "Fall. Grip. Climb. The surface changed. You adapted.",
    ],
    "The_Fireflys_Signal": [
        "The wrong signal attracts the wrong audience.",
        "Brightness without frequency is just noise.",
        "Signal clearly. The right ones will come.",
    ],
    "The_Foxs_Trail": [
        "The best path is the one nothing else is using.",
        "The fox does not outrun. The fox outthinks.",
        "Find your trail. Walk it alone if you must.",
    ],
    "The_Moths_Flame": [
        "Not everything that glows is worth burning for.",
        "The flame does not care who it burns.",
        "Turn from the flame. Find your own light.",
    ],
    "The_Bears_Winter": [
        "Dormancy is not weakness. Dormancy is strategy.",
        "The bear does not fight winter. The bear prepares for it.",
        "Rest is not retreat. Rest is reload.",
    ],
    "The_Coyotes_Laugh": [
        "The ones who laugh at the rules are the ones rewriting them.",
        "Chaos is not the enemy. Rigidity is.",
        "Laugh. Then build something unexpected.",
    ],
    "The_Pangolins_Armor": [
        "The armor you built to survive is the weight slowing you down.",
        "Protection and isolation wear the same shell.",
        "Uncurl. The threat has passed.",
    ],
    "The_Horses_Gait": [
        "Speed is not a gait. Rhythm is.",
        "The horse that wins is the one that paces.",
        "Find your rhythm. The race is long.",
    ],
    "The_Compass_Rose": [
        "You do not need more options. You need a bearing.",
        "North is not a direction. North is a decision.",
        "Set the bearing. Walk.",
    ],
    "The_Mockingbirds_Song": [
        "She never wrote a single song. She wrote all of them.",
        "Attention is not free. Attention is architecture.",
        "Listen to everything. Sing what matters.",
    ],
    "The_Starlings_Murmuration": [
        "You become the average of your seven closest influences.",
        "The murmuration has no leader. It has alignment.",
        "Choose your seven. They are choosing your future.",
    ],
    "The_Body_Lie": [
        "Your body has been keeping score while your mind changed the subject.",
        "The truth lives in your posture. Not in your explanation.",
        "Listen to your body. It never learned to lie.",
    ],
    "The_Bonsai_Method": [
        "The cut is not the wound. The cut is the design.",
        "A budget is not restriction. A budget is sculpture.",
        "Prune with intention. Grow with purpose.",
    ],
    "The_Fibonacci_Trim": [
        "Growth without pruning is just accumulation.",
        "The golden ratio is not math. It is nature voting.",
        "Trim to the ratio. Beauty follows structure.",
    ],
    "The_Arrival": [
        "You have been everywhere. You have arrived nowhere.",
        "Presence is not location. Presence is attention.",
        "Arrive. Finally, completely, arrive.",
    ],
    "The_Mycelium_Network": [
        "The most connected organism on Earth has no brain.",
        "The network does not think. The network transfers.",
        "Connect. Transfer. Grow. The forest depends on it.",
    ],
    "The_Termite_Cathedral": [
        "No architect. No blueprint. Just a cathedral.",
        "Emergence does not need a plan. It needs a principle.",
        "Build your piece. The cathedral builds itself.",
    ],
    "The_Bees_Dance": [
        "The dance is the data. The hive is the network.",
        "Communication is not talking. Communication is moving.",
        "Dance your discovery. The hive will follow.",
    ],
    "The_Otters_Play": [
        "Play is not the break from work. Play is the work.",
        "Joy is not the reward. Joy is the method.",
        "Play. The serious ones burn out first.",
    ],
    "The_Butterflys_Crossing": [
        "The crossing is not optional. The wings are.",
        "Transformation costs everything you were.",
        "Cross. What you become is worth what you lose.",
    ],
    "The_Elephants_Ground": [
        "Memory is not nostalgia. Memory is navigation.",
        "The elephant never forgets because forgetting is fatal.",
        "Remember. Your history is your compass.",
    ],
    "The_Whales_Breath": [
        "The deepest dive requires the longest breath.",
        "Silence is not emptiness. Silence is preparation.",
        "Breathe. Then go deeper than anyone expects.",
    ],
    "The_Tide_Pools_Echo": [
        "The edge is where everything interesting lives.",
        "The tide pool survives because it embraces the boundary.",
        "Live at the edge. That is where growth happens.",
    ],
    "Lay_It_Down": [
        "You cannot carry it and be carried by Him.",
        "The altar is not punishment. The altar is freedom.",
        "Lay it down. Walk away lighter.",
    ],
    "Lay_It_Down_Wrath": [
        "Anger is a fire. You are the house.",
        "The rage cycle has one exit. Surrender.",
        "Put down the torch. You are standing in gasoline.",
    ],
    "Lay_It_Down_Envy": [
        "Envy compares your backstage to their highlight reel.",
        "Celebration is the antidote. Not comparison.",
        "Stay in your lane. It was built for you.",
    ],
    "Lay_It_Down_Pride": [
        "The grip feels like strength. It is just fear holding on.",
        "Control is the illusion. Surrender is the power.",
        "Open your hands. See what stays.",
    ],
    "Lay_It_Down_Greed": [
        "Enough was the first word you forgot.",
        "Accumulation is not security. It is anxiety with a lock.",
        "You have enough. Now live like it.",
    ],
    "Lay_It_Down_Sloth": [
        "Stillness chose you. You did not choose it.",
        "Comfort is the slow poison that tastes like rest.",
        "Move. The resistance is the point.",
    ],
    "Lay_It_Down_Gluttony": [
        "The hunger was never in your stomach.",
        "Consumption without purpose is just noise with a receipt.",
        "Fast from the excess. Find what was hiding underneath.",
    ],
    "Lay_It_Down_Lust": [
        "What you chase consumes you before you catch it.",
        "Desire is not the enemy. Disorder is.",
        "Redirect the fire. It was meant to build, not burn.",
    ],
    "Dad_Talks_The_Dopamine_Drought": [
        "Your phone is a slot machine. You are the pigeon.",
        "Every notification is a negotiation for your attention.",
        "Guard your focus. It is the last thing they cannot buy.",
    ],
    "Dad_Talks_The_Mirror_Test": [
        "Someone told you who you were. You believed them.",
        "The mirror shows the outside. Identity lives underneath.",
        "Look again. This time, decide for yourself.",
    ],
    "The_Mantis_Shrimps_Eye": [
        "You see three colors. The mantis shrimp sees sixteen. Every lie you missed happened in a color you could not see.",
        "The apology was sized to his exit, not to her guilt.",
        "You are not broken for having been manipulated. You were operating with three channels in a sixteen channel world.",
    ],
    "The_Porcupines_Quills": [
        "Everything that bites a porcupine only does it once.",
        "The moment defense becomes performance, the predator begins auditioning for exceptions.",
        "You do not have to be harder. You have to build systems that execute in your absence.",
    ],
    "The_Tardigrade_Protocol": [
        "They boiled it. Froze it. Irradiated it. Shot it into space. The tardigrade survived every single one.",
        "That feeling is not accurate information about whether removing it would kill you.",
        "You were not destroyed. You were compressed. The structure was always there. Waiting. Preserved.",
    ],
    "The_Hermit_Crabs_Shell": [
        "You have never lived in your own body. Every identity you have ever worn was borrowed from someone else's back.",
        "The hermit crab has no memory of its own body. It only remembers the shells.",
        "Between the shell you are shedding and the shell you are reaching for, there is a moment where you are just yourself.",
    ],
    "The_Scorpions_Molt": [
        "The armor that protects you is the thing that is killing you. The only way to grow is to become completely soft.",
        "The scorpion does not choose to molt. The body outgrows the armor and the armor must break.",
        "The scorpion is not weaker during the molt. It is growing. The softness is not the vulnerability. It is the expansion.",
    ],
    "The_Vampire_Squids_Light": [
        "You were never a vampire. You were something that learned to survive in the dark and got misnamed by everyone, including yourself.",
        "The vampire squid does not borrow light from the surface. It generates light from its own body, in the deepest dark.",
        "A creature from the deep dark wrote a letter in sunlight and did not burst into flames.",
    ],
    "The_Cuttlefishs_Canvas": [
        "The cuttlefish does not see color. She becomes it.",
        "Diffusion does not create an image. It discovers one that was always hiding in the noise.",
        "You will never look at an AI image the same way. You will see the noise it started from.",
    ],
    "The_Centipedes_March": [
        "One image is a canvas. A hundred images in sequence is a march.",
        "The centipede does not plan the next hundred steps. It plans the next one, perfectly, a hundred times.",
        "Video is not a movie played fast. It is a prediction sustained.",
    ],
    "The_Lyrebirds_Echo": [
        "Every song in the forest lives inside one bird. She did not write any of them.",
        "The model does not compose music. It subtracts noise until music remains.",
        "You typed a sentence. Thirty seconds later, a song played back. Now you know how.",
    ],
}


# ---------------------------------------------------------------------------
# TITLE EXTRACTION
# ---------------------------------------------------------------------------
def extract_title(html: str, filename: str) -> str:
    m = re.search(r'<title>([^<]+)</title>', html)
    if m:
        title = m.group(1)
        for suffix in [". Kingdom Builders AI", " | Kingdom Builders", " - Kingdom Builders"]:
            title = title.replace(suffix, "")
        title = title.strip().rstrip(".")
        if title and len(title) < 60:
            return title
    name = filename.replace(".html", "").replace("_", " ")
    return name


def stem_to_display(stem: str) -> str:
    name = stem.replace("_Modified", "")
    return name.replace("_", " ")


# ---------------------------------------------------------------------------
# HTML TEMPLATE — Condensed cover + quote
# ---------------------------------------------------------------------------
def build_pull_quote_html(
    playbook_html: str,
    title: str,
    quote: str,
    width: int,
    height: int,
) -> str:
    """
    Build a self-contained HTML page that renders the cover design condensed
    into the top portion, with the quote displayed below the title.

    Strategy: Extract the <style> and cover section from the playbook HTML,
    then render a condensed version with the quote underneath.
    """
    # Extract all <style> blocks
    styles = re.findall(r'<style[^>]*>(.*?)</style>', playbook_html, re.DOTALL)
    combined_css = "\n".join(styles)

    # Extract Google Fonts link
    font_links = re.findall(r'<link[^>]+fonts\.googleapis\.com[^>]+>', playbook_html)
    font_html = "\n".join(font_links)

    # Extract cover inner HTML — handle cover-content, cover-wrap, or direct children
    cover_inner = ""
    for cls in ['cover-content', 'cover-wrap', 'cover-inner']:
        m = re.search(
            rf'<div\s+class="{cls}"[^>]*>(.*)</div>\s*</(?:section|div)>',
            playbook_html,
            re.DOTALL,
        )
        if m:
            cover_inner = m.group(1).strip()
            break
    if not cover_inner:
        # Fallback: extract everything inside the cover section/div
        m = re.search(
            r'<(?:section|div)\s+class="cover"[^>]*>(.*)</(?:section|div)>',
            playbook_html,
            re.DOTALL,
        )
        if m:
            cover_inner = m.group(1).strip()
    if not cover_inner:
        cover_inner = f"<h1>{title}</h1>"

    # Remove the tagline and author from cover (keep badge + title + art/icon)
    cover_inner = re.sub(r'<p\s+class="cover-tagline"[^>]*>.*?</p>', '', cover_inner, flags=re.DOTALL)
    cover_inner = re.sub(r'<p\s+class="cover-author"[^>]*>.*?</p>', '', cover_inner, flags=re.DOTALL)
    cover_inner = re.sub(r'<p\s+class="cover-sub"[^>]*>.*?</p>', '', cover_inner, flags=re.DOTALL)

    # Extract SVG <defs> block (symbol definitions for <use href> icons)
    # Extract SVG symbol/defs blocks — two patterns:
    # 1. <svg><defs>...</defs></svg>  (standalone defs block)
    # 2. <svg style="display:none"><symbol>...</symbol></svg>  (hidden symbol sprite)
    svg_defs_parts = []
    # Pattern 1: <svg><defs>...</defs></svg>
    for m in re.finditer(r'<svg[^>]*>\s*<defs>(.*?)</defs>\s*</svg>', playbook_html, re.DOTALL):
        svg_defs_parts.append(f'<defs>{m.group(1)}</defs>')
    # Pattern 2: <svg style="display:none">..symbols..</svg>
    for m in re.finditer(r'<svg[^>]*style="display:\s*none"[^>]*>(.*?)</svg>', playbook_html, re.DOTALL):
        svg_defs_parts.append(m.group(1))
    # Pattern 3: <svg ...><defs>...symbols...</defs> (inside larger hidden svg)
    for m in re.finditer(r'<svg[^>]*>\s*\n?\s*<defs>\s*\n?\s*(?=.*<symbol)', playbook_html, re.DOTALL):
        # Already captured by pattern 1/2
        pass
    svg_defs_html = f'<svg style="display:none">{"".join(svg_defs_parts)}</svg>' if svg_defs_parts else ""

    # Detect the heading font family from CSS
    heading_font_match = re.search(r'h1[^{]*\{[^}]*font-family:\s*([^;]+)', combined_css)
    heading_font = heading_font_match.group(1).strip().rstrip(';') if heading_font_match else "'Poppins', sans-serif"

    # Detect cover background from CSS
    cover_bg_match = re.search(r'\.cover\s*\{[^}]*background:\s*([^;]+)', combined_css)
    cover_bg = cover_bg_match.group(1).strip().rstrip(';') if cover_bg_match else "linear-gradient(165deg, #0E0618 0%, #1A0A2E 30%, #2D1B4E 70%, #1A0A2E 100%)"

    # Detect accent/gold color — try multiple variable names
    gold_color = "#D4A843"
    for var_name in ['--gold-glow', '--gold', '--amber-glow', '--amber', '--ember',
                     '--compass-gold', '--fire', '--teal', '--rust-bright']:
        gm = re.search(var_name.replace('-', r'\-') + r'\s*:\s*(#[0-9A-Fa-f]+)', combined_css)
        if gm:
            gold_color = gm.group(1)
            break

    # Ensure accent color is bright enough for dark backgrounds (min luminance)
    def _brighten(hex_color: str, min_lum: int = 140) -> str:
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        lum = r * 0.299 + g * 0.587 + b * 0.114
        if lum < min_lum:
            factor = min_lum / max(lum, 1)
            r = min(int(r * factor), 255)
            g = min(int(g * factor), 255)
            b = min(int(b * factor), 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    gold_color = _brighten(gold_color)

    # Detect serif font for quote
    serif_match = re.search(r"font-family:\s*'(Lora|Cormorant|Playfair|EB Garamond|Merriweather)[^']*'", combined_css)
    serif_font = f"'{serif_match.group(1)}'" if serif_match else "'Lora'"

    # Escape quote for HTML
    quote_html = quote.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    is_wide = width > height

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
{font_html}
<style>
{combined_css}

/* ===== PULL QUOTE OVERRIDES ===== */
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{
    width: {width}px;
    height: {height}px;
    overflow: hidden;
}}

.pq-wrapper {{
    width: {width}px;
    height: {height}px;
    background: {cover_bg};
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    position: relative;
    overflow: hidden;
}}

/* Radial glow effect */
.pq-wrapper::before {{
    content: '';
    position: absolute;
    top: {'15%' if not is_wide else '10%'};
    left: 50%;
    transform: translate(-50%, -50%);
    width: {'520px' if not is_wide else '600px'};
    height: {'520px' if not is_wide else '400px'};
    background: radial-gradient(circle, rgba(212,168,67,0.06) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}}

/* Vignette */
.pq-wrapper::after {{
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.4) 100%);
    pointer-events: none;
}}

.pq-content {{
    position: relative;
    z-index: 2;
    padding: {'40px 70px' if not is_wide else '24px 70px'};
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: {'14px' if not is_wide else '10px'};
}}

/* Condensed cover section — badge + art + title */
.pq-cover {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: {'6px' if not is_wide else '4px'};
}}

.pq-cover .cover-badge {{
    display: inline-block;
    padding: 5px 16px;
    border: 1px solid rgba(212,168,67,0.25);
    border-radius: 50px;
    font-family: {heading_font};
    font-size: {'11px' if not is_wide else '10px'};
    font-weight: 600;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: {gold_color};
    margin-bottom: 0;
}}

.pq-cover h1 {{
    font-family: {heading_font};
    font-size: {'clamp(1.6rem, 4vw, 2.2rem)' if not is_wide else 'clamp(1.3rem, 3vw, 1.8rem)'};
    font-weight: 300;
    color: #FFFFFF;
    line-height: 1.15;
    margin: 0;
}}

.pq-cover h1 strong,
.pq-cover h1 span,
.pq-cover h1 em {{
    font-weight: 700;
    font-style: normal;
    color: {gold_color};
    display: block;
}}

/* Decorative separator */
.pq-separator {{
    width: 120px;
    height: 1px;
    background: linear-gradient(90deg, transparent, {gold_color}55, transparent);
    position: relative;
}}
.pq-separator::after {{
    content: '';
    position: absolute;
    top: -2px;
    left: 50%;
    transform: translateX(-50%);
    width: 5px;
    height: 5px;
    background: {gold_color}55;
    border-radius: 50%;
}}

/* Quote text */
.pq-quote {{
    font-family: {serif_font}, Georgia, serif;
    font-size: {'clamp(1.4rem, 3.5vw, 2rem)' if not is_wide else 'clamp(1.1rem, 2.5vw, 1.5rem)'};
    font-weight: 400;
    font-style: italic;
    color: rgba(255,255,255,0.92);
    line-height: 1.55;
    max-width: {'700px' if not is_wide else '900px'};
    text-shadow: 0 2px 8px rgba(0,0,0,0.3);
}}

/* Brand watermark */
.pq-brand {{
    position: absolute;
    bottom: {'28px' if not is_wide else '18px'};
    left: 50%;
    transform: translateX(-50%);
    font-family: {heading_font};
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.15);
    z-index: 3;
}}

/* Hide animated bg elements that clutter — keep cover-art SVGs */
.cover-acorn, .leaf, .firefly, .star,
.ghost-frame-anim, .cover-frame-reveal, .cover-pulse,
.gravity-ring, .orbit-particle, .gravity-core,
.cover-stars, .cover-compass, .particle, .ghost-noise {{ display: none !important; }}

/* Cover art — as large as possible without overlapping text */
.pq-cover .cover-art {{
    margin-bottom: {'12px' if not is_wide else '8px'};
    flex-shrink: 0;
}}
.pq-cover .cover-art svg {{
    width: {'280px' if not is_wide else '200px'};
    max-height: {'280px' if not is_wide else '180px'};
    object-fit: contain;
    filter: drop-shadow(0 0 24px rgba(212,168,67,0.25));
}}

/* Cover icon (emoji or SVG symbol) */
.pq-cover .cover-icon {{
    display: block;
    margin-bottom: {'8px' if not is_wide else '4px'};
    font-size: {'5rem' if not is_wide else '3.5rem'};
    line-height: 1;
    animation: none !important;
}}
.pq-cover .cover-icon .ico {{
    width: {'100px' if not is_wide else '70px'};
    height: {'100px' if not is_wide else '70px'};
    stroke-width: 1.5;
    color: {gold_color};
    display: inline-block;
    fill: none;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
}}

</style>
</head>
<body>
{svg_defs_html}
<div class="pq-wrapper">
    <div class="pq-content">
        <div class="pq-cover">
            <span class="cover-badge">Kingdom Builders AI</span>
            {_extract_cover_art(cover_inner)}
            <h1>{_extract_h1_inner(cover_inner, title)}</h1>
        </div>
        <div class="pq-separator"></div>
        <div class="pq-quote">&ldquo;{quote_html}&rdquo;</div>
    </div>
    <div class="pq-brand">KingdomBuilders.ai</div>
</div>
</body>
</html>"""


def _extract_h1_inner(cover_inner: str, fallback_title: str) -> str:
    """Extract just the inner HTML of the h1 tag from the cover content."""
    m = re.search(r'<h1[^>]*>(.*?)</h1>', cover_inner, re.DOTALL)
    if m:
        return m.group(1).strip()
    return fallback_title


def _extract_cover_art(cover_inner: str) -> str:
    """Extract any cover-art div (with SVG) or cover-icon span from the cover content."""
    # Pattern 1: <div class="cover-art">...<svg>...</svg></div>
    art_match = re.search(
        r'<div\s+class="cover-art"[^>]*>.*?</svg>\s*</div>',
        cover_inner,
        re.DOTALL,
    )
    if art_match:
        return art_match.group(0)
    # Pattern 2: <div class="cover-art">...</div> (simpler, no svg tag)
    art_match2 = re.search(r'<div\s+class="cover-art"[^>]*>.*?</div>', cover_inner, re.DOTALL)
    if art_match2:
        return art_match2.group(0)
    # Pattern 3: <svg class="cover-art" ...>...</svg> (SVG element IS the cover-art)
    svg_art = re.search(r'<svg\s+[^>]*class="cover-art"[^>]*>.*?</svg>', cover_inner, re.DOTALL)
    if svg_art:
        return f'<div class="cover-art">{svg_art.group(0)}</div>'
    # Pattern 4: Other art class names (mound-art, crab-icon, etc.)
    other_art = re.search(
        r'<(?:div|svg)\s+[^>]*class="(?:mound|crab|cover)-(?:art|icon)"[^>]*>.*?</(?:div|svg)>',
        cover_inner,
        re.DOTALL,
    )
    if other_art:
        return f'<div class="cover-art">{other_art.group(0)}</div>'
    # Pattern 5: cover-icon (emoji or SVG symbol)
    icon_match = re.search(r'<span\s+class="cover-icon"[^>]*>.*?</span>', cover_inner, re.DOTALL)
    if icon_match:
        return icon_match.group(0)
    return ""


# ---------------------------------------------------------------------------
# IMAGE GENERATION
# ---------------------------------------------------------------------------
def generate_images_for_playbook(
    page,
    filepath: Path,
    playbook_html: str,
    title: str,
    quotes: list,
    display_name: str,
) -> list:
    """Generate all 6 images (3 quotes x 2 sizes) for one playbook."""
    outputs = []

    for idx, quote in enumerate(quotes, 1):
        for size, suffix in [(SQUARE, ""), (WIDE, " wide")]:
            w, h = size
            html_content = build_pull_quote_html(playbook_html, title, quote, w, h)

            # Set viewport to exact size
            page.set_viewport_size({"width": w, "height": h})
            page.set_content(html_content, wait_until="networkidle")

            # Small wait for fonts to load
            page.wait_for_timeout(500)

            out_path = OUTPUT_DIR / f"{display_name} {idx}{suffix}.png"
            page.screenshot(path=str(out_path), type="png")
            outputs.append(out_path)

    return outputs


# ---------------------------------------------------------------------------
# FILE PROCESSING
# ---------------------------------------------------------------------------
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

    # Determine which playbooks to process
    if len(sys.argv) > 1:
        targets = []
        for arg in sys.argv[1:]:
            target = ASSETS_DIR / arg
            if not target.exists():
                target = ASSETS_DIR / (arg + ".html")
            if not target.exists():
                print(f"  NOT FOUND: {arg}")
            else:
                targets.append(target)
    else:
        targets = get_active_playbooks()

    if not targets:
        print("No playbooks to process.")
        return

    print(f"Processing {len(targets)} playbook(s)...\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()

        total = 0
        for i, filepath in enumerate(targets, 1):
            stem = filepath.stem
            display_name = stem_to_display(stem)
            quotes = CURATED_QUOTES.get(stem)

            if not quotes:
                print(f"  [{i:2d}/{len(targets)}] {stem}... SKIP (no quotes)")
                continue

            print(f"  [{i:2d}/{len(targets)}] {stem}...", end=" ", flush=True)
            try:
                html = filepath.read_text(encoding="utf-8", errors="replace")
                title = extract_title(html, filepath.name)
                results = generate_images_for_playbook(
                    page, filepath, html, title, quotes, display_name,
                )
                total += len(results)
                print(f"OK ({len(results)} images)")
            except Exception as e:
                print(f"ERROR: {e}")

        browser.close()

    print(f"\nDone. {total} images saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
