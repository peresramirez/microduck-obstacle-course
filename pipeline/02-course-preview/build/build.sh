#!/usr/bin/env bash
# Assemble the whole course in Blender from the five exported assets (assets/*/model.usd) at their layout.json positions,
# render the overview and four duck-eye stills, render an 18 s fly-through, and run the course checks.
#
# Needs: Blender 5.2.x open with its MCP add-on (port 9876), the five assets built (assets/*/build/build.sh), uv, ffmpeg.
# Run from isaac-obstacle-course/:
#   pipeline/02-course-preview/build/build.sh                 # writes into pipeline/02-course-preview/
#   OUT=/some/dir SCENE=Course_test ANIM=0 pipeline/02-course-preview/build/build.sh   # elsewhere, stills only
#   RECORD=02-6a-rebuild pipeline/02-course-preview/build/build.sh   # also records videos/<RECORD>-blender.mp4
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(cd "$HERE/../../.." && pwd)"
OUT="${OUT:-$PROJECT/pipeline/02-course-preview}"
SCENE="${SCENE:-Course_preview}"
ANIM="${ANIM:-1}"                  # 0 = skip the fly-through render (432 frames, ~3 min on this Mac)
RECORD="${RECORD:-}"
PAUSE="${PAUSE:-$([ -n "$RECORD" ] && echo 3 || echo 0)}"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
cd "$PROJECT"
mkdir -p "$OUT/renders"
apps() { uv run --no-project python tools/apps.py "$@"; }
bl() { apps exec blender "$HERE/blender/_common.py" "$HERE/blender/$1" --var "SCENE=$SCENE" --var "OUT=$OUT" \
         --var "ASSETS=$PROJECT/assets" --var "LAYOUT=$PROJECT/pipeline/01-plan/layout.json"; sleep "$PAUSE"; }

echo "== Course checks (exported USDs at layout positions) =="
uv run --no-project --with usd-core --with numpy python tools/check_course.py

uv run --no-project --with usd-core python "$HERE/manifest.py"

echo "== Blender =="
[ -n "$RECORD" ] && apps rec-start blender "$RECORD-blender"
bl 01_assemble.py
bl 02_stage.py
bl 03_render_stills.py
bl 04_flythrough.py
[ -n "$RECORD" ] && apps rec-stop blender "$RECORD-blender"

if [ "$ANIM" = 1 ]; then
  echo "== Fly-through (background Blender, renders/flythrough/*.png -> videos/phase-2-assets/02-6-course-flythrough.mp4) =="
  rm -rf "$OUT/renders/flythrough"
  "$BLENDER" -b "$OUT/course.blend" -S "$SCENE" -a > "$OUT/renders/flythrough.log" 2>&1
  mkdir -p "$PROJECT/videos"
  ffmpeg -loglevel error -y -framerate 24 -pattern_type glob -i "$OUT/renders/flythrough/*.png" \
    -c:v libx264 -crf 18 -pix_fmt yuv420p "$PROJECT/videos/phase-2-assets/02-6-course-flythrough.mp4"
  echo "videos/phase-2-assets/02-6-course-flythrough.mp4"
fi
