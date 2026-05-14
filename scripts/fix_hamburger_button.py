"""Add missing <button class="nav-hamburger"> element to topnav on pages
that already have the CSS but lack the actual button element.
"""
import os
import re

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

HAM_BTN = (
    '<button class="nav-hamburger" aria-label="Open menu" onclick="openNavDrawer()">'
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" '
    'stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/>'
    '<line x1="3" y1="12" x2="21" y2="12"/>'
    '<line x1="3" y1="18" x2="21" y2="18"/></svg>'
    '</button>'
)

count = 0
for path in PAGES:
    if not os.path.exists(path):
        continue
    with open(path, encoding='utf-8') as f:
        html = f.read()

    # Skip if button element already exists
    if re.search(r'<button[^>]*class="nav-hamburger"', html):
        print(f"  (already has button) {path}")
        continue

    # Insert just before the closing </nav>
    new_html, n = re.subn(r'</nav>', '  ' + HAM_BTN + '\n</nav>', html, count=1)
    if n == 0:
        print(f"  (no </nav> tag) {path}")
        continue

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    count += 1
    print(f"  injected hamburger into {path}")

print(f"\nUpdated {count} pages.")
