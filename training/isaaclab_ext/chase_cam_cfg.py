"""Chase-camera variant of NVIDIA's rough Microduck task, for close-up evidence videos.

Identical to ``IsaacContrib-Velocity-Rough-MicroDuck`` except for one extra scene camera, ``chase_cam``, that an
interval event moves every control step (50 Hz) to a fixed world-space offset from each duck's root and points at it.
Record it with ``--video sensor:chase_cam``. Used by ``play_chase_cam.py``.

Why an event and not a camera parented to the trunk: with Newton physics the trunk's pose isn't propagated to child
prims, so a parented camera stays frozen at its spawn pose (tried 2026-10-26). The Newton recorder's own camera is
fixed in world space and the ``env.viewer`` overrides didn't reach the Kit recorder either.
"""

import os

import torch

from isaaclab.managers import EventTermCfg
from isaaclab.sensors import CameraCfg
from isaaclab.sim import PinholeCameraCfg
from isaaclab.utils import configclass
from isaaclab_physx.renderers import IsaacRtxRendererCfg

from isaaclab_tasks.contrib.microduck.rough_env_cfg import MicroDuckVelocityRoughEnvCfg


def follow_robot(env, env_ids, cam_name: str = "chase_cam", offset=(-0.70, 0.45, 0.32), look_height: float = 0.10):
    """Put each env's camera at the duck's root + ``offset`` (world frame, m) and aim it at the root, ``look_height`` up."""
    cam = env.scene[cam_name]
    root = env.scene["robot"].data.root_pos_w
    root = root.torch if hasattr(root, "torch") else root
    root = root[:, :3].clone()
    eyes = root + torch.tensor(offset, device=root.device, dtype=root.dtype)
    targets = root.clone()
    targets[:, 2] = root[:, 2] - 0.12 + look_height  # trunk sits ~0.12 m above the feet; aim just above the feet
    cam.set_world_poses_from_view(eyes, targets)
    _point_viewport_at_chase_cam()


_viewport_done = False


def _point_viewport_at_chase_cam() -> None:
    """With VIEWPORT_CAMERA=chase (and Kit running, e.g. a livestream), make Kit's active viewport look through env 0's
    chase camera once, so the stream follows the duck. The viewport's camera menu doesn't open through the WebRTC
    client (tried 2026-10-26), so it's set from here instead."""
    global _viewport_done
    if _viewport_done or os.environ.get("VIEWPORT_CAMERA") != "chase":
        return
    _viewport_done = True
    try:
        from omni.kit.viewport.utility import get_active_viewport

        get_active_viewport().camera_path = "/World/envs/env_0/ChaseCam"
        print("[chase_cam] viewport camera -> /World/envs/env_0/ChaseCam", flush=True)
    except Exception as exc:  # no Kit (Newton-only run) or no viewport
        print(f"[chase_cam] viewport camera not changed: {exc}", flush=True)


@configclass
class RoughChaseCamEnvCfg(MicroDuckVelocityRoughEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.chase_cam = CameraCfg(
            prim_path="{ENV_REGEX_NS}/ChaseCam",
            spawn=PinholeCameraCfg(focal_length=18.0, clipping_range=(0.02, 50.0)),
            width=1280,
            height=720,
            data_types=["rgb"],
            renderer_cfg=IsaacRtxRendererCfg(),
        )
        self.events.follow_chase_cam = EventTermCfg(
            func=follow_robot, mode="interval", interval_range_s=(0.02, 0.02), is_global_time=True
        )


def follow_crowd(env, env_ids, cam_name: str = "overview_cam", offset=(-3.0, -3.0, 2.0)):
    """Keep the single overview camera at env 0's origin + ``offset`` (world, m), looking at that origin. About 20
    training envs share each 8 m terrain tile, so this frames a crowd of ducks learning together."""
    cam = env.scene[cam_name]
    origin = env.scene.env_origins[0:1, :3].clone()
    eye = origin + torch.tensor(offset, device=origin.device, dtype=origin.dtype)
    target = origin.clone()
    target[:, 2] += 0.1
    cam.set_world_poses_from_view(eye, target)


@configclass
class RoughOverviewCamEnvCfg(MicroDuckVelocityRoughEnvCfg):
    """Training-scale variant: ONE global camera (not one per env, which would be 4,096 cameras) over env 0's tile.
    Record with ``--video sensor:overview_cam``."""

    def __post_init__(self):
        super().__post_init__()
        self.scene.overview_cam = CameraCfg(
            prim_path="/World/OverviewCam",
            spawn=PinholeCameraCfg(focal_length=14.0, clipping_range=(0.05, 200.0)),
            width=1280,
            height=720,
            data_types=["rgb"],
            renderer_cfg=IsaacRtxRendererCfg(),
        )
        self.events.follow_overview_cam = EventTermCfg(
            func=follow_crowd, mode="interval", interval_range_s=(0.02, 0.02), is_global_time=True
        )
