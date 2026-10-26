#!/usr/bin/env bash
# See the simulation live in Isaac Sim on your Mac.
#   cloud/nebius/stream.sh [CHECKPOINT]   start the VM if needed, run a policy with LIVESTREAM=1 in tmux session "stream",
#                                         wait for the WebRTC port, open the Isaac Sim WebRTC Streaming Client
#   cloud/nebius/stream.sh stop           end the stream session (the VM keeps running: stop it with stop.sh)
# CHECKPOINT: a .pt path on the VM; default = the newest checkpoint under ~/IsaacLab/logs/rsl_rl/, else NVIDIA's pretrained.
# COURSE=1 streams our obstacle course (16 lanes, our textured assets) instead of NVIDIA's rough terrain.
# VIEW=chase|overview picks the camera the viewport starts on (default chase; overview needs COURSE=1).
# DEPTH=1 (with COURSE=1) streams the phase 6b duck with the head ToF sensor (its 64 hit points drawn in the chase view);
# ROUTE=straight sends the ducks straight down the lane, so only what they sense gets them round the box.
# In the client: Server = the VM's IP (printed below), ports 49100 / 47998, Connect. The viewport camera is set from the
# VM (VIEWPORT_CAMERA), because the viewport's camera menu doesn't open through the client.
# Needs: the Omniverse EULA accepted on the VM (~/isaac-env.sh), the client installed (SETUP.md §9).
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
VM=$(vm_id); [ -n "$VM" ] || { log "no VM named $VM_NAME"; exit 1; }
if [ "${1:-}" = stop ]; then
  "$HERE/ssh.sh" 'tmux kill-session -t stream 2>/dev/null; echo "stream session ended"'; exit 0
fi
[ "$(vm_state "$VM")" = RUNNING ] || "$HERE/start.sh"
IP=$(vm_ip "$VM")
if [ "${COURSE:-0}" = 1 ]; then
  TASK=IsaacContrib-Velocity-Course-MicroDuck-$([ "${DEPTH:-0}" = 1 ] && echo Depth-)$([ "${VIEW:-chase}" = overview ] && echo OverviewCam || echo ChaseCam)
else
  TASK=IsaacContrib-Velocity-Rough-MicroDuck-ChaseCam
fi
"$HERE/ssh.sh" "CK='${1:-}' TASK='$TASK' VIEW='${VIEW:-chase}' ROUTE='${ROUTE:-detour}'"'
  [ -f ~/isaac-env.sh ] || { echo "no ~/isaac-env.sh: the Omniverse EULA has not been accepted on this VM"; exit 1; }
  if [ -z "$CK" ]; then CK=$(ls -t ~/IsaacLab/logs/rsl_rl/microduck_velocity_rough_backlash/*/model_*.pt 2>/dev/null | head -1); fi
  if [ -z "$CK" ]; then CK=$(ls ~/IsaacLab/.pretrained_checkpoints/rsl_rl/https/*/Assets/Isaac/6.2/Isaac/IsaacLab/PretrainedCheckpoints/rsl_rl/IsaacContrib-Velocity-Rough-MicroDuck_backlash_newtonmjwarp_none_rsl_rl.pt); fi
  echo "policy: $CK"; echo "task: $TASK, viewport: $VIEW, route: $ROUTE"
  tmux kill-session -t stream 2>/dev/null
  tmux new-session -d -s stream "source ~/isaac-env.sh; cd ~/IsaacLab; LIVESTREAM=1 VIEWPORT_CAMERA=$VIEW COURSE_ROUTE=$ROUTE ROUTE_PROGRESS_WEIGHT=1.5 PYTHONPATH=\$HOME/isaaclab_ext uv run --extra isaacsim --extra video python ~/isaaclab_ext/launch.py play --rl_library rsl_rl --task $TASK --checkpoint $CK --num_envs 16 presets=backlash --viz kit > ~/stream.log 2>&1"
  for i in $(seq 60); do sleep 5; ss -ltn 2>/dev/null | grep -q ":49100" && break; done
  ss -ltn 2>/dev/null | grep -q ":49100" && echo "stream server listening on 49100" || { echo "stream server did not start, see ~/stream.log"; exit 1; }'
log "connect the client to $IP (signal 49100 / stream 47998)"
open -a "Isaac Sim WebRTC Streaming Client" 2>/dev/null || log "client app not found: see SETUP.md §9"
