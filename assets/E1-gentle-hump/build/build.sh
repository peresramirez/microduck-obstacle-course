#!/usr/bin/env bash
# Rebuild E1 (gentle hump) from scratch in the running FreeCAD and Blender, then check the result.
#
# Needs: FreeCAD 1.1.x and Blender 5.2.x open, their MCP add-ons listening (ports 9875 / 9876),
# uv and ffmpeg. Run from isaac-obstacle-course/:
#   assets/E1-gentle-hump/build/build.sh                  # writes into assets/E1-gentle-hump/
#   OUT=/some/dir DOC=E1_test SCENE=E1_test assets/E1-gentle-hump/build/build.sh   # anywhere else
#   RECORD=02-1-e1-rebuild assets/E1-gentle-hump/build/build.sh   # also records videos/<RECORD>-freecad.mp4 / -blender.mp4
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(cd "$HERE/../../.." && pwd)"
OUT="${OUT:-$PROJECT/assets/E1-gentle-hump}"
DOC="${DOC:-E1_gentle_hump}"
SCENE="${SCENE:-E1_gentle_hump}"
TEX="$PROJECT/assets/_materials/birch-plywood/basecolor.png"
RECORD="${RECORD:-}"
PAUSE="${PAUSE:-$([ -n "$RECORD" ] && echo 3 || echo 0)}"   # seconds between steps, so each stage shows on video
cd "$PROJECT"
mkdir -p "$OUT"
apps() { uv run --no-project python tools/apps.py "$@"; }
fc() { apps exec freecad "$HERE/freecad/$1" --var "DOC=$DOC" --var "OUT=$OUT" "${@:2}"; sleep "$PAUSE"; }
bl() { apps exec blender "$HERE/blender/_common.py" "$HERE/blender/$1" --var "SCENE=$SCENE" --var "OUT=$OUT" --var "TEX=$TEX"; sleep "$PAUSE"; }

echo "== FreeCAD =="
[ -n "$RECORD" ] && apps rec-start freecad "$RECORD-freecad"
fc 01_params.py
fc 02_profile.py
fc 03_pad.py
for c in "44 mm" "10 mm" "33 mm"; do fc 03b_demo_crest.py --var "CREST=$c"; done
fc 04_export.py
[ -n "$RECORD" ] && apps rec-stop freecad "$RECORD-freecad"

echo "== Blender =="
[ -f "$TEX" ] || apps exec blender assets/_materials/birch-plywood/make_texture.py --var "TEX=$TEX"
[ -n "$RECORD" ] && apps rec-start blender "$RECORD-blender"
bl 01_import.py
bl 02_material.py
bl 03_stage.py
bl 04_render.py
bl 05_export.py
[ -n "$RECORD" ] && apps rec-stop blender "$RECORD-blender"

echo "== Checks =="
uv run --no-project --with usd-core --with trimesh --with numpy python tools/check_asset.py "$OUT" --size 1.0 0.6 0.033 --max-slope 6.0
