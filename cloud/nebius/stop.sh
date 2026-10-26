#!/usr/bin/env bash
# Stop the workstation at the end of every session: GPU/CPU/RAM billing stops; the disk (~$0.58/day) is kept.
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
VM=$(vm_id); [ -n "$VM" ] || { log "no VM named $VM_NAME"; exit 1; }
nebius compute instance stop --id "$VM" >/dev/null
for _ in $(seq 60); do [ "$(vm_state "$VM")" = STOPPED ] && break; sleep 10; done
log "VM $VM $(vm_state "$VM")"
