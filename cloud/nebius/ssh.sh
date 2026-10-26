#!/usr/bin/env bash
# SSH into the workstation (extra args are passed to ssh, e.g. -L 6006:localhost:6006 for TensorBoard).
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
VM=$(vm_id); IP=$(vm_ip "$VM")
exec ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 "$VM_USER@$IP" "$@"
