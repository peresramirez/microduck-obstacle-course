#!/usr/bin/env bash
# Phase 6, run A (stopped at 1,038 iterations: it slowed the ducks down; see docs/phase-6-train.md): fine-tune NVIDIA's walking policy on our obstacle course, as executed on the workstation (2026-10-26).
# 4,096 ducks on 10 difficulty rows x 64 lanes, 3,000 iterations (~57 min at ~1.1 s/iteration), headless (Newton only).
# From the Mac:  cloud/nebius/start.sh && cloud/nebius/sync.sh up
#                scp training/runs/phase6-course/run_train.sh <vm>: ; cloud/nebius/ssh.sh 'tmux new -d -s course_train bash ~/run_train.sh'
# Output: ~/IsaacLab/logs/rsl_rl/microduck_velocity_rough_backlash/<date>_course_finetune_from_nvidia/ (model_*.pt, events)
set -u
export PATH=$HOME/.local/bin:$PATH
cd ~/IsaacLab
export UV_PROJECT_ENVIRONMENT=~/IsaacLab/.venv-newton
NV=$(ls ~/IsaacLab/.pretrained_checkpoints/rsl_rl/https/*/Assets/Isaac/6.2/Isaac/IsaacLab/PretrainedCheckpoints/rsl_rl/IsaacContrib-Velocity-Rough-MicroDuck_backlash_newtonmjwarp_none_rsl_rl.pt)
echo start $(date -u +%H:%M:%SZ) > ~/course_train.log
PYTHONPATH=$HOME/isaaclab_ext uv run --extra video python ~/isaaclab_ext/launch.py train --rl_library rsl_rl \
  --task IsaacContrib-Velocity-Course-MicroDuck --num_envs 4096 presets=backlash --checkpoint "$NV" \
  --max_iterations 3000 --run_name course_finetune_from_nvidia >> ~/course_train.log 2>&1
echo end $(date -u +%H:%M:%SZ) exit $? >> ~/course_train.log
