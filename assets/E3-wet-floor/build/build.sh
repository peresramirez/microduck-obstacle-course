#!/usr/bin/env bash
# Rebuild E3 (wet floor) from scratch in the running FreeCAD and Blender, then check the result.
#
# Needs: FreeCAD 1.1.x and Blender 5.2.x open, their MCP add-ons listening (ports 9875 / 9876),
# uv and ffmpeg. Run from isaac-obstacle-course/:
#   assets/E3-wet-floor/build/build.sh                  # writes into assets/E3-wet-floor/
#   OUT=/some/dir DOC=E3_test SCENE=E3_test assets/E3-wet-floor/build/build.sh   # anywhere else
#   RECORD=02-3-e3-rebuild assets/E3-wet-floor/build/build.sh   # also records videos/<RECORD>-freecad.mp4 / -blender.mp4
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(cd "$HERE/../../.." && pwd)"
OUT="${OUT:-$PROJECT/assets/E3-wet-floor}"
DOC="${DOC:-E3_wet_floor}"
SCENE="${SCENE:-E3_wet_floor}"
MAT="$PROJECT/assets/_materials/wet-tile"
RECORD="${RECORD:-}"
PAUSE="${PAUSE:-$([ -n "$RECORD" ] && echo 3 || echo 0)}"   # seconds between steps, so each stage shows on video
cd "$PROJECT"
mkdir -p "$OUT"
apps() { uv run --no-project python tools/apps.py "$@"; }
fc() { apps exec freecad "$HERE/freecad/$1" --var "DOC=$DOC" --var "OUT=$OUT" "${@:2}"; sleep "$PAUSE"; }
bl() { apps exec blender "$HERE/blender/_common.py" "$HERE/blender/$1" --var "SCENE=$SCENE" --var "OUT=$OUT" \
         --var "BASE_TEX=$MAT/basecolor.png" --var "ROUGH_TEX=$MAT/roughness.png"; sleep "$PAUSE"; }

echo "== FreeCAD =="
[ -n "$RECORD" ] && apps rec-start freecad "$RECORD-freecad"
fc 01_params.py
fc 02_tile.py
fc 03_export.py
[ -n "$RECORD" ] && apps rec-stop freecad "$RECORD-freecad"

echo "== Blender =="
[ -f "$MAT/basecolor.png" ] && [ -f "$MAT/roughness.png" ] || apps exec blender "$MAT/make_textures.py" --var "DIR=$MAT"
[ -n "$RECORD" ] && apps rec-start blender "$RECORD-blender"
bl 01_import.py
bl 02_material.py
bl 03_stage.py
bl 04_render.py
bl 05_export.py
[ -n "$RECORD" ] && apps rec-stop blender "$RECORD-blender"

echo "== Checks =="
uv run --no-project --with usd-core --with trimesh --with numpy python tools/check_asset.py "$OUT" --size 0.8 0.6 0.002 --max-slope 1.0 \
    --part WetTile 0 0.8 -0.3 0.3 0 0.002
