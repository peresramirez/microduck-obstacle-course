#!/usr/bin/env bash
# If this Mac's public IP changed, point the security group's inbound rules at the new address.
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
IP="$(my_ip)"; SG=$(id_by_name vpc security-group get-by-name --parent-id "$PROJECT" --name "$SG_NAME")
nebius vpc security-rule list --parent-id "$SG" --format json | python3 -c "
import json,sys
for r in json.load(sys.stdin).get('items', []):
    if r['metadata']['name'].startswith('in-'): print(r['metadata']['id'], r['metadata']['name'])" |
while read -r RID NAME; do
  nebius vpc security-rule update --id "$RID" --ingress-source-cidrs "$IP/32" >/dev/null && log "$NAME -> $IP/32"
done
