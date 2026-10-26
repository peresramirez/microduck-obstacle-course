#!/usr/bin/env bash
# Phase 5b "before" run, as executed on the workstation (2026-10-26). NVIDIA's unchanged checkpoint (and our phase 4
# fine-tune) on the real course: scored runs with 128 ducks, then RTX videos (overview of 16 lanes, chase camera).
# Run on the VM from anywhere: bash run_before.sh   (outputs in ~/eval/before/)
set -u
export PATH=$HOME/.local/bin:$PATH
cd ~/IsaacLab
NV=$(ls ~/IsaacLab/.pretrained_checkpoints/rsl_rl/https/*/Assets/Isaac/6.2/Isaac/IsaacLab/PretrainedCheckpoints/rsl_rl/IsaacContrib-Velocity-Rough-MicroDuck_backlash_newtonmjwarp_none_rsl_rl.pt)
P4=~/IsaacLab/logs/rsl_rl/microduck_velocity_rough_backlash/2026-10-26_17-49-16_finetune_from_pretrained/model_51998.pt
OUT=~/eval/before; mkdir -p $OUT
EVAL="python $HOME/isaaclab_ext/eval_course.py --num_envs 128 presets=backlash --no_visuals --seconds 40 --speed 0.25"
# 1. scored runs, headless (Newton only)
( export UV_PROJECT_ENVIRONMENT=~/IsaacLab/.venv-newton
  PYTHONPATH=$HOME/isaaclab_ext uv run --extra video $EVAL --task IsaacContrib-Velocity-Course-MicroDuck \
    --checkpoint $NV --out $OUT/before_nvidia.json --label "before: NVIDIA checkpoint" > $OUT/before_nvidia.log 2>&1
  PYTHONPATH=$HOME/isaaclab_ext uv run --extra video $EVAL --task IsaacContrib-Velocity-Course-MicroDuck \
    --checkpoint $P4 --out $OUT/before_phase4.json --label "before: our phase 4 fine-tune" > $OUT/before_phase4.log 2>&1 )
# 2. RTX videos with Kit (needs the Omniverse EULA accepted: ~/isaac-env.sh)
source ~/isaac-env.sh
PYTHONPATH=$HOME/isaaclab_ext uv run --extra isaacsim --extra video python $HOME/isaaclab_ext/eval_course.py \
  --task IsaacContrib-Velocity-Course-MicroDuck-OverviewCam --num_envs 16 presets=backlash --checkpoint $NV \
  --seconds 40 --speed 0.25 --video sensor:overview_cam --video_length 2000 \
  --out $OUT/overview/report.json --label "before: overview, 16 lanes" > $OUT/overview.log 2>&1
PYTHONPATH=$HOME/isaaclab_ext uv run --extra isaacsim --extra video python $HOME/isaaclab_ext/eval_course.py \
  --task IsaacContrib-Velocity-Course-MicroDuck-ChaseCam --num_envs 4 presets=backlash --checkpoint $NV \
  --seconds 40 --speed 0.25 --video sensor:chase_cam --video_length 2000 \
  --out $OUT/chase/report.json --label "before: chase camera, 4 lanes" > $OUT/chase.log 2>&1
grep -h "^\[eval\]" $OUT/*.log
echo done
