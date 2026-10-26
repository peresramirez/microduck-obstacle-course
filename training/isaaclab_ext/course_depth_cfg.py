"""Phase 6b: the course task with the duck's head distance sensor (8 x 8 ToF) as a policy input.

The real Microduck has an 8 x 8-zone time-of-flight sensor in its head (VL53L5CX class: 45 x 45 degree field of view,
~4 m range). Here it is 64 rays cast from the lens position (6.4 cm in front of, 13.1 cm above the trunk origin,
measured in ``microduck_walk_backlash.usd``), pitched 30 degrees down so the zones cover the floor from ~0.17 m to
~1.7 m ahead. The head is held forward (``set_head_forward``), so the sensor is modelled rigidly in the trunk frame.

What changes compared with ``MicroDuckCourseEnvCfg`` (run B):

* the policy and the critic get 64 more inputs: distance per zone, clipped to 2 m, scaled ``(d - 0.6) / 0.4``
  (policy: +-0.05 noise, about +-2 cm). The policy goes from 61 to 125 inputs; ``expand_checkpoint.py`` widens a
  61-input checkpoint with zero weights for the new inputs, so training starts from exactly the old walker;
* half of the route-steered ducks are sent **straight down the lane centre**, through where the box is. Only what
  they sense can get them round it; ``box_contact`` (-2 per step with any body inside the box, +2 cm) punishes
  walking into it;
* the head is held forward for all ducks.

Task ids (``register.py``): ``IsaacContrib-Velocity-Course-MicroDuck-Depth`` (+ ``-ChaseCam`` / ``-OverviewCam``).
"""

import math
import os

import torch

from isaaclab.managers import ObservationTermCfg, RewardTermCfg, SceneEntityCfg
from isaaclab.sensors import RayCasterCfg
from isaaclab.sensors.ray_caster.patterns.patterns_cfg import PatternBaseCfg
from isaaclab.utils import configclass
from isaaclab.utils.noise import UniformNoiseCfg

import course_geometry as geo
from course_env_cfg import MicroDuckCourseEnvCfg, set_head_forward

TOF_ZONES, TOF_FOV_DEG, TOF_PITCH_DEG = 8, 45.0, 30.0
TOF_POS = (0.0637, 0.0, 0.1311)
"""Lens position in the trunk frame [m] (``jaw_soft/m12_lens_holder`` in the robot USD, head in its default pose)."""
TOF_CLIP, TOF_MEAN, TOF_SCALE = 2.0, 0.6, 0.4


def tof_pattern(cfg, device: str) -> tuple[torch.Tensor, torch.Tensor]:
    """``zones x zones`` rays from one point, evenly spread over ``fov_deg`` (sensor frame: x forward, y left, z up).

    Row-major from the top-left zone, as the sensor reports them."""
    half = math.radians(cfg.fov_deg) / 2
    centres = (torch.arange(cfg.zones, device=device, dtype=torch.float) + 0.5) / cfg.zones * 2 * half - half
    up, left = torch.meshgrid(-centres, -centres, indexing="ij")  # rows top->bottom, columns left->right
    dirs = torch.stack([torch.ones_like(up), torch.tan(left), torch.tan(up)], dim=-1).reshape(-1, 3)
    dirs = dirs / torch.linalg.norm(dirs, dim=1, keepdim=True)
    return torch.zeros_like(dirs), dirs


@configclass
class ToFPatternCfg(PatternBaseCfg):
    func: callable = tof_pattern
    zones: int = TOF_ZONES
    fov_deg: float = TOF_FOV_DEG


def tof_depth(env, sensor_cfg: SceneEntityCfg = SceneEntityCfg("tof")) -> torch.Tensor:
    """Distance per zone, clipped to ``TOF_CLIP`` m (misses read as the clip), scaled to about [-1.5, 3.5]."""
    d = env.scene[sensor_cfg.name].data.ray_distances.torch
    d = torch.nan_to_num(d, nan=TOF_CLIP, posinf=TOF_CLIP).clamp(0.0, TOF_CLIP)
    return (d - TOF_MEAN) / TOF_SCALE


def box_contact(env, pad: float = 0.02) -> torch.Tensor:
    """1 while any of the duck's bodies is inside the E4 box (+ ``pad``), else 0."""
    robot = env.scene["robot"]
    (x0, y0, _), (x1, y1, z1) = geo.box_bounds()
    b = robot.data.body_pos_w.torch - env.scene.env_origins.unsqueeze(1)
    inside = ((b[..., 0] > x0 - pad) & (b[..., 0] < x1 + pad) & (b[..., 1] > y0 - pad) & (b[..., 1] < y1 + pad)
              & (b[..., 2] < z1 + pad))
    return inside.any(dim=1).float()


def _pitch_down_quat(deg: float) -> tuple[float, float, float, float]:
    """(x, y, z, w) rotation about +y that tilts the sensor's +x axis ``deg`` degrees towards -z."""
    h = math.radians(deg) / 2
    return (0.0, math.sin(h), 0.0, math.cos(h))


@configclass
class MicroDuckCourseDepthEnvCfg(MicroDuckCourseEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.tof = RayCasterCfg(
            prim_path="{ENV_REGEX_NS}/Robot/Geometry/trunk_base",
            offset=RayCasterCfg.OffsetCfg(pos=TOF_POS, rot=_pitch_down_quat(TOF_PITCH_DEG)),
            ray_alignment="base",
            pattern_cfg=ToFPatternCfg(),
            mesh_prim_paths=["/World/ground"],
            max_distance=4.0,
            global_world_only=True,
            update_period=self.sim.dt * self.decimation,
        )
        self.observations.policy.tof = ObservationTermCfg(
            func=tof_depth, noise=UniformNoiseCfg(n_min=-0.05, n_max=0.05)
        )
        self.observations.critic.tof = ObservationTermCfg(func=tof_depth)
        self.commands.base_velocity.straight_route_prob = 0.5
        self.rewards.box_contact = RewardTermCfg(func=box_contact, weight=-2.0)
        set_head_forward(self)

    def play_mode(self):
        super().play_mode()
        # scoring picks the route with --route; the live stream with COURSE_ROUTE=straight (cloud/nebius/stream.sh)
        self.commands.base_velocity.straight_route_prob = 1.0 if os.environ.get("COURSE_ROUTE") == "straight" else 0.0
