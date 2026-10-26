#!/usr/bin/env bash
# Copy our code and course assets to the workstation, or results back.
#   cloud/nebius/sync.sh up                     training/isaaclab_ext/ -> ~/isaaclab_ext/ and assets/*/model.usd + textures
#                                               -> ~/isaac-obstacle-course/assets/ (what the course task and videos need)
#   cloud/nebius/sync.sh down REMOTE LOCAL      copy a file or folder from the VM (e.g. eval/before training/runs/x)
# The VM must be running (start.sh).
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
VM=$(vm_id); IP=$(vm_ip "$VM"); [ -n "$IP" ] || { log "VM not running"; exit 1; }
RS=(rsync -a -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new")
ROOT="$HERE/../.."
case "${1:-}" in
  up)
    "$HERE/ssh.sh" 'mkdir -p ~/isaaclab_ext ~/isaac-obstacle-course/assets'
    "${RS[@]}" --exclude __pycache__ "$ROOT/training/isaaclab_ext/" "$VM_USER@$IP:isaaclab_ext/"
    "${RS[@]}" --include="*/" --include="*/model.usd" --include="*/textures/**" --exclude="*" --prune-empty-dirs \
      "$ROOT/assets/" "$VM_USER@$IP:isaac-obstacle-course/assets/"
    log "synced isaaclab_ext and course assets to $IP" ;;
  down)
    [ -n "${2:-}" ] && [ -n "${3:-}" ] || { echo "usage: sync.sh down REMOTE LOCAL"; exit 1; }
    mkdir -p "$(dirname "$3")"
    "${RS[@]}" "$VM_USER@$IP:$2" "$3"
    log "copied $2 -> $3" ;;
  *) echo "usage: sync.sh up | down REMOTE LOCAL"; exit 1 ;;
esac
