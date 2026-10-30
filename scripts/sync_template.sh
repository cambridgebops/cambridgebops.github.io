#!/usr/bin/env bash
# Copy the shared, city-independent parts of this repository into another city's repository,
# then rebuild its pages from its own city.json. City-specific files are never touched:
# city.json, docs/events.json, docs/sources.json.
#
#   scripts/sync_template.sh ../oxfordbops      # push this repo's template to the Oxford repo
#
# Run it from the repository that has the newer template. Review `git diff` in the target, run its
# tests, commit and push there.
set -euo pipefail
cd "$(dirname "$0")/.."
target="${1:?path to the other city's repository}"
[ -f "$target/city.json" ] || { echo "$target has no city.json; not a bops city repository"; exit 1; }

shared=(site scripts tests .github LICENSE .gitignore README.md)
for item in "${shared[@]}"; do
  rm -rf "$target/$item"
  cp -R "$item" "$target/$item"
done
(cd "$target" && python3 scripts/build.py && python3 -m unittest discover -s tests)
echo "Template synced into $target. Review 'git -C $target status', then commit and push there."
