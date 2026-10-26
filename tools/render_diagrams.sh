#!/usr/bin/env bash
# Render every docs/architecture/*.mmd to an SVG next to it (Mermaid CLI, pinned; uses the installed Google Chrome,
# so Puppeteer doesn't download its own browser). Run from isaac-obstacle-course/: tools/render_diagrams.sh
set -euo pipefail
cd "$(dirname "$0")/../docs/architecture"
for f in *.mmd; do
  PUPPETEER_SKIP_DOWNLOAD=true npx -y @mermaid-js/mermaid-cli@11.4.2 -p puppeteer.json -t neutral -b white \
    -i "$f" -o "${f%.mmd}.svg" >/dev/null
  echo "${f%.mmd}.svg"
done
