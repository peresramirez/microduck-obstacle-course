# Send scripts to FreeCAD/Blender and archive exactly what was sent, in order, for the as-run record.
# Source it from isaac-obstacle-course/, set AR to the asset's build/as-run folder, then:
#   source tools/as_run.sh; AR=assets/E2-low-steps/build/as-run
#   send freecad fc01-params assets/E2-low-steps/build/freecad/01_params.py --var DOC=E2_low_steps
# Each call writes AR/NN-LABEL.py (header: app, time, --var values; then every script sent, in order) with this
# folder's absolute path masked as $PROJECT, then runs it through tools/apps.py exec.
send() {
  local app=$1 label=$2; shift 2
  local files=() vars=()
  while [ $# -gt 0 ]; do
    if [ "$1" = --var ]; then vars+=(--var "$2"); shift 2; else files+=("$1"); shift; fi
  done
  mkdir -p "$AR"
  local n=$(( $(find "$AR" -maxdepth 1 -name '*.py' | wc -l) + 1 ))
  local f="$AR/$(printf %02d "$n")-$label.py"
  { echo "# sent to $app on $(date '+%Y-%m-%d %H:%M:%S') with:"
    for v in "${vars[@]}"; do [ "$v" = --var ] || echo "#   --var $v"; done
    for s in "${files[@]}"; do echo "# ---- $s"; cat "$s"; done; } | sed -e "s#$PWD#\$PROJECT#g" -e "s#$HOME#~#g" > "$f"
  uv run --no-project python tools/apps.py exec "$app" "${files[@]}" "${vars[@]}"
}
