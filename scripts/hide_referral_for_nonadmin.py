"""Inject CSS that hides every Refer/referral link from non-admin users.

Until we have proof that ads alone can convert paying subscribers, the
referral surface stays admin-only. The code stays in place — only the
menu links disappear from regular users' views.

Strategy:
- Add a <style id="auth-hide-referral"> in the <head> of every nav-bearing
  page that hides anchors targeting /playbooks/referrals by default.
- The v4 auth-aware script in inject_auth_awareness.py adds a
  `body.auth-admin` class when /auth/status returns is_admin=true. The
  hiding CSS uses :not(.auth-admin) so admin pages render the link
  immediately (no flicker), non-admin pages keep it hidden permanently.
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

MARKER_ID = 'auth-hide-referral'
STYLE = (
    f'<style id="{MARKER_ID}">'
    # Hide referral links by default — both topnav and drawer flavors.
    # Restored when body.auth-admin is present (set by the auth-aware script
    # once /auth/status returns is_admin=true).
    'body:not(.auth-admin) a[href$="/referrals"],'
    'body:not(.auth-admin) form[action$="/referrals"]'
    '{display:none !important}'
    '</style>'
)


def main() -> None:
    updated = 0
    for path in PAGES:
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            html = f.read()
        # Strip any prior copy so this is idempotent
        html = re.sub(
            rf'<style id="{MARKER_ID}">.*?</style>',
            '',
            html, flags=re.DOTALL,
        )
        # Inject just before </head>
        if '</head>' not in html:
            print(f"  no </head> in {path}, skipping")
            continue
        html = html.replace('</head>', STYLE + '\n</head>', 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        updated += 1
        print(f"  injected referral-hide into {path}")
    print(f"\nUpdated {updated} pages.")


if __name__ == "__main__":
    main()
