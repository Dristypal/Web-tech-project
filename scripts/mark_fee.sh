#!/usr/bin/env bash
# Simple script to seed, login as admin, and mark the first pending fee as paid.
# Usage: ./scripts/mark_fee.sh
set -euo pipefail
WORKDIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$WORKDIR"
COOKIEJAR="/tmp/cc_cookies.txt"
ADMIN_EMAIL="admin@campus.edu"
ADMIN_PW="admin123"
BASEURL="http://127.0.0.1:5000"

echo "Seeding demo data..."
curl -s -c "$COOKIEJAR" "$BASEURL/seed" >/dev/null || true

echo "Logging in as admin ($ADMIN_EMAIL)..."
# login (no CSRF required for login route)
curl -s -c "$COOKIEJAR" -b "$COOKIEJAR" -L -X POST \
  -d "email=$ADMIN_EMAIL" -d "password=$ADMIN_PW" \
  "$BASEURL/login" >/dev/null

echo "Fetching admin page to find pending fee form..."
curl -s -b "$COOKIEJAR" "$BASEURL/admin" -o /tmp/cc_admin_page.html

ACTION=$(grep -oE '/admin/fees/mark_paid/[0-9]+' /tmp/cc_admin_page.html | head -n1 || true)
CSRF=$(grep -oE 'name="_csrf_token" value="[^"]+"' /tmp/cc_admin_page.html | sed -E 's/.*value="([^"]+)"/\1/' | head -n1 || true)

if [ -z "$ACTION" ] || [ -z "$CSRF" ]; then
  echo "No pending fee form found on admin page. Check if there are pending fees or login succeeded." >&2
  exit 1
fi

echo "Found action: $ACTION"
echo "Found CSRF token: ${CSRF:0:8}..."

FULLURL="$BASEURL$ACTION"

echo "Posting mark-paid to $FULLURL"
resp=$(curl -s -b "$COOKIEJAR" -c "$COOKIEJAR" -X POST -d "_csrf_token=$CSRF" "$FULLURL" -i)

echo "Response headers:"
echo "$resp" | sed -n '1,20p'

# verify by fetching fee detail (if available in page links)
FEEID=$(echo "$ACTION" | sed -E 's:.*/([0-9]+):\1:')
if [ -n "$FEEID" ]; then
  echo "Fetching fee detail for id $FEEID"
  curl -s -b "$COOKIEJAR" "$BASEURL/admin/fees/$FEEID" -o /tmp/cc_fee_detail.html
  echo "Fee detail snippet:"
  sed -n '1,120p' /tmp/cc_fee_detail.html
fi

echo "Done."