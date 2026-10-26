# Our Isaac Lab code

Python that runs **on the workstation** next to the Isaac Lab checkout (`~/IsaacLab`, `main` @ `727e4e43a` + the patch in `cloud/nebius/patches/`, applied by `setup_vm.sh`). Copy it, with the course assets, from the Mac:

```bash
cloud/nebius/start.sh && cloud/nebius/sync.sh up     # -> ~/isaaclab_ext/ and ~/isaac-obstacle-course/assets/
```

## Files

| File | What |
|---|---|
| `course_geometry.py` | The course's collision geometry and route (lane frame, metres): E1 cosine hump, E2 two sheets, E3 wet tile, E4 box, the route around the box, element extents. numpy + trimesh only, so `scenes/build_course_usd.py` uses it on the Mac too |
| `course_env_cfg.py` | **The course task** `MicroDuckCourseEnvCfg`: NVIDIA's rough Microduck task with our course as the terrain (one lane per 8 × 2 m tile, 10 difficulty rows × 64 lanes), wet tiles with their own friction (MuJoCo contact `priority = 1`), route-steering commands, spawns along the route, a progress curriculum, NVIDIA's schedules pinned at their final values. `play_mode()` = the real course, 16 lanes, our textured assets |
| `course_cam_cfg.py` | Camera variants of the course task: `-ChaseCam` (follows each duck), `-OverviewCam` (across 16 lanes), `-TrainCam` (high and wide over the training terrain). `VIEWPORT_CAMERA=chase|overview` points the Kit viewport (and the live stream) at one of them |
| `eval_course.py` | Scores a policy on the course: one lane per duck, start line, route at a set speed, one episode each. Writes a JSON report (finished, falls and where, box contact, time per element, commanded vs measured speed) |
| `chase_cam_cfg.py` | Phase 3–4: `RoughChaseCamEnvCfg` / `RoughOverviewCamEnvCfg` on NVIDIA's rough terrain; `follow_robot` is reused by the course chase camera |
| `register.py` | Registers all our task ids with gymnasium (string entry points, so Newton isn't imported before Kit starts) |
| `launch.py` | `launch.py play|train <isaaclab play/train arguments>`: registers our tasks, then runs Isaac Lab's normal CLI |
| `play_chase_cam.py` | Phase 3 wrapper, kept for the record (`launch.py play` does the same) |

Task ids: `IsaacContrib-Velocity-Rough-MicroDuck-{ChaseCam,OverviewCam}` and `IsaacContrib-Velocity-Course-MicroDuck[-ChaseCam|-OverviewCam|-TrainCam]`.

## Reproduce phases 5–7

The exact scripts that ran are in `training/runs/`:

| Phase | Script (run on the VM) | What |
|---|---|---|
| 5b before | `training/runs/phase5-before/run_before.sh` | NVIDIA's and our phase 4 checkpoints on the real course (128 ducks each, headless), then RTX videos (16-lane overview, chase camera) |
| 6 train | `training/runs/phase6-course/run_train.sh` | 3,000-iteration fine-tune of NVIDIA's checkpoint on the course, 4,096 ducks |
| 7 validate | `training/runs/phase7-validate/run_validate.sh` | The course policy vs NVIDIA's on the real course, faster, harder and flat, plus RTX videos |

```bash
# on the Mac
cloud/nebius/sync.sh up
scp -i ~/.ssh/id_ed25519 training/runs/phase5-before/run_before.sh duck@<vm-ip>:
cloud/nebius/ssh.sh 'tmux new -d -s before "bash ~/run_before.sh > ~/run_before.log 2>&1"'
cloud/nebius/sync.sh down eval/before training/runs/phase5-before/eval/     # when it prints "done"
```

Headless runs use the Newton-only environment (`UV_PROJECT_ENVIRONMENT=~/IsaacLab/.venv-newton`, `--extra video`). Kit/RTX runs need `source ~/isaac-env.sh` (the accepted Omniverse EULA) and both extras (`--extra isaacsim --extra video`).

## Watch it live

```bash
COURSE=1 VIEW=overview cloud/nebius/stream.sh <checkpoint.pt on the VM>   # or VIEW=chase
```
