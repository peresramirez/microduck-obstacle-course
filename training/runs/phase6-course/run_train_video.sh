#!/usr/bin/env bash
# The training-scale video: 4,096 ducks training on all 640 lanes of our course (10 rows x 64), our textured assets
# shown (COURSE_VISUALS=1), filmed by one wide RTX camera (-TrainCam). 40 more PPO iterations from a run B checkpoint
# (training conditions, so NVIDIA's random head poses are on). As executed on the workstation (2026-10-26).
# On the VM: bash run_train_video.sh [CHECKPOINT]    -> logs/rsl_rl/.../<date>_train_video_course/videos/train/
set -u
export PATH=$HOME/.local/bin:$PATH
cd ~/IsaacLab
source ~/isaac-env.sh
RUNB=$(ls -d ~/IsaacLab/logs/rsl_rl/microduck_velocity_rough_backlash/*course_finetune_v2_progress | tail -1)
CK=${1:-$RUNB/model_52000.pt}
COURSE_VISUALS=1 ROUTE_PROGRESS_WEIGHT=1.5 PYTHONPATH=$HOME/${EXT:-isaaclab_ext} uv run --extra isaacsim --extra video \
  python $HOME/${EXT:-isaaclab_ext}/launch.py train --rl_library rsl_rl --task IsaacContrib-Velocity-Course-MicroDuck-TrainCam \
  --num_envs 4096 presets=backlash --checkpoint "$CK" --max_iterations 40 --run_name train_video_course \
  --video sensor:overview_cam --video_length 500 --video_interval 1000000 > ~/train_video_course.log 2>&1
echo "exit $?"
