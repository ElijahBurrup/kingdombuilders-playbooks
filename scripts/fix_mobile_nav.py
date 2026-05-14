"""Fix the broken mobile menu on all top-nav pages.
Replaces the alert() placeholder hamburger with a real drawer that
includes Pathways, Archive, Refer, and Sign In.
"""
import os
import re
import sys

sys.path.insert(0, '.')

PAGES = [
    'static/index.html',
    'static/archive.html',
    'static/compass.html',
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

DRAWER_CSS = """
/* === Mobile drawer (works on small screens) === */
.nav-drawer{
  position:fixed;top:0;right:0;bottom:0;
  width:280px;max-width:85vw;
  background:linear-gradient(170deg,#06070E 0%,#1F2440 100%);
  z-index:200;
  transform:translateX(100%);transition:transform 0.3s ease;
  display:flex;flex-direction:column;padding:64px 24px 24px;
  box-shadow:-12px 0 40px rgba(0,0,0,0.4);
}
.nav-drawer.open{transform:translateX(0)}
.nav-drawer-backdrop{
  position:fixed;inset:0;background:rgba(0,0,0,0.55);
  z-index:199;opacity:0;pointer-events:none;transition:opacity 0.3s;
}
.nav-drawer-backdrop.open{opacity:1;pointer-events:auto}
.nav-drawer .close-btn{
  position:absolute;top:18px;right:18px;
  width:36px;height:36px;border-radius:50%;
  background:rgba(245,224,168,0.08);border:1px solid rgba(245,224,168,0.18);
  color:#F5E0A8;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
}
.nav-drawer .close-btn svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round}
.nav-drawer a{
  display:block;padding:14px 18px;margin-bottom:6px;
  font-family:'Poppins',sans-serif;font-size:0.85rem;font-weight:700;letter-spacing:1.5px;
  text-transform:uppercase;color:rgba(245,224,168,0.7);text-decoration:none;
  border-radius:10px;transition:all 0.2s;
}
.nav-drawer a:hover{background:rgba(245,224,168,0.06);color:#E8C96A}
.nav-drawer a.drawer-cta{
  background:linear-gradient(135deg,#D4A843,#E8C96A);
  color:#1F2440;
  margin-top:16px;text-align:center;letter-spacing:2px;
  box-shadow:0 4px 16px rgba(212,168,67,0.35);
}
.nav-drawer a.drawer-cta:hover{background:linear-gradient(135deg,#E8C96A,#F5E0A8);color:#1F2440}
.nav-drawer .drawer-divider{
  height:1px;background:rgba(245,224,168,0.12);margin:14px 0;
}
"""

DRAWER_HTML = """
<!-- Mobile drawer (slides in from right on small screens) -->
<div class="nav-drawer-backdrop" id="nav-drawer-backdrop" onclick="closeNavDrawer()"></div>
<div class="nav-drawer" id="nav-drawer">
  <button class="close-btn" onclick="closeNavDrawer()" aria-label="Close menu">
    <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
  </button>
  <a href="/playbooks/">Pathways</a>
  <a href="/playbooks/archive">Archive</a>
  <a href="/playbooks/compass">Compass</a>
  <div class="drawer-divider"></div>
  <a href="/playbooks/referrals">Refer</a>
  <a href="/playbooks/my-playbooks">My Playbooks</a>
  <a href="/playbooks/auth" class="drawer-cta">Sign In</a>
</div>
<script>
function openNavDrawer(){
  document.getElementById('nav-drawer').classList.add('open');
  document.getElementById('nav-drawer-backdrop').classList.add('open');
  document.body.style.overflow='hidden';
}
function closeNavDrawer(){
  document.getElementById('nav-drawer').classList.remove('open');
  document.getElementById('nav-drawer-backdrop').classList.remove('open');
  document.body.style.overflow='';
}
</script>
"""

count = 0
for path in PAGES:
    if not os.path.exists(path):
        continue
    with open(path, encoding='utf-8') as f:
        html = f.read()

    # Skip if already has the drawer
    if 'id="nav-drawer"' in html:
        print(f"  (already has drawer) {path}")
        continue

    # Inject CSS just before </style>
    html = html.replace('</style>', DRAWER_CSS + '\n</style>', 1)

    # Inject HTML just before </body>
    html = html.replace('</body>', DRAWER_HTML + '\n</body>', 1)

    # Replace the alert() hamburger with the drawer opener
    html = re.sub(
        r'onclick="alert\([^"]+\)"',
        'onclick="openNavDrawer()"',
        html
    )

    # Some pages may have <button class="nav-hamburger"> without an onclick
    # — make sure it opens the drawer
    if 'nav-hamburger' in html and 'openNavDrawer' not in html:
        html = re.sub(
            r'<button class="nav-hamburger"([^>]*)>',
            r'<button class="nav-hamburger"\1 onclick="openNavDrawer()">',
            html, count=1
        )

    # For pages that don't have a nav-hamburger button at all, add one to the topnav
    if 'nav-hamburger' not in html and '<nav class="topnav">' in html:
        ham_html = (
            '<button class="nav-hamburger" aria-label="Open menu" onclick="openNavDrawer()">\n'
            '    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>\n'
            '  </button>'
        )
        # Insert before closing </nav>
        html = re.sub(
            r'(</nav>)',
            ham_html + r'\n\1',
            html, count=1
        )

    # Add hamburger CSS if not already in this page
    if '.nav-hamburger{' not in html:
        ham_css = (
            "\n.nav-hamburger{display:none;width:36px;height:36px;background:transparent;"
            "border:1px solid rgba(245,224,168,0.25);border-radius:8px;color:#F5E0A8;"
            "cursor:pointer;align-items:center;justify-content:center;margin-left:auto}"
            "\n.nav-hamburger svg{width:18px;height:18px}"
            "\n@media(max-width:780px){.nav-hamburger{display:flex}.topnav-primary,.topnav-utility{display:none}}"
        )
        html = html.replace('</style>', ham_css + '\n</style>', 1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    count += 1
    print(f"  injected drawer into {path}")

print(f"\nUpdated {count} pages.")
