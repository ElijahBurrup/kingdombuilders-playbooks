"""Replace the minimal topnav on each pathway page with the same topnav as
index.html / archive.html (brand + Pathways + Archive + Refer + Sign In).
Also ensure the supporting CSS (topnav-primary, topnav-utility, nav-link,
nav-button, nav-avatar) is present.
"""
import os
import re

PAGES = [
    'static/pathways/work-reset.html',
    'static/pathways/identity-walk.html',
    'static/pathways/ai-age.html',
    'static/pathways/money-architecture.html',
    'static/pathways/resilience-stack.html',
    'static/pathways/inner-battle.html',
    'static/pathways/family-foundation.html',
    'static/pathways/strategist-toolkit.html',
    'static/pathways/process-model.html',
]

NEW_TOPNAV_HTML = '''<nav class="topnav">
  <a href="/playbooks/" class="brand">Kingdom Builders AI</a>
  <div class="topnav-primary">
    <a href="/playbooks/" class="active">Pathways</a>
    <a href="/playbooks/archive">Archive</a>
  </div>
  <div class="topnav-utility">
    <a href="/playbooks/referrals" class="nav-link">Refer</a>
    <a href="/playbooks/auth" class="nav-button">Sign In</a>
  </div>
  <button class="nav-hamburger" aria-label="Open menu" onclick="openNavDrawer()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg></button>
</nav>'''

# Canonical topnav CSS — mirrors index.html
TOPNAV_CSS = '''
/* ===== TOP NAV (shared) ===== */
.topnav{position:absolute;top:0;left:0;right:0;display:flex;align-items:center;padding:18px 36px;z-index:10;gap:32px}
.topnav .brand{font-family:'Poppins',sans-serif;font-size:0.7rem;font-weight:700;letter-spacing:5px;text-transform:uppercase;color:rgba(245,224,168,0.85);text-decoration:none;flex-shrink:0}
.topnav-primary{display:flex;gap:8px;flex:1}
.topnav-primary a{font-family:'Poppins',sans-serif;font-size:0.72rem;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:rgba(245,224,168,0.55);text-decoration:none;padding:8px 14px;border-radius:30px;transition:all 0.2s}
.topnav-primary a:hover{color:var(--gold-glow,#E8C96A);background:rgba(245,224,168,0.06)}
.topnav-primary a.active{color:var(--gold-glow,#E8C96A);background:rgba(245,224,168,0.10)}
.topnav-utility{display:flex;gap:10px;align-items:center;flex-shrink:0}
.nav-link{font-family:'Poppins',sans-serif;font-size:0.7rem;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:rgba(245,224,168,0.6);text-decoration:none;padding:8px 14px;transition:all 0.2s}
.nav-link:hover{color:var(--gold-glow,#E8C96A)}
.nav-button{font-family:'Poppins',sans-serif;font-size:0.7rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--dawn,#1F2440);background:linear-gradient(135deg,var(--gold,#D4A843),var(--gold-glow,#E8C96A));text-decoration:none;padding:9px 20px;border-radius:50px;transition:all 0.25s;box-shadow:0 2px 12px rgba(212,168,67,0.32)}
.nav-button:hover{transform:translateY(-1px);box-shadow:0 4px 18px rgba(212,168,67,0.45)}
@media(max-width:780px){.topnav{padding:14px 18px;gap:0}.topnav-primary,.topnav-utility{display:none}}
'''

count = 0
for path in PAGES:
    if not os.path.exists(path):
        continue
    with open(path, encoding='utf-8') as f:
        html = f.read()

    # 1) Replace any existing <nav class="topnav">...</nav> block with canonical one
    new_html, n = re.subn(
        r'<nav class="topnav">.*?</nav>',
        NEW_TOPNAV_HTML,
        html, count=1, flags=re.DOTALL,
    )
    if n == 0:
        print(f"  (no topnav block) {path}")
        continue

    # 2) Inject canonical CSS if topnav-primary CSS isn't present yet
    if '.topnav-primary{' not in new_html:
        new_html = new_html.replace('</style>', TOPNAV_CSS + '\n</style>', 1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    count += 1
    print(f"  standardized topnav on {path}")

print(f"\nUpdated {count} pages.")
