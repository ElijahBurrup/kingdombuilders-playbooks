"""Remove the obsolete v1 auth-aware <script> block from each nav-bearing page.
v2 now does the logout via fetch+navigate to bypass Cloudflare's redirect-eating.
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

pat = re.compile(
    r'\s*<script data-auth-aware="v1">.*?</script>',
    re.DOTALL,
)

count = 0
for path in PAGES:
    if not os.path.exists(path):
        continue
    with open(path, encoding='utf-8') as f:
        html = f.read()
    new_html, n = pat.subn('', html)
    if n == 0:
        continue
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    count += 1
    print(f"  stripped v1 from {path}")
print(f"\nStripped {count} pages.")
