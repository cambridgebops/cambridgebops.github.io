#!/usr/bin/env bash
# Builds docs/index.html (served by GitHub Pages) from site/index.html, filling in the Supabase URL and publishable key.
# Usage: scripts/build.sh <supabase-url> <publishable-key>
set -euo pipefail
cd "$(dirname "$0")/.."
url="${1:?supabase url}"; key="${2:?publishable key}"
sed -e "s|__SUPABASE_URL__|$url|g" -e "s|__SUPABASE_KEY__|$key|g" site/index.html > docs/index.html
echo "wrote docs/index.html"
