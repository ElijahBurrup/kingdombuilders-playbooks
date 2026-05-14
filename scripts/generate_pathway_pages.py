"""Generate stub pathway detail pages for all pathways except Work Reset
(which has the full custom template). Each gets a clean list page.
"""
import re
import sys
import os

sys.path.insert(0, '.')
from pathway_definitions import PATHWAYS
from playbook_registry import SLUG_TO_FILE

# Extract playbook titles from the archive backup catalog
with open('static/archive-original.html.bak', encoding='utf-8') as f:
    cat = f.read()
pb_titles = {}
for m in re.finditer(
    r'<a href="read/([\w-]+)"[\s\S]*?class="card-title">([^<]+)</div>', cat
):
    pb_titles[m.group(1)] = m.group(2).strip()

ACCENTS = {
    'work-reset':       ('#1A2030', '#3D4670', '#7A6020', '#D4A843', '#8A6B20', '#F5E0A8'),
    'identity-walk':    ('#0A0612', '#1A0E2E', '#5B2FA0', '#7B4FBF', '#5B2FA0', '#D8C8F0'),
    'ai-age':           ('#040810', '#0A1E2E', '#1F7A7A', '#00A8A8', '#006666', '#B8E8E8'),
    'money-architecture': ('#040A06', '#0A1E14', '#2D8A4E', '#3DAE6E', '#1E5D34', '#C8F0D0'),
    'resilience-stack': ('#0A0604', '#1E1408', '#A06530', '#C97A2C', '#7A4A18', '#F0D8B8'),
    'inner-battle':     ('#0A0408', '#1E0A14', '#7A2842', '#A13C5A', '#7A2842', '#F0C8D0'),
    'family-foundation': ('#0A0604', '#1E0E08', '#C25840', '#E07A5F', '#A04830', '#F0D0C8'),
    'strategist-toolkit': ('#040810', '#0A1422', '#4A6B8A', '#6E8FA8', '#2A4866', '#C8D8E8'),
    'process-model':    ('#040A04', '#0E1A0E', '#1E3A1E', '#5A7A4E', '#3A5530', '#D0E5C8'),
}

COUNT_WORDS = {3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight'}

STEP_TEMPLATE = '''    <a href="/playbooks/read/{slug}" class="step">
      <div class="step-banner">
        <div class="step-banner-left">
          <div class="step-num">Step {step_num:02d}</div>
          <div class="step-name">{title}</div>
        </div>
      </div>
      <div class="step-body">
        <p class="step-quote">Step {step_num} of the {pathway_name} pathway.</p>
        <span class="step-action">Open Step {step_num:02d} &rarr;</span>
      </div>
    </a>'''


def build_page(p):
    acc1, acc2, acc3, acc4, acc5, acc6 = ACCENTS[p['slug']]
    steps = []
    for i, slug in enumerate(p['playbook_sequence'], 1):
        title = pb_titles.get(slug, slug.replace('-', ' ').title())
        steps.append(STEP_TEMPLATE.format(
            slug=slug, step_num=i, title=title, pathway_name=p['name']
        ))
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
.path-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:22px}}

.step{{background:var(--white);border-radius:20px;overflow:hidden;box-shadow:var(--shadow-mid);border:1px solid var(--cream-deep);text-decoration:none;color:inherit;display:block;transition:all 0.4s}}
.step:hover{{transform:translateY(-4px);box-shadow:0 16px 60px rgba(14,15,26,0.18);border-color:rgba(212,168,67,0.35)}}
.step-banner{{padding:22px 26px 20px;background:linear-gradient(160deg,{acc1} 0%,{acc2} 50%,{acc3} 100%);display:flex;justify-content:space-between;align-items:flex-start;position:relative;overflow:hidden}}
.step-banner::before{{content:'';position:absolute;top:-40%;right:-12%;width:280px;height:280px;background:radial-gradient(circle,rgba(245,224,168,0.16) 0%,transparent 65%);border-radius:50%;pointer-events:none}}
.step-banner-left{{position:relative;z-index:2;flex:1}}
.step-num{{font-family:'Poppins',sans-serif;font-size:0.58rem;font-weight:800;letter-spacing:3.5px;text-transform:uppercase;color:var(--accent-pale);margin-bottom:6px;opacity:0.85}}
.step-name{{font-family:'Nunito',sans-serif;font-size:1.35rem;font-weight:900;color:var(--white);letter-spacing:-0.015em;line-height:1.18}}
.step-body{{padding:20px 26px}}
.step-quote{{font-family:'Lora',serif;font-size:1rem;font-style:italic;color:var(--text-light);line-height:1.55;padding-left:14px;border-left:3px solid var(--accent);margin-bottom:14px}}
.step-action{{display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:50px;font-family:'Poppins',sans-serif;font-size:0.76rem;font-weight:700;letter-spacing:0.3px;color:var(--accent-deep);border:1.5px solid var(--cream-deep)}}
.step:hover .step-action{{border-color:var(--accent);background:var(--accent-soft)}}
.coming-soon-note{{max-width:760px;margin:48px auto 0;padding:20px 28px;background:rgba(212,168,67,0.06);border:1px dashed rgba(212,168,67,0.3);border-radius:14px;text-align:center;font-family:'Lora',serif;font-style:italic;color:var(--text-light);font-size:0.95rem}}
.coming-soon-note strong{{color:var(--accent-deep);font-style:normal;font-weight:700}}
footer{{background:var(--night);color:rgba(255,255,255,0.4);padding:48px 24px 36px;text-align:center;margin-top:80px}}
footer p{{font-family:'Lora',serif;font-size:0.85rem;font-style:italic;color:rgba(245,224,168,0.4);margin-bottom:14px;max-width:540px;margin-left:auto;margin-right:auto}}
footer .brand-mark{{font-family:'Poppins',sans-serif;font-size:0.55rem;letter-spacing:5px;text-transform:uppercase;color:rgba(255,255,255,0.18)}}
@media(max-width:680px){{.topnav{{padding:14px 18px;gap:16px}}.topnav-primary,.topnav-utility .nav-link{{display:none}}.hero{{padding:90px 20px 80px}}.path-wrap{{padding:0 16px 56px}}}}
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

  <div class="coming-soon-note">
    <strong>Step-by-step descriptions coming soon.</strong> For now, open any step to read the playbook directly. Detailed breakthrough quotes and contents lists are being added pathway by pathway.
  </div>
</div>

<footer>
  <p>{scripture}</p>
  <div class="brand-mark">Kingdom Builders AI &middot; Pathway {p['order']:02d} of 08</div>
</footer>

</body>
</html>
"""


for p in PATHWAYS:
    if p['slug'] == 'work-reset':
        continue
    out_path = f"static/pathways/{p['slug']}.html"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(build_page(p))
    print(f"Wrote {out_path}")

print(f"\nAll {len(PATHWAYS)} pathways live.")
