#!/usr/bin/env bash
# Delete the workstation completely: VM, boot disk (ALL DATA ON IT IS LOST), security group rules, security group.
# Only for when the project is finished or the region must change; for pauses use stop.sh (keeps the disk).
# Usage: CONFIRM=yes [SITE=eu-south1] cloud/nebius/destroy.sh
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
[ "${CONFIRM:-}" = yes ] || { log "refusing: set CONFIRM=yes (this deletes the disk and everything on it)"; exit 1; }
VM=$(vm_id); [ -n "$VM" ] && { log "deleting VM $VM"; nebius compute instance delete --id "$VM" >/dev/null; }
DISK=$(id_by_name compute disk get-by-name --parent-id "$PROJECT" --name "$DISK_NAME")
[ -n "$DISK" ] && { log "deleting disk $DISK"; nebius compute disk delete --id "$DISK" >/dev/null; }
SG=$(id_by_name vpc security-group get-by-name --parent-id "$PROJECT" --name "$SG_NAME")
if [ -n "$SG" ]; then
  # a security group can only be deleted once it has no rules
  for r in $(nebius vpc security-rule list --parent-id "$SG" --format json | python3 -c "import json,sys; [print(i['metadata']['id']) for i in json.load(sys.stdin).get('items',[])]"); do
    nebius vpc security-rule delete --id "$r" >/dev/null
  done
  log "deleting security group $SG"; nebius vpc security-group delete --id "$SG" >/dev/null
fi
log "done"
