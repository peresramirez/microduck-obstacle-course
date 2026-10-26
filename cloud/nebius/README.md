# Nebius workstation (phase 3)

One GPU VM for Isaac Lab training (Newton) and Isaac Sim (RTX rendering, WebRTC stream).

| | |
|---|---|
| Region / project | **eu-south1** (project ID in `workstation.eu-south1.local.env`, not in git) (us-central1 had no RTX PRO 6000 capacity on 2026-10-26; its settings stay in `workstation.us-central1.env`) |
| VM | `isaac-ws`, `gpu-rtx6000-a` / `1gpu-24vcpu-218gb`: RTX PRO 6000 Blackwell 96 GB, 24 vCPU, 218 GB RAM, static public IP, on-demand **$1.80/h while running** |
| Disk | `isaac-ws-boot`, 250 GiB network SSD from `ubuntu24.04-cuda13-latest`, kept between sessions (**~$17.75/month, ~$0.58/day**) |
| Firewall | `isaac-ws-sg` only: inbound TCP 22, 49100, 48010 and UDP 47998 from the Mac's IPv4 /32; outbound any. The network's default group allows **all** inbound traffic, so it is deliberately not attached |
| User | `duck` (SSH key `~/.ssh/id_ed25519`, added by cloud-init; never stored in the repo) |

## Scripts (run from `isaac-obstacle-course/`)

| Script | Does | Cost effect |
|---|---|---|
| `cloud/nebius/create.sh` | Security group + rules for this Mac's IP, boot disk, VM; reuses existing pieces by name | starts billing |
| `cloud/nebius/start.sh` | Start the stopped VM, print its IP | VM billing resumes |
| `cloud/nebius/stop.sh` | Stop the VM (**end of every session**) | VM billing stops; disk remains |
| `cloud/nebius/status.sh` | State, IP, what's billed | — |
| `cloud/nebius/ssh.sh [args]` | SSH in (e.g. `-L 6006:localhost:6006` for TensorBoard) | — |
| `cloud/nebius/update-ip.sh` | Point the inbound rules at the Mac's new IP | — |
| `CONFIRM=yes cloud/nebius/destroy.sh` | Delete VM, disk (data lost), rules, group | stops all billing |
| `cloud/nebius/setup_vm.sh` | Runs **on** the VM: packages, driver/Vulkan check, uv, Isaac Lab `main@727e4e43a`, `uv sync`, task list | — |

`SITE=us-central1` switches any script to the other region's settings.
