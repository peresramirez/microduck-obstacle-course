#!/usr/bin/env bash
# Rebuild E4 (box) from scratch in the running FreeCAD and Blender, then check the result.
#
# Needs: FreeCAD 1.1.x and Blender 5.2.x open, their MCP add-ons listening (ports 9875 / 9876),
# uv and ffmpeg. Run from isaac-obstacle-course/:
#   assets/E4-box/build/build.sh                  # writes into assets/E4-box/
#   OUT=/some/dir DOC=E4_test SCENE=E4_test assets/E4-box/build/build.sh   # anywhere else
#   RECORD=02-4-e4-rebuild assets/E4-box/build/build.sh   # also records videos/<RECORD>-freecad.mp4 / -blender.mp4
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(cd "$HERE/../../.." && pwd)"
OUT="${OUT:-$PROJECT/assets/E4-box}"
DOC="${DOC:-E4_box}"
SCENE="${SCENE:-E4_box}"
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
fc 02_box.py
for h in "100 mm" "200 mm" "150 mm"; do fc 02b_demo_height.py --var "HEIGHT=$h"; done
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
uv run --no-project --with usd-core --with trimesh --with numpy python tools/check_asset.py "$OUT" --size 0.2 0.2 0.15 \
    --part E4_Box 0 0.2 -0.1 0.1 0 0.15
