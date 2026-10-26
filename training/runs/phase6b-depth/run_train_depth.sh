#!/usr/bin/env bash
# Phase 6b: give the walker the head ToF sensor (8 x 8 distances) and train it to use it, as executed (2026-10-26).
# Starts from phase 6 run B's best checkpoint, widened from 61 to 125 policy inputs (critic 76 -> 140) with zero
# weights for the new inputs (expand_checkpoint.py), so it starts as exactly the run B walker. Half of the route ducks
# are then sent straight down the lane through the box's position (box_contact penalty -2 per step).
# 4,096 ducks, 2,000 iterations, headless. On the VM: bash run_train_depth.sh
set -u
export PATH=$HOME/.local/bin:$PATH
export ROUTE_PROGRESS_WEIGHT=1.5
cd ~/IsaacLab
export UV_PROJECT_ENVIRONMENT=~/IsaacLab/.venv-newton
RUNB=$(ls -d ~/IsaacLab/logs/rsl_rl/microduck_velocity_rough_backlash/*course_finetune_v2_progress | tail -1)
BEST_B=$(python3 -c "
import glob, json, os, re
runs = glob.glob(os.path.expanduser('~/eval/progress/course_finetune_v2_progress/model_*.json'))
best = max(runs, key=lambda f: (json.load(open(f))['summary']['finished'], int(re.search(r'(\d+)', os.path.basename(f)).group(1))))
print(os.path.basename(best).replace('.json', '.pt'))")
mkdir -p ~/ckpt
echo start $(date -u +%H:%M:%SZ) from $BEST_B > ~/course_train_depth.log
.venv-newton/bin/python ~/isaaclab_ext/expand_checkpoint.py "$RUNB/$BEST_B" ~/ckpt/depth_init_from_runB.pt \
  --actor-add 64 --critic-add 64 >> ~/course_train_depth.log 2>&1
PYTHONPATH=$HOME/isaaclab_ext uv run --extra video python ~/isaaclab_ext/launch.py train --rl_library rsl_rl \
  --task IsaacContrib-Velocity-Course-MicroDuck-Depth --num_envs 4096 presets=backlash \
  --checkpoint ~/ckpt/depth_init_from_runB.pt --max_iterations 2000 --run_name course_depth_from_runB \
  >> ~/course_train_depth.log 2>&1
echo end $(date -u +%H:%M:%SZ) exit $? >> ~/course_train_depth.log
