#!/usr/bin/env bash
# Rebuild E2 (low steps) from scratch in the running FreeCAD and Blender, then check the result.
#
# Needs: FreeCAD 1.1.x and Blender 5.2.x open, their MCP add-ons listening (ports 9875 / 9876),
# uv and ffmpeg. Run from isaac-obstacle-course/:
#   assets/E2-low-steps/build/build.sh                  # writes into assets/E2-low-steps/
#   OUT=/some/dir DOC=E2_test SCENE=E2_test assets/E2-low-steps/build/build.sh   # anywhere else
#   RECORD=02-2-e2-rebuild assets/E2-low-steps/build/build.sh   # also records videos/<RECORD>-freecad.mp4 / -blender.mp4
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(cd "$HERE/../../.." && pwd)"
OUT="${OUT:-$PROJECT/assets/E2-low-steps}"
DOC="${DOC:-E2_low_steps}"
SCENE="${SCENE:-E2_low_steps}"
MAT="$PROJECT/assets/_materials/birch-plywood"
RECORD="${RECORD:-}"
PAUSE="${PAUSE:-$([ -n "$RECORD" ] && echo 3 || echo 0)}"   # seconds between steps, so each stage shows on video
cd "$PROJECT"
mkdir -p "$OUT"
apps() { uv run --no-project python tools/apps.py "$@"; }
fc() { apps exec freecad "$HERE/freecad/$1" --var "DOC=$DOC" --var "OUT=$OUT" "${@:2}"; sleep "$PAUSE"; }
bl() { apps exec blender "$HERE/blender/_common.py" "$HERE/blender/$1" --var "SCENE=$SCENE" --var "OUT=$OUT" \
         --var "TEX=$MAT/basecolor.png" --var "EDGE_TEX=$MAT/edge.png"; sleep "$PAUSE"; }

echo "== FreeCAD =="
[ -n "$RECORD" ] && apps rec-start freecad "$RECORD-freecad"
fc 01_params.py
fc 02_sheets.py
for r in "15 mm" "5 mm" "10 mm"; do fc 02b_demo_rise.py --var "RISE=$r"; done
fc 03_export.py
[ -n "$RECORD" ] && apps rec-stop freecad "$RECORD-freecad"

echo "== Blender =="
[ -f "$MAT/basecolor.png" ] || apps exec blender "$MAT/make_texture.py" --var "TEX=$MAT/basecolor.png"
[ -f "$MAT/edge.png" ] || apps exec blender "$MAT/make_edge_texture.py" --var "TEX=$MAT/edge.png"
[ -n "$RECORD" ] && apps rec-start blender "$RECORD-blender"
bl 01_import.py
bl 02_material.py
bl 03_stage.py
bl 04_render.py
bl 05_export.py
[ -n "$RECORD" ] && apps rec-stop blender "$RECORD-blender"

echo "== Checks =="
uv run --no-project --with usd-core --with trimesh --with numpy python tools/check_asset.py "$OUT" --size 1.2 0.6 0.02 --max-slope 1.0 \
    --part BottomSheet 0 1.2 -0.3 0.3 0 0.01 --part TopSheet 0.2 1.0 -0.3 0.3 0.01 0.02
