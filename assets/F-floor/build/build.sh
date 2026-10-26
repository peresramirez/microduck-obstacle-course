#!/usr/bin/env bash
# Rebuild F (floor and lane) from scratch in the running FreeCAD and Blender, then check the result.
#
# Needs: FreeCAD 1.1.x and Blender 5.2.x open, their MCP add-ons listening (ports 9875 / 9876),
# uv and ffmpeg. Run from isaac-obstacle-course/:
#   assets/F-floor/build/build.sh                  # writes into assets/F-floor/
#   OUT=/some/dir DOC=F_test SCENE=F_test assets/F-floor/build/build.sh   # anywhere else
#   RECORD=02-5-f-rebuild assets/F-floor/build/build.sh   # also records videos/<RECORD>-freecad.mp4 / -blender.mp4
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(cd "$HERE/../../.." && pwd)"
OUT="${OUT:-$PROJECT/assets/F-floor}"
DOC="${DOC:-F_floor}"
SCENE="${SCENE:-F_floor}"
MAT="$PROJECT/assets/_materials/polished-concrete"
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
fc 02_floor.py
fc 03_export.py
[ -n "$RECORD" ] && apps rec-stop freecad "$RECORD-freecad"

echo "== Blender =="
# tape lines at the route start / finish of layout.json (x 0.40 and 5.60 m), 5 cm wide
[ -f "$MAT/basecolor.png" ] && [ -f "$MAT/roughness.png" ] || apps exec blender "$MAT/make_textures.py" --var "DIR=$MAT" \
    --var START_X=0.40 --var FINISH_X=5.60 --var TAPE_W=0.05
[ -n "$RECORD" ] && apps rec-start blender "$RECORD-blender"
bl 01_import.py
bl 02_material.py
bl 03_stage.py
bl 04_render.py
bl 05_export.py
[ -n "$RECORD" ] && apps rec-stop blender "$RECORD-blender"

echo "== Checks =="
uv run --no-project --with usd-core --with trimesh --with numpy python tools/check_asset.py "$OUT" --size 6.0 1.2 0.0 --max-slope 1.0 \
    --part LaneFloor 0 6.0 -0.6 0.6 0 0
