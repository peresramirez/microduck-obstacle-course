# How this project was built: the tooling

The project was built by an AI agent, **Claude Code**, working with a person who decided what to build and approved every paid or public step. This page lists everything the agent used, what each tool did, and the exact versions. How to install and run the project: [Getting started](../README.md#getting-started).

![Claude Code](https://img.shields.io/badge/agent-Claude%20Code-D97757?logo=anthropic&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-FreeCAD%20%C2%B7%20Blender-6E56CF)
![Nebius CLI](https://img.shields.io/badge/cloud-Nebius%20CLI%200.12.293-0B1D3A)
![uv](https://img.shields.io/badge/python-uv-DE5FE9?logo=uv&logoColor=white)

## The agent

| Tool | Version | What it did here |
|---|---|---|
| **Claude Code** | CLI, Claude Opus 5.5 | Planned the course, wrote every script, drove FreeCAD and Blender, rented and set up the cloud GPU, wrote the Isaac Lab tasks, ran and watched training, scored results, recorded videos and wrote the docs. Every decision was logged in the project's phase docs and notes (kept locally, not in this repository) |
| Claude Code subagents | — | Research tasks in parallel, e.g. the study of NVIDIA's released code (kept with the local notes) |
| Claude Code skills | `flux-image-best-practices` (pinned in `skills-lock.json`) | Prompting guide for the FLUX concept images |
| Computer use | — | Operated the Isaac Sim WebRTC Streaming Client on the Mac (connect, browse the scene tree) while a script recorded that window only |

## MCP servers (the agent's hands in the 3D apps)

The Model Context Protocol (MCP) lets the agent call tools inside other programs. Both servers are pinned in [`.mcp.json`](../.mcp.json).

| Server | Version | Talks to | Used for |
|---|---|---|---|
| **FreeCAD MCP** ([neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp)) | server `freecad-mcp==0.1.28`, add-on v0.1.28 | FreeCAD 1.1.4, XML-RPC on `127.0.0.1:9875` | Parametric shapes of every obstacle, STEP and mesh export, headless exports via `freecadcmd` |
| **Blender MCP** ([ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender)) | server `mcp-for-blender==2.2.4`, add-on v1.8 | Blender 5.2.2, JSON over TCP on `127.0.0.1:9876` | Materials, lights, cameras, previews, USD/GLB export, the course fly-through |
| Exa, Tavily (user-level) | — | Web search and page reading | Research on NVIDIA's workflow, Nebius, Isaac Lab |

When the MCP tools weren't loaded in a session, the agent used the same add-on endpoints directly through [`tools/apps.py`](../tools/apps.py) (`apps.py exec freecad|blender script.py`). Every script sent this way was archived as it was sent (`tools/as_run.sh`, kept locally); the clean, replayable versions are each obstacle's `build/` scripts.

## Command-line tools

| Tool | Version | Used for |
|---|---|---|
| **Nebius CLI** (`nebius`) | 0.12.293 | Create, start, stop and delete the GPU VM, disk, IP and firewall rules ([`cloud/nebius/`](../cloud/nebius/)) |
| `ssh`, `rsync` | system | Run commands on the VM; copy code up and results down (`cloud/nebius/sync.sh`) |
| `tmux` (on the VM) | Ubuntu 24.04 package | Keep training running when the connection drops |
| **uv** / `uvx` | — | Python environments everywhere: the MCP servers, our tools (`uv run --with …`), Isaac Lab on the VM |
| `gh` (GitHub CLI) | — | Searching Isaac Lab pull requests and repos |
| `git` | 2.54 | Version control; reading NVIDIA's and Pollen's public repositories |
| `ffmpeg` | Homebrew | Encode recordings, trim clips, contact sheets, the showreel |
| Google Chrome (headless) | — | Render text overlays and check pages and diagrams (`tools/readme_diagrams.py` draws the README's SVGs) |
| Mermaid CLI | `@mermaid-js/mermaid-cli@11.4.2` (via `npx`) | Architecture diagrams (`tools/render_diagrams.sh`) |
| `screencapture` (macOS) | — | Record one app window only (`tools/record_window.py`) |

## Desktop apps

| App | Version | Role |
|---|---|---|
| FreeCAD | 1.1.4 (Homebrew cask) | Exact, parametric obstacle shapes |
| Blender | 5.2.2 LTS | Materials, rendering, USD export |
| Isaac Sim WebRTC Streaming Client | 2.0.0 (macOS, aarch64) | Watch and use Isaac Sim running on the cloud GPU |

## Cloud and the NVIDIA stack

| Item | Version | Notes |
|---|---|---|
| Nebius VM | `gpu-rtx6000-a`, preset `1gpu-24vcpu-218gb`, eu-south1 | NVIDIA RTX PRO 6000 Blackwell, 96 GB; $1.80 per hour while running. Deleted after the project |
| OS image | `ubuntu24.04-cuda13-latest` | Driver 610.57.04, CUDA 13.3, Vulkan 1.4 |
| Isaac Lab | `main` @ `727e4e43a` (3.0 line) | Training framework; Microduck tasks; plus our one-line patch (`cloud/nebius/patches/`) |
| Isaac Sim | 6.2.0.0 | RTX rendering, cameras, live stream |
| Newton | with Isaac Lab | Physics, MuJoCo-Warp (MJWarp) solver, BAM servo model |
| RSL-RL | with Isaac Lab | PPO training |

## APIs and Python libraries

| Name | Used for |
|---|---|
| Black Forest Labs **FLUX 3** API | One concept image per obstacle (`tools/flux_generate.py`; key in `.env`, never committed) |
| `usd-core` | Read and write USD: checks, the scene file `course.usd` |
| `trimesh`, `numpy` | Course collision geometry (`course_geometry.py`) |
| `matplotlib`, `tensorboard` | Training and result charts |
| `pyobjc-framework-Quartz` | Find the window to record |

## What the person did

- Chose the goal, the course and the cloud GPU, and asked for every step to be documented and reproducible.
- Accepted the NVIDIA Omniverse licence and the streaming client licence.
- Approved paid cloud use, the deletion of the workstation, and each commit.
- Asked the key questions that shaped phase 6b (the head sensor) and the "can and can't" documentation.
