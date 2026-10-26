#!/usr/bin/env bash
# Score every saved checkpoint of the phase 6 run on the real course (128 ducks, headless, same settings as the
# "before" run), so progress is measured in finishes, not just reward. Skips checkpoints already scored.
# Run on the VM: bash eval_checkpoints.sh [RUN_NAME] [--follow]   -> ~/eval/progress/<RUN_NAME>/model_<iteration>.json
# RUN_NAME defaults to course_finetune_from_nvidia (run A); --follow keeps scoring new checkpoints until training ends.
# TASK=... picks the task (default the blind course task; the 6b run uses IsaacContrib-Velocity-Course-MicroDuck-Depth).
# Extra eval_course.py options go in EVAL_ARGS (e.g. EVAL_ARGS="--head random"). Runs A and B were scored with the
# code of that time, whose head pose was NVIDIA's random one (now: --head random).
set -u
export PATH=$HOME/.local/bin:$PATH
cd ~/IsaacLab
export UV_PROJECT_ENVIRONMENT=~/IsaacLab/.venv-newton
NAME=${1:-course_finetune_from_nvidia}
RUN=$(ls -d ~/IsaacLab/logs/rsl_rl/microduck_velocity_rough_backlash/*_$NAME | tail -1)
OUT=~/eval/progress/$NAME${SUFFIX:-}; mkdir -p $OUT   # SUFFIX separates scoring conditions (e.g. _straight)
while true; do
for ck in $(ls $RUN/model_*.pt | sort -t_ -k2 -n); do
  name=$(basename $ck .pt)
  [ -f $OUT/$name.json ] && continue
  PYTHONPATH=$HOME/isaaclab_ext uv run --extra video python $HOME/isaaclab_ext/eval_course.py \
    --task ${TASK:-IsaacContrib-Velocity-Course-MicroDuck} --num_envs 128 presets=backlash --no_visuals --seconds 40 \
    --checkpoint $ck --out $OUT/$name.json --label "$name" ${EVAL_ARGS:-} > $OUT/$name.log 2>&1
  python3 -c "import json;s=json.load(open('$OUT/$name.json'))['summary'];print('$name', s['finished'], s['fell'], s['passed'])"
done
[ "${2:-}" = --follow ] || break
pgrep -f "run_name $NAME" >/dev/null || break   # training ended and every checkpoint is scored
sleep 60
done
