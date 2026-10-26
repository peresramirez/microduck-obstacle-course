"""Register our task variants with gymnasium (string entry points, so nothing imports Newton before Kit starts).

Imported by ``launch.py`` and ``eval_course.py``; see ``launch.py`` for the list of task ids.
"""

import gymnasium as gym

import isaaclab_tasks  # noqa: F401  (registers the stock tasks)

BASE = "IsaacContrib-Velocity-Rough-MicroDuck"
COURSE = "IsaacContrib-Velocity-Course-MicroDuck"
base = gym.spec(BASE)
for task_id, cfg in (
    (f"{BASE}-ChaseCam", "chase_cam_cfg:RoughChaseCamEnvCfg"),
    (f"{BASE}-OverviewCam", "chase_cam_cfg:RoughOverviewCamEnvCfg"),
    (COURSE, "course_env_cfg:MicroDuckCourseEnvCfg"),
    (f"{COURSE}-ChaseCam", "course_cam_cfg:MicroDuckCourseChaseCamEnvCfg"),
    (f"{COURSE}-OverviewCam", "course_cam_cfg:MicroDuckCourseOverviewCamEnvCfg"),
    (f"{COURSE}-TrainCam", "course_cam_cfg:MicroDuckCourseTrainCamEnvCfg"),
    (f"{COURSE}-Depth", "course_depth_cfg:MicroDuckCourseDepthEnvCfg"),
    (f"{COURSE}-Depth-ChaseCam", "course_cam_cfg:MicroDuckCourseDepthChaseCamEnvCfg"),
    (f"{COURSE}-Depth-OverviewCam", "course_cam_cfg:MicroDuckCourseDepthOverviewCamEnvCfg"),
):
    gym.register(id=task_id, entry_point=base.entry_point, disable_env_checker=True,
                 kwargs={**base.kwargs, "env_cfg_entry_point": cfg})
