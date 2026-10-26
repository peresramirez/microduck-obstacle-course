"""Run Isaac Lab's normal play or train on our camera variants of NVIDIA's rough Microduck task.

Registers, with string entry points (so nothing imports Newton before Kit starts):
  IsaacContrib-Velocity-Rough-MicroDuck-ChaseCam     one camera per env following its duck  -> --video sensor:chase_cam
  IsaacContrib-Velocity-Rough-MicroDuck-OverviewCam  one global camera over env 0's tile     -> --video sensor:overview_cam
  IsaacContrib-Velocity-Course-MicroDuck             our obstacle course (course_env_cfg.py)
  IsaacContrib-Velocity-Course-MicroDuck-ChaseCam    ... with a camera following each duck   -> --video sensor:chase_cam
  IsaacContrib-Velocity-Course-MicroDuck-OverviewCam ... with one camera across the lanes    -> --video sensor:overview_cam
  IsaacContrib-Velocity-Course-MicroDuck-TrainCam    ... high wide camera for training videos -> --video sensor:overview_cam
  IsaacContrib-Velocity-Course-MicroDuck-Depth[-ChaseCam|-OverviewCam]  phase 6b: + the head ToF sensor (course_depth_cfg.py)
then hands the rest of the command line to ``isaaclab play`` / ``isaaclab train``. Run on the workstation:

    source ~/isaac-env.sh && cd ~/IsaacLab
    PYTHONPATH=~/isaaclab_ext uv run --extra isaacsim --extra video python ~/isaaclab_ext/launch.py play \\
        --rl_library rsl_rl --task IsaacContrib-Velocity-Rough-MicroDuck-ChaseCam --checkpoint <file.pt> \\
        --num_envs 4 presets=backlash --video sensor:chase_cam --video_length 500

``--checkpoint pretrained`` doesn't work here (it derives the file name from the task id): pass the file path.
"""

import sys

import register  # noqa: F401  (registers our task ids)

from isaaclab_rl.entrypoints import run_play_cli, run_train_cli

if len(sys.argv) < 2 or sys.argv[1] not in ("play", "train"):
    sys.exit("usage: launch.py play|train <isaaclab play/train arguments>")
sys.exit((run_play_cli if sys.argv[1] == "play" else run_train_cli)(sys.argv[2:]))
