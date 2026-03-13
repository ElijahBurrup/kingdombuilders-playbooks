"""
Update all landing page HTML files in static/:
1. Remove cta-hero button from cover
2. Shrink cover min-height from 100vh to 60vh
3. Add floating fab-cta button (CSS + HTML)
4. Remove cta-btn "READ THE PLAYBOOK" button
5. Remove cover-price span
"""

import os
import re
import glob

STATIC_DIR = "C:/Projects/KingdomBuilders.AI/Playbooks/static"
EXCLUDE = {"index.html", "privacy.html", "refund.html", "terms.html",
           "thanks.html", "free-salmon-ch1.html", "landing.html"}

FAB_CSS = (
    "\n.fab-cta{position:fixed;bottom:24px;right:24px;z-index:999;padding:14px 28px;"
    "background:linear-gradient(135deg,var(--gold),var(--gold-glow));color:var(--purple-deep);"
    "font-family:'Poppins',sans-serif;font-size:0.82rem;font-weight:700;letter-spacing:0.5px;"
    "text-decoration:none;border-radius:50px;box-shadow:0 4px 20px rgba(212,168,67,0.4);"
    "transition:all 0.3s;border:none;cursor:pointer}\n"
    ".fab-cta:hover{transform:translateY(-2px);box-shadow:0 8px 32px rgba(212,168,67,0.55)}\n"
    ".fab-cta svg{display:inline-block;vertical-align:middle;width:16px;height:16px;"
    "margin-right:6px;stroke:currentColor;fill:none;stroke-width:2}"
)

FAB_JS = (
    '<script>'
    '(function(){'
    'var p="";try{var s=location.pathname.split("/");if(s.length>2)p="/"+s[1];}catch(e){}'
    'var a=document.querySelector(".fab-cta");'
    'if(a)a.href=p+"/read/"+a.getAttribute("data-slug")+"?buy=1";'
    '})()'
    '</script>'
)

def fab_html(slug):
    return (
        '<a href="read/' + slug + '?buy=1" class="fab-cta" data-slug="' + slug + '">'
        '<svg viewBox="0 0 24 24">'
        '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>'
        '<circle cx="12" cy="12" r="3"/></svg>'
        'Get the Playbook</a>'
    )


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(filepath)
    slug = filename.replace(".html", "")
    original = content
    changes = []

    # 1. Remove cta-hero line
    new = re.sub(r'[ \t]*<a [^>]*class="cta-hero"[^>]*>.*?</a>\s*\n?', '', content)
    if new != content:
        changes.append("removed cta-hero")
        content = new

    # 5. Remove cover-price line
    new = re.sub(r'[ \t]*<span [^>]*class="cover-price"[^>]*>.*?</span>\s*\n?', '', content)
    if new != content:
        changes.append("removed cover-price")
        content = new

    # 2. Shrink cover height: min-height:100vh -> min-height:60vh in .cover rule
    new = content.replace("min-height:100vh", "min-height:60vh", 1)
    if new != content:
        changes.append("shrunk cover to 60vh")
        content = new

    # 3a. Add fab-cta CSS before </style>
    if ".fab-cta{" not in content:
        content = content.replace("</style>", FAB_CSS + "\n</style>")
        changes.append("added fab-cta CSS")

    # 3b. Fix fab-cta href to point to read/{slug} (the purchase gate)
    # Replace any existing fab-cta with correct href + data-slug
    old_fab = re.search(r'<a href="[^"]*" class="fab-cta"[^>]*>.*?</a>', content)
    if old_fab:
        correct_fab = fab_html(slug)
        if old_fab.group(0) != correct_fab:
            content = content.replace(old_fab.group(0), correct_fab)
            changes.append(f"fixed fab-cta href to read/{slug}")
    else:
        content = content.replace("</body>", fab_html(slug) + "\n\n</body>")
        changes.append("added fab-cta HTML")

    # 3c. Add fab-cta JS for prefix detection (fixes links on production)
    if 'data-slug="' in content and FAB_JS not in content:
        content = content.replace("</body>", FAB_JS + "\n</body>")
        changes.append("added fab-cta prefix JS")

    # 4. Remove cta-btn "READ THE PLAYBOOK" line
    new = re.sub(r'[ \t]*<a [^>]*class="cta-btn"[^>]*>READ THE PLAYBOOK</a>\s*\n?', '', content)
    if new != content:
        changes.append("removed cta-btn READ THE PLAYBOOK")
        content = new

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return changes
    return []


def main():
    files = glob.glob(os.path.join(STATIC_DIR, "*.html"))
    processed = 0
    skipped = 0

    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        if filename in EXCLUDE:
            print(f"  SKIP: {filename}")
            skipped += 1
            continue

        changes = process_file(filepath)
        if changes:
            print(f"  UPDATED: {filename} — {', '.join(changes)}")
            processed += 1
        else:
            print(f"  NO CHANGE: {filename}")

    print(f"\nDone. {processed} files updated, {skipped} files skipped.")


if __name__ == "__main__":
    main()
