#!/usr/bin/env bash
# Phase 7: validate the course-trained policies against NVIDIA's original, as executed on the workstation (2026-10-26).
# Same harness as phase 5b (eval_course.py: one lane per duck, start line, route steering, 40 s, one episode each),
# all with the head held forward, 128 ducks per test. Every condition is run for every policy, so rows compare.
#
#   bash run_validate.sh blind          NVIDIA's checkpoint vs phase 6 run B's best checkpoint (blind)
#   bash run_validate.sh depth CK.pt    + the phase 6b policy with the head ToF sensor
#
# Outputs: ~/eval/validate/<policy>/<test>.json|log ; videos with: bash run_validate.sh videos <policy> CK.pt [TASK]
set -u
export PATH=$HOME/.local/bin:$PATH
cd ~/IsaacLab
NV=$(ls ~/IsaacLab/.pretrained_checkpoints/rsl_rl/https/*/Assets/Isaac/6.2/Isaac/IsaacLab/PretrainedCheckpoints/rsl_rl/IsaacContrib-Velocity-Rough-MicroDuck_backlash_newtonmjwarp_none_rsl_rl.pt)
RUNB=$(ls -d ~/IsaacLab/logs/rsl_rl/microduck_velocity_rough_backlash/*course_finetune_v2_progress | tail -1)
# run B's best checkpoint = most finishes in its own checkpoint scoring (ties -> the later one)
BEST_B=$(python3 - <<'EOF'
import glob, json, os, re
runs = sorted(glob.glob(os.path.expanduser("~/eval/progress/course_finetune_v2_progress/model_*.json")))
best = max(runs, key=lambda f: (json.load(open(f))["summary"]["finished"], int(re.search(r"(\d+)", os.path.basename(f)).group(1))))
print(os.path.basename(best).replace(".json", ".pt"))
EOF
)
OUT=~/eval/validate
COURSE=IsaacContrib-Velocity-Course-MicroDuck
TESTS=(
  "real|--speed 0.25"
  "fast|--speed 0.35"
  "harder|--height_scale 1.4 --wet_friction 0.2"
  "flat|--height_scale 0.01 --wet_friction 1.0"
  "straight|--route straight"
  "moved_box|--route straight --box_x 4.7"
)
score() {  # policy task checkpoint
  local policy=$1 task=$2 ck=$3
  mkdir -p $OUT/$policy
  for t in "${TESTS[@]}"; do
    local name=${t%%|*} args=${t#*|}
    [ -f $OUT/$policy/$name.json ] && continue
    UV_PROJECT_ENVIRONMENT=~/IsaacLab/.venv-newton PYTHONPATH=$HOME/isaaclab_ext uv run --extra video \
      python $HOME/isaaclab_ext/eval_course.py --task $task --num_envs 128 presets=backlash --no_visuals --seconds 40 \
      --checkpoint "$ck" --out $OUT/$policy/$name.json --label "$policy: $name" $args > $OUT/$policy/$name.log 2>&1
    grep -h "^\[eval\] " $OUT/$policy/$name.log | grep -v report
  done
}
videos() {  # policy checkpoint [task prefix]
  local policy=$1 ck=$2 task=${3:-$COURSE}
  source ~/isaac-env.sh
  for cam in OverviewCam ChaseCam; do
    local n=$([ $cam = OverviewCam ] && echo 16 || echo 4) s=$([ $cam = OverviewCam ] && echo overview_cam || echo chase_cam)
    PYTHONPATH=$HOME/isaaclab_ext uv run --extra isaacsim --extra video python $HOME/isaaclab_ext/eval_course.py \
      --task $task-$cam --num_envs $n presets=backlash --checkpoint "$ck" --seconds 40 \
      --video sensor:$s --video_length 2000 --out $OUT/$policy/video_${cam}/report.json \
      --label "$policy: $cam" ${VIDEO_ARGS:-} > $OUT/$policy/video_${cam}.log 2>&1
    grep -h "^\[eval\] " $OUT/$policy/video_${cam}.log | grep -v report
  done
}
case "${1:-blind}" in
  blind)
    echo "run B best checkpoint: $BEST_B"
    score nvidia $COURSE "$NV"
    score runB $COURSE "$RUNB/$BEST_B" ;;
  depth)
    score depth $COURSE-Depth "$2" ;;
  videos)
    videos "$2" "$3" "${4:-$COURSE}" ;;
esac
echo done
