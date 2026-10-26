"""Our obstacle course as an Isaac Lab task: NVIDIA's rough Microduck task, with the terrain replaced by our course.

Registered by ``launch.py`` as ``IsaacContrib-Velocity-Course-MicroDuck`` (+ ``-ChaseCam`` / ``-OverviewCam`` in
``course_cam_cfg.py``). Everything the policy sees is unchanged (61 inputs -> 14 joint targets), so NVIDIA's and our
phase 4 checkpoints load as they are.

What changes, and why:

* **Terrain.** Every terrain tile (8 m x 2 m) holds one lane of the course (``course_geometry.py``): the E1 hump, the
  E2 sheets and the E4 box are part of the terrain mesh. Rows are the curriculum: row difficulty d scales the hump
  crest and the sheet rise by 0.5 + d (the real course is d = 0.5).
* **Wet floor.** Newton's MuJoCo solver takes the *larger* friction of the two touching colliders, so a mu 0.3 tile
  under a mu 0.7-1.3 foot would act like mu 1.0. The E3 tiles are therefore separate meshes with MuJoCo contact
  ``priority = 1``: their own friction wins. Friction falls with the row (0.8 -> 0.2; the real tile is 0.3).
* **Commands.** Most ducks are steered along the course route (``ROUTE``) by a look-ahead heading controller at
  0.15-0.35 m/s, and stop after the finish. The others keep NVIDIA's random velocity commands, so the general gait
  isn't forgotten. The policy is still blind: it never sees the box; the route takes it around.
* **Resets** place the duck on flat floor at random points along the route, facing along it, so every element is
  trained equally. **Curriculum**: progress along the lane (not NVIDIA's distance rule).
* **One extra reward**, ``route_progress`` (speed along the route / commanded speed, capped at 1): without it, run A
  drifted to walking at under half the commanded speed (see ``docs/phase-6-train.md``).
* **Schedules.** NVIDIA's reward/command schedules count steps from the start of each process, so a resumed run
  restarts them at their early values. A fine-tune of a fully trained policy starts them at their final values here.
* **Visuals** (Kit only, ``course_visuals=True``): our textured phase 2 assets are placed on every tile, scaled to that
  tile's heights. Physics never sees them: they have no colliders.
"""

from __future__ import annotations

import math
import os

import numpy as np
import torch
import trimesh
from isaaclab_newton.sim.schemas import MujocoCollisionCfg

import isaaclab.sim as sim_utils
import isaaclab.terrains as terrain_gen
import isaaclab.utils.math as math_utils
from isaaclab.managers import CurriculumTermCfg, EventTermCfg, RewardTermCfg, SceneEntityCfg
from isaaclab.sim.spawners.materials import RigidBodyMaterialBaseCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.terrains.utils import create_prim_from_mesh
from isaaclab.utils import configclass

from isaaclab_tasks.contrib.microduck.mdp.commands import MicroDuckVelocityCommand, MicroDuckVelocityCommandCfg
from isaaclab_tasks.contrib.microduck.rough_env_cfg import MicroDuckTerrainImporter, MicroDuckVelocityRoughEnvCfg

import course_geometry as geo

TILE_SIZE = (8.0, 2.0)
"""Terrain tile [m]: 8 m along the lane, 2 m across (lane 1.2 m + 0.8 m to the next lane)."""
CONTACT_SOLREF, CONTACT_SOLIMP = (0.04, 1.0), (0.85, 0.95, 0.001, 0.5, 2.0)
"""NVIDIA's soft terrain contact (MicroDuckTerrainImporter), reused for the wet tiles."""
ASSETS_DIR = os.environ.get("COURSE_ASSETS", os.path.expanduser("~/isaac-obstacle-course/assets"))
"""Our phase 2 assets (``assets/<id>/model.usd`` + textures), copied to the VM."""
VISUALS = (  # asset folder, lane-frame placement x, z lift [m] (avoids coincident surfaces), scaled part
    ("F-floor", 0.0, 0.0005, None),
    ("E1-gentle-hump", geo.E1["x0"], 0.001, "crest"),
    ("E2-low-steps", geo.E2["x0"], 0.001, "rise"),
    ("E3-wet-floor", geo.E3["x0"], 0.001, None),
    ("E4-box", geo.E4["x0"], 0.0, None),
)


# ---------------------------------------------------------------------------------------------------------------- terrain


def course_terrain(difficulty: float, cfg: CourseTerrainCfg) -> tuple[list[trimesh.Trimesh], np.ndarray]:
    """One course lane on a flat tile; the origin is the lane start on the lane centre."""
    origin = np.array([geo.LANE_X0, cfg.size[1] / 2, 0.0])
    meshes = [terrain_gen.trimesh.utils.make_plane(cfg.size, 0.0, center_zero=False)]
    for mesh in geo.solid_meshes(cfg.scale_range[0] + difficulty * (cfg.scale_range[1] - cfg.scale_range[0])).values():
        mesh = mesh.copy()
        mesh.apply_translation(origin)
        meshes.append(mesh)
    return meshes, origin


@configclass
class CourseTerrainCfg(terrain_gen.SubTerrainBaseCfg):
    function = course_terrain
    scale_range: tuple[float, float] = (0.5, 1.5)
    """Height scale of E1 and E2 at difficulty 0 and 1 (1.0 = the real course)."""


class CourseTerrainImporter(MicroDuckTerrainImporter):
    """NVIDIA's terrain importer, plus the wet tiles (own friction, contact priority) and our textured assets."""

    cfg: CourseTerrainImporterCfg

    def import_mesh(self, name: str, mesh: trimesh.Trimesh) -> None:
        super().import_mesh(name, mesh)
        if name == "terrain":
            self._course_mesh = mesh

    def configure_env_origins(self, origins=None):
        super().configure_env_origins(origins)
        if origins is None or getattr(self, "_course_done", False):
            return
        self._course_done = True
        origins = np.asarray(origins.cpu() if isinstance(origins, torch.Tensor) else origins)
        self._import_wet_tiles(origins)
        if self.cfg.course_visuals:
            self._add_visuals(origins)

    def wet_friction(self, num_rows: int) -> np.ndarray:
        """Friction of each row's wet tiles (row 0 = easiest)."""
        if isinstance(self.cfg.wet_friction, (int, float)):
            return np.full(num_rows, float(self.cfg.wet_friction))
        easy, hard = self.cfg.wet_friction
        return np.linspace(easy, hard, num_rows) if num_rows > 1 else np.array([hard])

    def _import_wet_tiles(self, origins: np.ndarray) -> None:
        tile = geo.wet_tile_mesh()
        for row, mu in enumerate(self.wet_friction(origins.shape[0])):
            parts = []
            for origin in origins[row]:
                part = tile.copy()
                part.apply_translation(origin)
                parts.append(part)
            path = f"{self.cfg.prim_path}/wet_row{row}"
            create_prim_from_mesh(
                path,
                trimesh.util.concatenate(parts),
                visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.35, 0.55, 0.75), roughness=0.1),
                physics_material=RigidBodyMaterialBaseCfg(static_friction=float(mu), dynamic_friction=float(mu)),
            )
            sim_utils.apply_collision_properties(
                f"{path}/mesh", [MujocoCollisionCfg(priority=1, solref=CONTACT_SOLREF, solimp=CONTACT_SOLIMP)]
            )
        print(f"[course] wet tiles: {origins.shape[0]} rows, friction {self.wet_friction(origins.shape[0]).round(3)}",
              flush=True)

    def _tile_heights(self, origin: np.ndarray) -> tuple[float, float]:
        """Measure E1's crest and E2's sheet rise of the tile at ``origin`` from the generated terrain mesh."""
        v = self._course_mesh.vertices
        near = (np.abs(v[:, 1] - origin[1]) < geo.E1["width"] / 2 + 1e-3) & (np.abs(v[:, 2] - origin[2]) < 0.2)
        crest_x = origin[0] + geo.E1["x0"] + geo.E1["length"] / 2
        top_x = origin[0] + geo.E2["x0"] + geo.E2["top_x0"]
        crest = v[near & (np.abs(v[:, 0] - crest_x) < 1e-3), 2].max() - origin[2]
        top = v[near & (np.abs(v[:, 0] - top_x) < 1e-3), 2].max() - origin[2]
        return float(crest), float(top / 2)

    def _add_visuals(self, origins: np.ndarray) -> None:
        count = 0
        for row in range(origins.shape[0]):
            for col in range(origins.shape[1]):
                origin = origins[row, col]
                crest, rise = self._tile_heights(origin)
                scales = {"crest": crest / geo.E1["crest"], "rise": rise / geo.E2["rise"], None: 1.0}
                for folder, x, lift, part in VISUALS:
                    usd = os.path.join(ASSETS_DIR, folder, "model.usd")
                    spawn = sim_utils.UsdFileCfg(usd_path=usd, scale=(1.0, 1.0, scales[part]))
                    spawn.func(
                        f"/World/course_visuals/r{row}_c{col}/{folder.replace('-', '_')}",
                        spawn,
                        translation=(float(origin[0] + x), float(origin[1]), float(origin[2] + lift)),
                    )
                count += 1
        print(f"[course] visuals: our assets placed on {count} tiles from {ASSETS_DIR}", flush=True)


@configclass
class CourseTerrainImporterCfg(TerrainImporterCfg):
    class_type: type = CourseTerrainImporter
    wet_friction: float | tuple[float, float] = (0.8, 0.2)
    """Wet-tile friction: one value for every tile, or (row 0, last row) interpolated across the rows."""
    course_visuals: bool = os.environ.get("COURSE_VISUALS") == "1"
    """Place our textured assets on every tile (Kit rendering only). Off for headless training unless
    ``COURSE_VISUALS=1`` (used for the training-scale video)."""


# -------------------------------------------------------------------------------------------------------------- commands


class _Polyline:
    """A route as a polyline in the lane frame: closest-point progress and point at an arc length (batched)."""

    def __init__(self, points, device):
        route = torch.tensor(points, device=device, dtype=torch.float)
        self.start, self.vec = route[:-1], route[1:] - route[:-1]
        self.seg_len = torch.linalg.norm(self.vec, dim=1)
        self.s0 = torch.cat([torch.zeros(1, device=device), torch.cumsum(self.seg_len, 0)[:-1]])
        self.length = float(self.seg_len.sum())

    def point_at(self, s: torch.Tensor) -> torch.Tensor:
        s = s.clamp(0.0, self.length)
        seg = torch.searchsorted(self.s0, s, right=True) - 1
        t = ((s - self.s0[seg]) / self.seg_len[seg]).unsqueeze(1)
        return self.start[seg] + t * self.vec[seg]

    def progress(self, p: torch.Tensor) -> torch.Tensor:
        """Arc length of the closest route point to each ``p`` (n x 2) [m]."""
        rel = p.unsqueeze(1) - self.start.unsqueeze(0)
        t = ((rel * self.vec).sum(-1) / self.seg_len**2).clamp(0.0, 1.0)
        dist = torch.linalg.norm(rel - t.unsqueeze(-1) * self.vec, dim=-1)
        best = dist.argmin(dim=1)
        return self.s0[best] + t.gather(1, best.unsqueeze(1)).squeeze(1) * self.seg_len[best]


class CourseRouteCommand(MicroDuckVelocityCommand):
    """NVIDIA's velocity command, but most ducks are steered along a course route instead.

    Route ducks get ``(v cos+(e), 0, clip(k e))`` every step, with ``e`` the heading error to a point ``lookahead``
    metres further along their route, and stand still once past the finish. Two routes: ``route`` (around the box,
    the "planner" knows where it is) and, for a share ``straight_route_prob`` of route ducks, straight down the lane
    centre through the box's position (phase 6b: avoiding it is then up to what the duck senses).
    ``lane_xy`` and ``start_x`` are kept for the curriculum and the evaluation.
    """

    cfg: CourseRouteCommandCfg

    def __init__(self, cfg: CourseRouteCommandCfg, env):
        super().__init__(cfg, env)
        self._detour = _Polyline(cfg.route, self.device)
        self._straight = _Polyline((cfg.route[0], (cfg.finish_x, cfg.route[0][1])), self.device)
        self.is_route_env = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self.is_straight = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self.route_speed = torch.zeros(self.num_envs, device=self.device)
        self.lane_xy = torch.zeros(self.num_envs, 2, device=self.device)
        self.start_x = torch.zeros(self.num_envs, device=self.device)

    def progress(self, p: torch.Tensor) -> torch.Tensor:
        """Arc length along each duck's own route of its closest route point [m]."""
        return torch.where(self.is_straight, self._straight.progress(p), self._detour.progress(p))

    def point_at(self, s: torch.Tensor) -> torch.Tensor:
        """Point at arc length ``s`` on each duck's own route (lane frame) [m]."""
        return torch.where(self.is_straight.unsqueeze(1), self._straight.point_at(s), self._detour.point_at(s))

    def _resample_command(self, env_ids):
        super()._resample_command(env_ids)
        if isinstance(env_ids, slice):
            env_ids = torch.arange(self.num_envs, device=self.device)[env_ids]
        env_ids = torch.as_tensor(env_ids, dtype=torch.long, device=self.device)
        r = torch.empty(len(env_ids), device=self.device)
        route = r.uniform_(0.0, 1.0) < self.cfg.rel_route_envs
        self.is_route_env[env_ids] = route
        self.is_straight[env_ids] = r.uniform_(0.0, 1.0) < self.cfg.straight_route_prob
        self.route_speed[env_ids] = r.uniform_(*self.cfg.route_speed)
        self.is_standing_env[env_ids[route]] = False

    def _update_command(self):
        super()._update_command()
        p = self.robot.data.root_pos_w.torch[:, :2] - self._env.scene.env_origins[:, :2]
        self.lane_xy[:] = p
        target = self.point_at(self.progress(p) + self.cfg.lookahead)
        d = target - p
        err = math_utils.wrap_to_pi(torch.atan2(d[:, 1], d[:, 0]) - self.robot.data.heading_w.torch)
        vx = self.route_speed * torch.cos(err).clamp(min=0.0)
        wz = (self.cfg.yaw_gain * err).clamp(*self.cfg.ranges.ang_vel_z)
        finished = p[:, 0] >= self.cfg.finish_x
        steer = self.is_route_env & ~finished
        stop = self.is_route_env & finished
        self.vel_command_b[steer] = torch.stack([vx, torch.zeros_like(vx), wz], 1)[steer]
        self.vel_command_b[stop] = 0.0


@configclass
class CourseRouteCommandCfg(MicroDuckVelocityCommandCfg):
    class_type: type = CourseRouteCommand
    route: tuple = geo.ROUTE
    finish_x: float = geo.FINISH_X
    rel_route_envs: float = 0.75
    """Share of command resamples that steer along the route; the rest keep NVIDIA's random commands."""
    route_speed: tuple[float, float] = (0.15, 0.35)
    lookahead: float = 0.25
    yaw_gain: float = 2.0
    straight_route_prob: float = 0.0
    """Share of route ducks sent straight down the lane centre (through the box's position) instead of around it."""


# ---------------------------------------------------------------------------------------------------- events, curriculum


def _ids(env, env_ids) -> torch.Tensor:
    """Managers pass either indices or ``slice(None)`` (all envs)."""
    if isinstance(env_ids, slice):
        return torch.arange(env.num_envs, device=env.device)[env_ids]
    return torch.as_tensor(env_ids, dtype=torch.long, device=env.device)


def reset_on_route(
    env,
    env_ids: torch.Tensor,
    from_start_prob: float = 0.3,
    y_noise: float = 0.05,
    yaw_noise: float = 0.3,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
):
    """Place each duck on flat floor along the route (or at the start line), facing along the route."""
    asset = env.scene[asset_cfg.name]
    env_ids = _ids(env, env_ids)
    n = len(env_ids)
    dev = env.device
    segs = torch.tensor(geo.FLAT_STARTS, device=dev)
    seg = torch.multinomial(segs[:, 1] - segs[:, 0], n, replacement=True)
    x = segs[seg, 0] + torch.rand(n, device=dev) * (segs[seg, 1] - segs[seg, 0])
    x = torch.where(torch.rand(n, device=dev) < from_start_prob, torch.full_like(x, geo.START_X), x)
    y_route = torch.from_numpy(geo.route_y(x.cpu().numpy())).to(dev, torch.float)
    y_ahead = torch.from_numpy(geo.route_y((x + 0.1).cpu().numpy())).to(dev, torch.float)
    y = y_route + (torch.rand(n, device=dev) * 2 - 1) * y_noise
    yaw = torch.atan2(y_ahead - y_route, torch.full_like(x, 0.1)) + (torch.rand(n, device=dev) * 2 - 1) * yaw_noise
    default_pose = asset.data.default_root_pose.torch[env_ids]
    pos = default_pose[:, :3] + env.scene.env_origins[env_ids] + torch.stack([x, y, torch.full_like(x, 0.003)], 1)
    quat = math_utils.quat_mul(
        default_pose[:, 3:7], math_utils.quat_from_euler_xyz(torch.zeros_like(yaw), torch.zeros_like(yaw), yaw)
    )
    asset.write_root_pose_to_sim_index(root_pose=torch.cat([pos, quat], dim=-1), env_ids=env_ids)
    asset.write_root_velocity_to_sim_index(root_velocity=asset.data.default_root_vel.torch[env_ids], env_ids=env_ids)
    env.command_manager.get_term("base_velocity").start_x[env_ids] = x


def course_levels(env, env_ids, up_progress: float = 2.0, down_progress: float = 0.5) -> torch.Tensor:
    """Harder row if the duck got ``up_progress`` m along the lane or to the finish; easier if under ``down_progress``.

    Only route-steered ducks move; randomly commanded ones stay on their row.
    """
    terrain = env.scene.terrain
    cmd = env.command_manager.get_term("base_velocity")
    env_ids = _ids(env, env_ids)
    progress = cmd.lane_xy[env_ids, 0] - cmd.start_x[env_ids]
    reached = cmd.lane_xy[env_ids, 0] >= geo.FINISH_X - 0.05
    route = cmd.is_route_env[env_ids]
    move_up = route & ((progress > up_progress) | reached)
    move_down = route & ~move_up & (progress < down_progress)
    terrain.update_env_origins(env_ids, move_up, move_down)
    return torch.mean(terrain.terrain_levels.float())


# --------------------------------------------------------------------------------------------------------------- rewards


def route_progress(env, command_name: str = "base_velocity") -> torch.Tensor:
    """Speed along the route as a share of the commanded speed, in [-1, 1], for route-steered ducks before the finish.

    Added after run A (2026-10-26): with NVIDIA's rewards alone, fine-tuning made the ducks walk at under half the
    commanded speed (smoother and safer, but too slow to finish). Capped at 1, so going faster than asked earns nothing.
    """
    cmd = env.command_manager.get_term(command_name)
    vel = env.scene["robot"].data.root_lin_vel_w.torch[:, :2]
    s = cmd.progress(cmd.lane_xy)
    tangent = cmd.point_at(s + 0.05) - cmd.point_at(s)
    tangent = tangent / torch.linalg.norm(tangent, dim=1, keepdim=True).clamp(min=1e-6)
    ratio = ((vel * tangent).sum(dim=1) / cmd.route_speed.clamp(min=0.05)).clamp(-1.0, 1.0)
    active = cmd.is_route_env & (cmd.lane_xy[:, 0] < cmd.cfg.finish_x)
    return torch.where(active, ratio, torch.zeros_like(ratio))


# -------------------------------------------------------------------------------------------------------------- env cfg


def course_generator(num_rows: int, num_cols: int, curriculum: bool, difficulty=(0.0, 1.0)):
    return terrain_gen.TerrainGeneratorCfg(
        size=TILE_SIZE,
        border_width=10.0,
        num_rows=num_rows,
        num_cols=num_cols,
        curriculum=curriculum,
        difficulty_range=difficulty,
        sub_terrains={"course": CourseTerrainCfg(proportion=1.0)},
    )


ROUTE_PROGRESS_WEIGHT = float(os.environ.get("ROUTE_PROGRESS_WEIGHT", "1.5"))
"""Weight of ``route_progress`` (run A had none; run B 1.5). NVIDIA's ``track_lin_vel`` weighs 2.0."""

FINAL_SCHEDULE_VALUES = (
    "action_rate_weight", "head_pose_bias_weight", "standing_envs", "head_pose_range", "com_range", "head_com_range"
)


@configclass
class MicroDuckCourseEnvCfg(MicroDuckVelocityRoughEnvCfg):
    """Fine-tune on our course: 64 lanes x 10 difficulty rows, 4,096 ducks."""

    def __post_init__(self):
        super().__post_init__()
        stock = self.scene.terrain
        self.scene.terrain = CourseTerrainImporterCfg(
            prim_path=stock.prim_path,
            terrain_type="generator",
            terrain_generator=course_generator(num_rows=10, num_cols=64, curriculum=True),
            max_init_terrain_level=5,
            collision_group=stock.collision_group,
            physics_material=stock.physics_material,
            debug_vis=False,
        )
        self.sim.physics_material = self.scene.terrain.physics_material
        stock_cmd = self.commands.base_velocity
        self.commands.base_velocity = CourseRouteCommandCfg(
            asset_name=stock_cmd.asset_name,
            resampling_time_range=stock_cmd.resampling_time_range,
            rel_standing_envs=stock_cmd.rel_standing_envs,
            rel_forward_envs=stock_cmd.rel_forward_envs,
            rel_turn_in_place_envs=stock_cmd.rel_turn_in_place_envs,
            debug_vis=False,
            ranges=stock_cmd.ranges,
        )
        self.events.reset_base = EventTermCfg(func=reset_on_route, mode="reset")
        self.curriculum.terrain_levels = CurriculumTermCfg(func=course_levels)
        self.episode_length_s = 25.0
        self.rewards.route_progress = RewardTermCfg(func=route_progress, weight=ROUTE_PROGRESS_WEIGHT)
        # start NVIDIA's schedules at their final values (see the module docstring)
        for name in FINAL_SCHEDULE_VALUES:
            term = getattr(self.curriculum, name)
            stages = term.params["modify_params"]["stages"]
            term.params["modify_params"]["stages"] = [(0, stages[-1][1])]

    def play_mode(self):
        """The real course: 16 lanes side by side at the real heights and wet-floor friction, all ducks from the start
        line along the route at 0.25 m/s, with our textured assets."""
        super().play_mode()
        self.scene.terrain.terrain_generator = course_generator(1, 16, curriculum=False, difficulty=(0.5, 0.5))
        self.scene.terrain.max_init_terrain_level = None
        self.scene.terrain.wet_friction = geo.E3["friction"]
        self.scene.terrain.course_visuals = True
        self.commands.base_velocity.rel_route_envs = 1.0
        self.commands.base_velocity.route_speed = (0.25, 0.25)
        self.commands.base_velocity.resampling_time_range = (1.0e6, 1.0e6)
        self.events.reset_base.params = {"from_start_prob": 1.0, "y_noise": 0.0, "yaw_noise": 0.0}
        self.episode_length_s = 40.0
        set_head_forward(self)


HEAD_RANGE_FINAL = ((-1.1, 1.1), (-1.1, 1.1), (-1.4, 1.4), (-0.31, 0.31))
"""NVIDIA's widest head-pose command range [rad] (the last stage of its ``head_pose_range`` schedule)."""


def set_head_forward(cfg) -> None:
    """Hold the head in its default pose (looking forward) instead of NVIDIA's random "look around" poses.

    NVIDIA's task commands a random head pose every 2-5 s so the real duck looks around while walking; the policy is
    blind, so the head's direction doesn't affect walking. For the course videos and scoring we want it forward.
    """
    cfg.commands.head_pose.ranges = tuple((0.0, 0.0) for _ in HEAD_RANGE_FINAL)
    cfg.curriculum.head_pose_range = None  # the schedule would widen the range again at the first reset
