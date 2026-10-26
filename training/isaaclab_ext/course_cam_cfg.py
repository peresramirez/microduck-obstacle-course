"""Camera variants of the course task, for videos and the live stream (Kit only).

* ``-ChaseCam``: one camera per duck that follows it (``follow_robot`` from ``chase_cam_cfg.py``), placed behind and
  to the +y side, so the hump, the steps and the box are seen from the side as the duck passes.
  Record with ``--video sensor:chase_cam``.
* ``-OverviewCam``: one global camera pinned to a terrain tile, looking across several lanes.
  Record with ``--video sensor:overview_cam``.
* ``-TrainCam``: the same global camera, higher and wider, over the 4,096-duck training terrain (many lanes and
  difficulty rows). Run ``train`` with ``COURSE_VISUALS=1`` and ``--video sensor:overview_cam``.

``VIEWPORT_CAMERA=chase|overview`` makes Kit's viewport (and so the WebRTC stream) look through that camera, since
the viewport's camera menu doesn't open through the streaming client.
"""

import os

import torch

from isaaclab.managers import EventTermCfg
from isaaclab.sensors import CameraCfg
from isaaclab.sim import PinholeCameraCfg
from isaaclab.utils import configclass
from isaaclab_physx.renderers import IsaacRtxRendererCfg

from chase_cam_cfg import follow_robot
from course_depth_cfg import MicroDuckCourseDepthEnvCfg
from course_env_cfg import MicroDuckCourseEnvCfg

CHASE_OFFSET = (-0.55, 0.75, 0.38)
"""Chase camera position relative to the duck (world axes) [m]: behind, on the +y side, above."""


def _rtx_camera(prim_path: str, focal_length: float) -> CameraCfg:
    return CameraCfg(
        prim_path=prim_path,
        spawn=PinholeCameraCfg(focal_length=focal_length, clipping_range=(0.02, 200.0)),
        width=1280,
        height=720,
        data_types=["rgb"],
        renderer_cfg=IsaacRtxRendererCfg(),
    )


_viewport_done = False


def _point_viewport(paths: dict[str, str]) -> None:
    """Once, set Kit's active viewport to the camera named by ``VIEWPORT_CAMERA`` (a key of ``paths``)."""
    global _viewport_done
    want = os.environ.get("VIEWPORT_CAMERA")
    if _viewport_done or want not in paths:
        return
    _viewport_done = True
    try:
        from omni.kit.viewport.utility import get_active_viewport

        get_active_viewport().camera_path = paths[want]
        print(f"[course_cam] viewport camera -> {paths[want]}", flush=True)
    except Exception as exc:  # no Kit, or no viewport
        print(f"[course_cam] viewport camera not changed: {exc}", flush=True)


def follow_duck(env, env_ids, offset=CHASE_OFFSET):
    follow_robot(env, env_ids, cam_name="chase_cam", offset=offset)
    _point_viewport({"chase": "/World/envs/env_0/ChaseCam"})


def frame_tile(env, env_ids, cam_name="overview_cam", tile=(0, 0), eye=(3.0, -4.2, 2.4), target=(3.0, 2.0, 0.0)):
    """Keep the global camera at a terrain tile's origin + ``eye``, looking at origin + ``target`` [m]."""
    cam = env.scene[cam_name]
    origin = env.scene.terrain.terrain_origins[tile[0], tile[1]].reshape(1, 3)
    cam.set_world_poses_from_view(
        origin + torch.tensor(eye, device=origin.device), origin + torch.tensor(target, device=origin.device)
    )
    _point_viewport({"overview": "/World/OverviewCam"})


@configclass
class MicroDuckCourseChaseCamEnvCfg(MicroDuckCourseEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.chase_cam = _rtx_camera("{ENV_REGEX_NS}/ChaseCam", focal_length=18.0)
        self.events.follow_chase_cam = EventTermCfg(
            func=follow_duck, mode="interval", interval_range_s=(0.02, 0.02), is_global_time=True
        )


@configclass
class MicroDuckCourseOverviewCamEnvCfg(MicroDuckCourseEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.overview_cam = _rtx_camera("/World/OverviewCam", focal_length=14.0)
        self.events.follow_overview_cam = EventTermCfg(
            func=frame_tile, mode="interval", interval_range_s=(0.02, 0.02), is_global_time=True,
            params={"tile": (0, 0), "eye": (3.0, -4.2, 2.4), "target": (3.0, 2.0, 0.0)},
        )


@configclass
class MicroDuckCourseTrainCamEnvCfg(MicroDuckCourseEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.overview_cam = _rtx_camera("/World/OverviewCam", focal_length=12.0)
        self.events.follow_overview_cam = EventTermCfg(
            func=frame_tile, mode="interval", interval_range_s=(0.02, 0.02), is_global_time=True,
            params={"tile": (1, 2), "eye": (-1.0, -3.5, 3.2), "target": (5.0, 5.0, 0.0)},
        )


@configclass
class MicroDuckCourseDepthChaseCamEnvCfg(MicroDuckCourseDepthEnvCfg):
    """Phase 6b chase camera; the ToF sensor's 64 hit points are drawn (Kit debug markers)."""

    def __post_init__(self):
        super().__post_init__()
        self.scene.chase_cam = _rtx_camera("{ENV_REGEX_NS}/ChaseCam", focal_length=18.0)
        self.events.follow_chase_cam = EventTermCfg(
            func=follow_duck, mode="interval", interval_range_s=(0.02, 0.02), is_global_time=True
        )
        self.scene.tof.debug_vis = True


@configclass
class MicroDuckCourseDepthOverviewCamEnvCfg(MicroDuckCourseDepthEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.overview_cam = _rtx_camera("/World/OverviewCam", focal_length=14.0)
        self.events.follow_overview_cam = EventTermCfg(
            func=frame_tile, mode="interval", interval_range_s=(0.02, 0.02), is_global_time=True,
            params={"tile": (0, 0), "eye": (3.0, -4.2, 2.4), "target": (3.0, 2.0, 0.0)},
        )
