#!/usr/bin/env bash
# Show the workstation's state, IP and what is being billed.
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
VM=$(vm_id)
if [ -z "$VM" ]; then log "no VM named $VM_NAME"; else
  S=$(vm_state "$VM"); log "VM $VM_NAME ($VM): $S, public IP $(vm_ip "$VM" 2>/dev/null || echo -)"
  [ "$S" = RUNNING ] && log "billing: GPU VM \$1.80/h + disk" || log "billing: disk only (~\$0.58/day)"
fi
