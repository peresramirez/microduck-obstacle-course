#!/usr/bin/env bash
# Start the stopped workstation (billing for GPU/CPU/RAM resumes: $1.80/h). Prints the public IP.
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
VM=$(vm_id); [ -n "$VM" ] || { log "no VM named $VM_NAME"; exit 1; }
nebius compute instance start --id "$VM" >/dev/null
for _ in $(seq 60); do [ "$(vm_state "$VM")" = RUNNING ] && break; sleep 10; done
log "VM $VM $(vm_state "$VM"), public IP $(vm_ip "$VM")"
