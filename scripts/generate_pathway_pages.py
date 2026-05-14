"""Generate rich pathway detail pages matching the work-reset template.

For each step card, pull live data from disk:
- Title from playbook_registry → asset HTML's <h1>
- Tagline from the playbook's <p class="cover-tagline">
- Series + position from series_definitions
- Chapter count from the playbook's <h2> elements
- Free/paid status from FREE_SLUGS
"""
import re
import sys
import os

sys.path.insert(0, '.')
from pathway_definitions import PATHWAYS
from playbook_registry import SLUG_TO_FILE
from series_definitions import (
    SERIES_DISPLAY_NAME,
    get_series_position,
)

ASSETS_DIR = "assets"

# Mirror api/routers/legacy.py FREE_SLUGS
FREE_SLUGS = {
    "conductors-playbook",
    "lay-it-down",
    "the-mockingbirds-song",
    "the-lifted-ceiling",
    "the-tide-pools-echo",
    "dad-talks-the-dopamine-drought",
    "the-mantis-shrimps-eye",
    "the-hermit-crabs-shell",
}

ACCENTS = {
    'work-reset':         ('#1A2030', '#3D4670', '#7A6020', '#D4A843', '#8A6B20', '#F5E0A8'),
    'identity-walk':      ('#0A0612', '#1A0E2E', '#5B2FA0', '#7B4FBF', '#5B2FA0', '#D8C8F0'),
    'ai-age':             ('#040810', '#0A1E2E', '#1F7A7A', '#00A8A8', '#006666', '#B8E8E8'),
    'money-architecture': ('#040A06', '#0A1E14', '#2D8A4E', '#3DAE6E', '#1E5D34', '#C8F0D0'),
    'resilience-stack':   ('#0A0604', '#1E1408', '#A06530', '#C97A2C', '#7A4A18', '#F0D8B8'),
    'inner-battle':       ('#0A0408', '#1E0A14', '#7A2842', '#A13C5A', '#7A2842', '#F0C8D0'),
    'family-foundation':  ('#0A0604', '#1E0E08', '#C25840', '#E07A5F', '#A04830', '#F0D0C8'),
    'strategist-toolkit': ('#040810', '#0A1422', '#4A6B8A', '#6E8FA8', '#2A4866', '#C8D8E8'),
    'process-model':      ('#040A04', '#0E1A0E', '#1E3A1E', '#5A7A4E', '#3A5530', '#D0E5C8'),
}

COUNT_WORDS = {3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight'}


def _read_asset(slug: str) -> str:
    fname = SLUG_TO_FILE.get(slug)
    if not fname:
        return ""
    path = os.path.join(ASSETS_DIR, fname)
    if not os.path.isfile(path):
        return ""
    with open(path, encoding='utf-8') as f:
        return f.read()


def _strip(html_fragment: str) -> str:
    # Insert a space at every tag boundary so adjacent block children
    # (e.g. <h1>Lay It Down<strong>I Am Calling You Deeper</strong></h1>)
    # don't collapse into one word when tags are removed.
    s = re.sub(r'<[^>]+>', ' ', html_fragment)
    return re.sub(r'\s+', ' ', s).strip()


def extract_playbook_meta(slug: str) -> dict:
    """Pull title, tagline, quote, chapter count from the asset HTML."""
    html = _read_asset(slug)
    if not html:
        return {
            "title": slug.replace('-', ' ').title(),
            "tagline": "",
            "quote": "",
            "chapters": 0,
        }

    title_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, flags=re.DOTALL | re.IGNORECASE)
    title = _strip(title_m.group(1)) if title_m else slug.replace('-', ' ').title()

    # Tagline lives under several class names depending on when the
    # playbook was authored. Try the common variants in priority order.
    tagline = ""
    for cls in ("cover-tagline", "cover-sub", "cover-subtitle", "cover-description"):
        m = re.search(
            rf'<(?:p|div)[^>]*class="[^"]*\b{cls}\b[^"]*"[^>]*>(.*?)</(?:p|div)>',
            html, flags=re.DOTALL | re.IGNORECASE,
        )
        if m:
            tagline = _strip(m.group(1))
            if tagline:
                break
    if len(tagline) > 200:
        tagline = tagline[:197] + "..."

    # Try to find a quotable line: a blockquote, otherwise a styled emphasized line
    quote = ""
    bq_m = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', html, flags=re.DOTALL | re.IGNORECASE)
    if bq_m:
        quote = _strip(bq_m.group(1))
    if not quote:
        # Many playbooks use a class like "pull-quote" / "callout" / "breakthrough"
        for cls in ("pull-quote", "breakthrough", "callout-quote", "key-line", "anchor-quote"):
            m = re.search(
                rf'<(?:p|div|aside)[^>]*class="[^"]*{cls}[^"]*"[^>]*>(.*?)</(?:p|div|aside)>',
                html, flags=re.DOTALL | re.IGNORECASE,
            )
            if m:
                quote = _strip(m.group(1))
                break
    # Strip any wrapping quote characters (smart or straight) so the template
    # can apply its own quote glyphs without producing "" stutters.
    quote = quote.strip().strip('"').strip('“”').strip()
    if quote and len(quote) > 240:
        quote = quote[:237] + "..."

    # Don't show the quote if it is just the tagline restated.
    def _norm(s: str) -> str:
        return re.sub(r'[^a-z0-9]+', '', s.lower())
    if quote and tagline and (_norm(quote) == _norm(tagline) or _norm(quote) in _norm(tagline) or _norm(tagline) in _norm(quote)):
        quote = ""

    return {
        "title": title,
        "tagline": tagline,
        "quote": quote,
    }


def step_card(slug: str, step_num: int, accent: dict) -> str:
    meta = extract_playbook_meta(slug)
    series_info = get_series_position(slug)
    if series_info:
        series_slug, pos, total = series_info
        series_name = SERIES_DISPLAY_NAME.get(series_slug, series_slug)
        step_num_label = f"Step {step_num:02d} &middot; {series_name} &middot; Part {pos} of {total}"
    else:
        step_num_label = f"Step {step_num:02d}"

    is_free = slug in FREE_SLUGS
    price_label = '<span class="free">Free</span>' if is_free else '<span>$2.50</span>'

    tagline_block = (
        f'<div class="step-sub">{meta["tagline"]}</div>' if meta["tagline"] else ""
    )
    quote_block = (
        f'<p class="step-quote">&ldquo;{meta["quote"]}&rdquo;</p>' if meta["quote"] else ""
    )

    return f"""    <a href="/playbooks/read/{slug}" class="step">
      <div class="step-banner">
        <div class="step-banner-left">
          <div class="step-num">{step_num_label}</div>
          <div class="step-name">{meta["title"]}</div>
          {tagline_block}
        </div>
      </div>
      <div class="step-body">
        {quote_block}
        <div class="step-footer">
          <div class="step-meta"><span>~30 min</span><span class="dot"></span>{price_label}</div>
          <div class="step-action">Open Step {step_num:02d} &rarr;</div>
        </div>
      </div>
    </a>"""


def build_page(p: dict) -> str:
    acc1, acc2, acc3, acc4, acc5, acc6 = ACCENTS[p['slug']]
    steps = [step_card(slug, i, {'a': acc1}) for i, slug in enumerate(p['playbook_sequence'], 1)]
    count_word = COUNT_WORDS.get(len(p['playbook_sequence']), 'Several')
    scripture = p.get('scripture', '').replace('"', '')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{p['name']} | Pathways | Kingdom Builders AI</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Lora:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{
  --night:#0E0F1A;--dawn:#1F2440;--sky:#3D4670;
  --gold:#D4A843;--gold-glow:#E8C96A;--gold-pale:#F5E0A8;
  --cream:#FDFAF3;--cream-warm:#F5EFE0;--cream-deep:#ECE5CC;
  --text:#1A1A26;--text-light:#4A4E5E;--text-muted:#7A7E8E;--white:#FFFFFF;
  --shadow-soft:0 2px 12px rgba(14,15,26,0.06);--shadow-mid:0 8px 32px rgba(14,15,26,0.14);
  --accent:{acc4};--accent-deep:{acc5};--accent-pale:{acc6};--accent-soft:rgba(212,168,67,0.10);
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Lora',Georgia,serif;color:var(--text);background:var(--cream);line-height:1.65;font-size:17px}}
.topnav{{position:absolute;top:0;left:0;right:0;display:flex;align-items:center;padding:18px 36px;z-index:50;gap:32px}}
.topnav .brand{{font-family:'Poppins',sans-serif;font-size:0.7rem;font-weight:700;letter-spacing:5px;text-transform:uppercase;color:rgba(245,224,168,0.85);text-decoration:none;flex-shrink:0}}
.topnav-primary{{display:flex;gap:8px;flex:1}}
.topnav-primary a{{font-family:'Poppins',sans-serif;font-size:0.72rem;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:rgba(245,224,168,0.55);text-decoration:none;padding:8px 14px;border-radius:30px}}
.topnav-primary a.active{{color:var(--gold-glow);background:rgba(245,224,168,0.10)}}
.topnav-utility{{display:flex;gap:10px;align-items:center;flex-shrink:0}}
.topnav-utility .nav-link{{font-family:'Poppins',sans-serif;font-size:0.7rem;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:rgba(245,224,168,0.6);text-decoration:none;padding:8px 14px}}
.topnav-utility .nav-button{{font-family:'Poppins',sans-serif;font-size:0.7rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--dawn);background:linear-gradient(135deg,var(--gold),var(--gold-glow));text-decoration:none;padding:9px 20px;border-radius:50px;box-shadow:0 2px 12px rgba(212,168,67,0.32)}}

.hero{{background:linear-gradient(170deg,{acc1} 0%,{acc2} 30%,{acc3} 70%,{acc5} 100%);padding:120px 24px 100px;text-align:center;position:relative;overflow:hidden}}
.hero-content{{position:relative;z-index:2;max-width:780px;margin:0 auto}}
.hero-breadcrumb{{font-family:'Poppins',sans-serif;font-size:0.6rem;font-weight:700;letter-spacing:4px;text-transform:uppercase;color:rgba(245,224,168,0.55);margin-bottom:16px}}
.hero-breadcrumb a{{color:rgba(245,224,168,0.7);text-decoration:none}}
.hero h1{{font-family:'Nunito',sans-serif;font-size:clamp(2.8rem,7vw,4.6rem);font-weight:900;color:var(--gold-glow);line-height:1.04;letter-spacing:-0.03em;margin-bottom:6px}}
.hero-tagline{{font-family:'Nunito',sans-serif;font-size:1.15rem;font-weight:700;color:var(--accent-pale);margin-bottom:24px}}
.hero-audience{{font-family:'Lora',serif;font-size:1.05rem;font-style:italic;color:rgba(255,255,255,0.62);max-width:560px;margin:0 auto 16px;line-height:1.6}}
.hero-promise{{display:inline-block;padding:14px 28px;background:rgba(245,224,168,0.08);border:1px solid rgba(245,224,168,0.22);border-radius:14px;font-family:'Lora',serif;font-size:0.95rem;font-style:italic;color:var(--gold-pale);margin-top:18px;max-width:580px}}

.path-wrap{{max-width:1240px;margin:64px auto 0;padding:0 24px 60px}}
.path-intro{{text-align:center;margin-bottom:40px}}
.path-intro-kicker{{font-family:'Poppins',sans-serif;font-size:0.6rem;font-weight:700;letter-spacing:5px;text-transform:uppercase;color:var(--accent-deep);margin-bottom:8px}}
.path-intro h2{{font-family:'Nunito',sans-serif;font-size:1.85rem;font-weight:800;color:var(--dawn);letter-spacing:-0.02em;line-height:1.15}}
.path-intro p{{font-family:'Lora',serif;font-size:1rem;font-style:italic;color:var(--text-light);max-width:560px;margin:10px auto 0}}
.path-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:24px}}

.step{{background:var(--white);border-radius:20px;overflow:hidden;box-shadow:var(--shadow-mid);border:1px solid var(--cream-deep);text-decoration:none;color:inherit;display:flex;flex-direction:column;transition:all 0.4s}}
.step:hover{{transform:translateY(-4px);box-shadow:0 16px 60px rgba(14,15,26,0.18);border-color:rgba(212,168,67,0.35)}}
.step-banner{{padding:24px 26px 22px;background:linear-gradient(160deg,{acc1} 0%,{acc2} 50%,{acc3} 100%);position:relative;overflow:hidden}}
.step-banner::before{{content:'';position:absolute;top:-40%;right:-12%;width:280px;height:280px;background:radial-gradient(circle,rgba(245,224,168,0.16) 0%,transparent 65%);border-radius:50%;pointer-events:none}}
.step-banner-left{{position:relative;z-index:2}}
.step-num{{font-family:'Poppins',sans-serif;font-size:0.58rem;font-weight:800;letter-spacing:3.5px;text-transform:uppercase;color:var(--accent-pale);margin-bottom:8px;opacity:0.85;line-height:1.4}}
.step-name{{font-family:'Nunito',sans-serif;font-size:1.4rem;font-weight:900;color:var(--white);letter-spacing:-0.015em;line-height:1.18;margin-bottom:8px}}
.step-sub{{font-family:'Lora',serif;font-style:italic;font-size:0.95rem;color:rgba(255,255,255,0.78);line-height:1.45}}
.step-body{{padding:22px 26px 20px;display:flex;flex-direction:column;flex:1}}
.step-quote{{font-family:'Lora',serif;font-size:1rem;font-style:italic;color:var(--text-light);line-height:1.55;padding-left:14px;border-left:3px solid var(--accent);margin-bottom:18px;flex:1}}
.step-footer{{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:auto}}
.step-meta{{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-family:'Poppins',sans-serif;font-size:0.7rem;font-weight:600;color:var(--text-muted);letter-spacing:0.3px}}
.step-meta .dot{{width:3px;height:3px;border-radius:50%;background:var(--text-muted);opacity:0.5}}
.step-meta .free{{color:#1E7E34;font-weight:700}}
.step-action{{display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:50px;font-family:'Poppins',sans-serif;font-size:0.76rem;font-weight:700;letter-spacing:0.3px;color:var(--accent-deep);border:1.5px solid var(--cream-deep);white-space:nowrap}}
.step:hover .step-action{{border-color:var(--accent);background:var(--accent-soft)}}
footer{{background:var(--night);color:rgba(255,255,255,0.4);padding:48px 24px 36px;text-align:center;margin-top:80px}}
footer p{{font-family:'Lora',serif;font-size:0.85rem;font-style:italic;color:rgba(245,224,168,0.4);margin-bottom:14px;max-width:540px;margin-left:auto;margin-right:auto}}
footer .brand-mark{{font-family:'Poppins',sans-serif;font-size:0.55rem;letter-spacing:5px;text-transform:uppercase;color:rgba(255,255,255,0.18)}}
@media(max-width:680px){{.topnav{{padding:14px 18px;gap:16px}}.topnav-primary,.topnav-utility .nav-link{{display:none}}.hero{{padding:90px 20px 80px}}.path-wrap{{padding:0 16px 56px}}.step-footer{{flex-direction:column;align-items:flex-start}}}}
</style>
</head>
<body>

<nav class="topnav">
  <a href="/playbooks/" class="brand">Kingdom Builders AI</a>
  <div class="topnav-primary">
    <a href="/playbooks/" class="active">Pathways</a>
    <a href="/playbooks/archive">Archive</a>
  </div>
  <div class="topnav-utility">
    <a href="/playbooks/referrals" class="nav-link">Refer</a>
    <a href="/playbooks/auth" class="nav-button">Sign In</a>
  </div>
</nav>

<section class="hero">
  <div class="hero-content">
    <div class="hero-breadcrumb"><a href="/playbooks/">Pathways</a> &nbsp;&middot;&nbsp; Pathway {p['order']:02d}</div>
    <h1>{p['name']}</h1>
    <div class="hero-tagline">{p['tagline']}</div>
    <p class="hero-audience">{p['audience']}</p>
    <div class="hero-promise"><strong>The promise:</strong> {p['promise']}</div>
  </div>
</section>

<div class="path-wrap">
  <div class="path-intro">
    <div class="path-intro-kicker">The {count_word} Steps</div>
    <h2>Walk them in order. Skip what you have already walked through.</h2>
    <p>Each step is a self-contained playbook. The pathway is the recommended order, not a lock.</p>
  </div>

  <div class="path-grid">
{chr(10).join(steps)}
  </div>
</div>

<footer>
  <p>{scripture}</p>
  <div class="brand-mark">Kingdom Builders AI &middot; Pathway {p['order']:02d} of 09</div>
</footer>

</body>
</html>
"""


if __name__ == "__main__":
    for p in PATHWAYS:
        if p['slug'] == 'work-reset':
            continue
        out_path = f"static/pathways/{p['slug']}.html"
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(build_page(p))
        print(f"Wrote {out_path}")
    print(f"\nAll {len(PATHWAYS)} pathways regenerated.")
