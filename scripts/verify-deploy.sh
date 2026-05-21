#!/usr/bin/env bash
# Post-deploy verification. Run this AFTER every push to production.
#
# Catches the silent failures that have repeatedly killed sign-in:
#   1. Login flow end-to-end (Playwright)
#   2. Auth endpoint accepts credentials and sets a session cookie
#   3. A paid playbook returns 200 + the actual content (not the paywall)
#
# Fails the deploy if any of these fail. Wire this into your push workflow.
#
# Usage:
#   bash scripts/verify-deploy.sh
set -euo pipefail

PROD="https://kingdombuilders.ai/playbooks"
EMAIL="elijahburrup323@gmail.com"
PASS="Eli624462!"

echo "[verify-deploy] 1/3 — POST /auth/login returns redirect + cookie"
LOGIN_RESPONSE=$(curl -s -i -X POST "$PROD/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "email=$EMAIL" \
  --data-urlencode "password=$PASS" \
  --data-urlencode "next=/playbooks/")
STATUS=$(echo "$LOGIN_RESPONSE" | head -n 1 | awk '{print $2}')
if [[ "$STATUS" != "200" && "$STATUS" != "303" ]]; then
  echo "[verify-deploy] FAIL — login returned status $STATUS"
  echo "$LOGIN_RESPONSE" | head -n 20
  exit 1
fi
if ! echo "$LOGIN_RESPONSE" | grep -qi "set-cookie:.*kb_session"; then
  echo "[verify-deploy] FAIL — login did not set kb_session cookie"
  echo "$LOGIN_RESPONSE" | head -n 30
  exit 1
fi
echo "[verify-deploy] ok"

echo "[verify-deploy] 2/3 — full Playwright login smoke test"
cd "$(dirname "$0")/.."
npx playwright test tests/login-smoke.spec.js --project=chrome-desktop --reporter=line

echo "[verify-deploy] 3/3 — health endpoint"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$PROD/health")
if [[ "$HEALTH_STATUS" != "200" ]]; then
  echo "[verify-deploy] FAIL — /health returned $HEALTH_STATUS"
  exit 1
fi
echo "[verify-deploy] ok"

echo "[verify-deploy] ALL CHECKS PASSED"
