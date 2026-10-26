"""Run a policy through our obstacle course and score every duck (phases 5b and 7).

Each duck gets its own lane of the real course (crest 3.3 cm, two 1 cm sheets, wet tile mu 0.3, the box), starts on
the start line facing along the lane, and is steered along the route at ``--speed``. One episode per duck, no restarts.
Per duck it records: how far it got, whether and where it fell, when it finished, how long its body was inside the
box's footprint, and its time on each element. Writes ``--out`` (JSON) and prints a summary.

Run on the workstation (headless with Newton, or with Kit for video):

    cd ~/IsaacLab && export UV_PROJECT_ENVIRONMENT=~/IsaacLab/.venv-newton      # headless
    PYTHONPATH=~/isaaclab_ext uv run --extra video python ~/isaaclab_ext/eval_course.py \\
        --task IsaacContrib-Velocity-Course-MicroDuck --checkpoint <model.pt> --num_envs 64 presets=backlash \\
        --out ~/eval/before.json [--speed 0.25] [--seconds 40] [--wet_friction 0.3] [--label before]

With Kit (``.venv``, ``source ~/isaac-env.sh``, ``--extra isaacsim --extra video``) add for example
``--task …-OverviewCam --video sensor:overview_cam --video_length 1500``.
"""

import argparse
import contextlib
import json
import os
import sys
import time

import register  # noqa: F401  (registers our task ids)

from isaaclab_rl.entrypoints.backends import play_rsl_rl as pb

import course_geometry as geo


def _course_args() -> tuple[argparse.Namespace, list[str]]:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--out", required=True, help="JSON report path")
    p.add_argument("--label", default="", help="name of this run in the report")
    p.add_argument("--seconds", type=float, default=40.0, help="time limit per duck [s]")
    p.add_argument("--speed", type=float, default=0.25, help="commanded walking speed along the route [m/s]")
    p.add_argument("--wet_friction", type=float, default=geo.E3["friction"])
    p.add_argument("--lanes", type=int, default=None, help="lanes side by side (default: one per duck, max 64)")
    p.add_argument("--no_visuals", action="store_true", help="skip our textured assets (headless scoring)")
    p.add_argument("--height_scale", type=float, default=1.0, help="E1 crest and E2 rise x this (1 = real course)")
    p.add_argument("--route", choices=("detour", "straight"), default="detour",
                   help="steer around the box (detour) or straight down the lane through it (the duck must avoid it)")
    p.add_argument("--box_x", type=float, default=None,
                   help="move the E4 box's start to this lane x [m] (trained: 5.1); use with --route straight")
    p.add_argument("--head", choices=("forward", "random"), default="forward",
                   help="head held forward (default) or NVIDIA's random look-around poses")
    return p.parse_known_args(sys.argv[1:])


def _where(x: float) -> str:
    for name, (x0, x1) in geo.ELEMENTS.items():
        if x0 - 0.05 <= x <= x1 + 0.05:
            return name
    if x < geo.START_X:
        return "before start"
    return "past finish" if x >= geo.FINISH_X else "flat floor"


def main() -> None:
    import torch

    from isaaclab.utils import to_dict
    from isaaclab.utils.assets import retrieve_file_path
    from isaaclab_tasks.utils import resolve_task_config

    ours, rest = _course_args()
    if ours.box_x is not None:  # before the task config is imported: terrain, visuals and scoring read geo.E4
        geo.E4["x0"] = ours.box_x
    args_cli = pb._parse_args(rest)
    env_cfg, agent_cfg = resolve_task_config(args_cli.task, args_cli.agent, play_mode=True)
    num_envs = args_cli.num_envs or env_cfg.scene.num_envs
    lanes = ours.lanes or min(num_envs, 64)
    env_cfg.scene.terrain.terrain_generator.num_cols = lanes
    env_cfg.scene.terrain.wet_friction = ours.wet_friction
    env_cfg.scene.terrain.course_visuals = not ours.no_visuals
    env_cfg.scene.terrain.terrain_generator.sub_terrains["course"].scale_range = (ours.height_scale, ours.height_scale)
    env_cfg.commands.base_velocity.straight_route_prob = 1.0 if ours.route == "straight" else 0.0
    if ours.head == "random":  # play_mode holds the head forward; restore NVIDIA's random head poses
        from course_env_cfg import HEAD_RANGE_FINAL

        env_cfg.commands.head_pose.ranges = HEAD_RANGE_FINAL
    env_cfg.commands.base_velocity.route_speed = (ours.speed, ours.speed)
    env_cfg.episode_length_s = ours.seconds
    pb.pre_launch_video_config(env_cfg, args_cli)

    with pb.launch_simulation(env_cfg, args_cli), contextlib.ExitStack() as cleanup:
        agent_cfg = pb.cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
        pb.apply_env_overrides(args_cli, env_cfg)
        env_cfg.seed = agent_cfg.seed
        checkpoint = retrieve_file_path(args_cli.checkpoint)
        out_dir = os.path.dirname(os.path.abspath(ours.out))
        os.makedirs(out_dir, exist_ok=True)
        env_cfg.log_dir = out_dir
        pb.apply_video_recording(env_cfg, out_dir, args_cli, subdir="videos", checkpoint_path=checkpoint)
        env = pb.create_isaaclab_env(args_cli.task, env_cfg, args_cli, convert_marl_to_single_agent=False)
        cleanup.callback(lambda: pb.close_env(env))
        env = pb.RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
        runner = pb.OnPolicyRunner(env, to_dict(agent_cfg), log_dir=None, device=agent_cfg.device)
        runner.load(checkpoint)
        policy = runner.get_inference_policy(device=env.unwrapped.device)

        base = env.unwrapped
        robot = base.scene["robot"]
        n, dev, dt = base.num_envs, base.device, base.step_dt
        (bx0, by0, _), (bx1, by1, bz1) = geo.box_bounds()
        pad = 0.01
        last_x = torch.zeros(n, device=dev)
        last_y = torch.zeros(n, device=dev)
        max_x = torch.full((n,), -1.0, device=dev)
        finish_t = torch.full((n,), float("nan"), device=dev)
        box_steps = torch.zeros(n, device=dev)
        elem_steps = {k: torch.zeros(n, device=dev) for k in geo.ELEMENTS}
        done_at = torch.full((n,), -1, dtype=torch.long, device=dev)
        cmd_term = base.command_manager.get_term("base_velocity")
        sum_cmd = torch.zeros(n, 3, device=dev)  # commanded vx, vy, wz while walking the route
        sum_vel = torch.zeros(n, 3, device=dev)  # measured body-frame vx, vy, wz
        walk_steps = torch.zeros(n, device=dev)
        fell = torch.zeros(n, dtype=torch.bool, device=dev)
        steps = int(round(ours.seconds / dt))
        obs = env.get_observations()
        t0 = time.time()
        with torch.inference_mode():
            for k in range(steps + 1):
                active = done_at < 0
                origins = base.scene.env_origins
                root = robot.data.root_pos_w.torch[:, :3] - origins
                last_x = torch.where(active, root[:, 0], last_x)
                last_y = torch.where(active, root[:, 1], last_y)
                max_x = torch.where(active, torch.maximum(max_x, root[:, 0]), max_x)
                newly = active & torch.isnan(finish_t) & (root[:, 0] >= geo.FINISH_X)
                finish_t[newly] = k * dt
                bodies = robot.data.body_pos_w.torch - origins.unsqueeze(1)
                in_box = ((bodies[..., 0] > bx0 - pad) & (bodies[..., 0] < bx1 + pad) & (bodies[..., 1] > by0 - pad)
                          & (bodies[..., 1] < by1 + pad) & (bodies[..., 2] < bz1 + pad)).any(dim=1)
                box_steps += (in_box & active).float()
                walking = active & (root[:, 0] < geo.FINISH_X)
                vel_b = torch.cat([robot.data.root_lin_vel_b.torch[:, :2], robot.data.root_ang_vel_b.torch[:, 2:3]], 1)
                sum_cmd += cmd_term.command[:, :3] * walking.unsqueeze(1)
                sum_vel += vel_b * walking.unsqueeze(1)
                walk_steps += walking.float()
                for name, (x0, x1) in geo.ELEMENTS.items():
                    elem_steps[name] += (active & (root[:, 0] >= x0) & (root[:, 0] <= x1)).float()
                if os.environ.get("PRINT_TOF") and "tof" in base.scene.sensors and k in (0, 50, 250, 600, 1000):
                    d = base.scene["tof"].data.ray_distances.torch[0].reshape(8, 8).clamp(max=9.99)
                    print(f"[tof] duck 0 at x={float(root[0, 0]):.2f} m, distances [m] (top row first):\n"
                          + "\n".join(" ".join(f"{v:4.2f}" for v in row) for row in d.tolist()), flush=True)
                if k == steps or not bool(active.any()):
                    break
                obs, _, dones, _ = env.step(policy(obs))
                policy.reset(dones)
                ended = active & dones.bool().to(dev)
                if bool(ended.any()):
                    fell_now = base.termination_manager.get_term("fell_over").bool()
                    fell |= ended & fell_now
                    done_at[ended] = k + 1
        wall = time.time() - t0

        ducks = []
        for i in range(n):
            mx = float(max_x[i])
            ducks.append({
                "duck": i,
                "finished": bool(not torch.isnan(finish_t[i])),
                "finish_time_s": None if torch.isnan(finish_t[i]) else round(float(finish_t[i]), 2),
                "fell": bool(fell[i]),
                "end": "fell" if fell[i] else ("finished" if not torch.isnan(finish_t[i]) else "time limit"),
                "end_x": round(float(last_x[i]), 3),
                "end_y": round(float(last_y[i]), 3),
                "end_where": _where(float(last_x[i])),
                "max_x": round(mx, 3),
                "box_contact_s": round(float(box_steps[i]) * dt, 2),
                "mean_cmd_vx_vy_wz": [round(float(v), 3) for v in sum_cmd[i] / max(float(walk_steps[i]), 1.0)],
                "mean_vel_vx_vy_wz": [round(float(v), 3) for v in sum_vel[i] / max(float(walk_steps[i]), 1.0)],
                "seconds_on": {k: round(float(v[i]) * dt, 2) for k, v in elem_steps.items()},
            })
        fin = [d for d in ducks if d["finished"]]
        summary = {
            "ducks": n,
            "finished": len(fin),
            "finished_pct": round(100 * len(fin) / n, 1),
            "fell": sum(d["fell"] for d in ducks),
            "touched_box": sum(d["box_contact_s"] > 0 for d in ducks),
            "mean_finish_time_s": round(sum(d["finish_time_s"] for d in fin) / len(fin), 2) if fin else None,
            "mean_cmd_vx": round(sum(d["mean_cmd_vx_vy_wz"][0] for d in ducks) / n, 3),
            "mean_vx": round(sum(d["mean_vel_vx_vy_wz"][0] for d in ducks) / n, 3),
            "passed": {name: sum(d["max_x"] > x1 for d in ducks) for name, (_, x1) in geo.ELEMENTS.items()},
            "falls_at": {},
            "stopped_at": {},
        }
        for d in ducks:
            if d["fell"]:
                summary["falls_at"][d["end_where"]] = summary["falls_at"].get(d["end_where"], 0) + 1
            elif not d["finished"]:
                summary["stopped_at"][d["end_where"]] = summary["stopped_at"].get(d["end_where"], 0) + 1
        report = {
            "label": ours.label,
            "task": args_cli.task,
            "checkpoint": checkpoint,
            "speed_mps": ours.speed,
            "seconds": ours.seconds,
            "wet_friction": ours.wet_friction,
            "height_scale": ours.height_scale,
            "head": ours.head,
            "route": ours.route,
            "box_x": geo.E4["x0"],
            "lanes": lanes,
            "course": {"E1_crest_m": geo.E1["crest"], "E2_rise_m": geo.E2["rise"], "route": geo.ROUTE,
                       "finish_x": geo.FINISH_X, "elements": geo.ELEMENTS},
            "wall_time_s": round(wall, 1),
            "summary": summary,
            "ducks": ducks,
        }
        with open(ours.out, "w") as f:
            json.dump(report, f, indent=1)
        print(f"[eval] {ours.label or 'run'}: {json.dumps(summary)}", flush=True)
        print(f"[eval] report -> {ours.out}", flush=True)


if __name__ == "__main__":
    main()
