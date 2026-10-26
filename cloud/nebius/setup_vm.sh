#!/usr/bin/env bash
# Runs ON the workstation (copy it and patches/ there first). Installs what phases 3-7 need, step by step,
# printing a header per step so the log reads as a record. Safe to re-run.
#   scp -r cloud/nebius/setup_vm.sh cloud/nebius/patches duck@<ip>:~/ && ssh duck@<ip> 'bash ~/setup_vm.sh 2>&1 | tee ~/setup.log'
# ACCEPT_OMNIVERSE_EULA=yes (only with the user's acceptance of the NVIDIA Omniverse License Agreement) also writes
# ~/isaac-env.sh with OMNI_KIT_ACCEPT_EULA=YES. Accepted by the user on 2026-10-26.
set -euo pipefail
ISAACLAB_COMMIT=727e4e43a          # Isaac Lab main on 2026-10-26 (Microduck tasks; the develop branch is gone)
step() { printf '\n===== [%s] %s =====\n' "$(date -u '+%H:%M:%SZ')" "$*"; }

step "1. System packages (vulkan-tools for the rendering check, tmux, ffmpeg for videos)"
sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq vulkan-tools tmux ffmpeg git git-lfs htop >/dev/null
echo "installed: $(dpkg -l vulkan-tools tmux ffmpeg | awk '/^ii/{print $2"="$3}' | tr '\n' ' ')"

step "2. GPU, driver and Vulkan"
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv
vulkaninfo --summary 2>/dev/null | grep -E "apiVersion|driverVersion|deviceName|deviceType" | head -8 || echo "vulkaninfo: no device"

step "3. uv"
if ! command -v uv >/dev/null && [ ! -x "$HOME/.local/bin/uv" ]; then curl -LsSf https://astral.sh/uv/install.sh | sh; fi
export PATH="$HOME/.local/bin:$PATH"
uv --version

step "4. Isaac Lab (main @ $ISAACLAB_COMMIT)"
cd "$HOME"
[ -d IsaacLab ] || git clone --quiet https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab && git fetch --quiet origin && git checkout --quiet "$ISAACLAB_COMMIT"
git log -1 --format='commit %h %cd %s' --date=short
ls source/isaaclab_tasks/isaaclab_tasks/contrib/microduck

step "5. uv sync (Newton + PyTorch cu130, no Isaac Sim yet)"
time uv sync 2>&1 | tail -5

step "6. Microduck tasks"
uv run isaaclab list_envs --keyword MicroDuck --show_presets 2>&1 | tail -15

step "7. Patch: Microduck events import Newton lazily (else Kit can't start: OpenUSD 26.08 vs Kit's 25.11)"
P="$HOME/patches/isaaclab-727e4e43a-microduck-lazy-newton-import.patch"
if git apply --reverse --check "$P" 2>/dev/null; then echo "already applied"; else git apply "$P" && echo "applied"; fi

step "8. Newton-only environment .venv-newton (training, headless video; no Kit, no EULA)"
UV_PROJECT_ENVIRONMENT="$HOME/IsaacLab/.venv-newton" uv sync --extra video 2>&1 | tail -2

step "9. Isaac Sim 6.2 in .venv (Kit: RTX rendering, scene work, WebRTC stream)"
time uv sync --extra isaacsim --extra video 2>&1 | tail -3
if [ "${ACCEPT_OMNIVERSE_EULA:-}" = yes ]; then
  printf '# Accepted by the user: NVIDIA Omniverse License Agreement (needed to run Kit / Isaac Sim).\nexport OMNI_KIT_ACCEPT_EULA=YES\nexport PATH=$HOME/.local/bin:$PATH\n' > "$HOME/isaac-env.sh"
  echo "wrote ~/isaac-env.sh"
else
  echo "Kit needs the Omniverse EULA: rerun with ACCEPT_OMNIVERSE_EULA=yes once the user has accepted it"
fi

step "done"
