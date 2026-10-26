# Shared helpers for the workstation scripts. Source after workstation.env.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# SITE picks the region settings file: workstation.$SITE.env (+ workstation.$SITE.local.env) (default eu-south1; us-central1 had no capacity)
SITE="${SITE:-eu-south1}"
source "$HERE/workstation.$SITE.env"
# account IDs (PROJECT, NETWORK, SUBNET) live in a git-ignored file next to it
[[ -f "$HERE/workstation.$SITE.local.env" ]] && source "$HERE/workstation.$SITE.local.env"
for v in PROJECT NETWORK SUBNET; do
  [[ -n "${!v:-}" ]] || { echo "set $v in cloud/nebius/workstation.$SITE.local.env (see workstation.$SITE.env)" >&2; exit 1; }
done
SSH_KEY="${SSH_KEY/#\~/$HOME}"
log() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" >&2; }
# id of a resource by name, or empty (uses get-by-name; "NotFound" -> empty)
id_by_name() { nebius "$@" --format json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)['metadata']['id'])" 2>/dev/null || true; }
my_ip() { curl -s --max-time 10 https://api.ipify.org; }
vm_id() { id_by_name compute instance get-by-name --parent-id "$PROJECT" --name "$VM_NAME"; }
vm_state() { nebius compute instance get --id "$1" --format json | python3 -c "import json,sys; print(json.load(sys.stdin)['status']['state'])"; }
vm_ip() { nebius compute instance get --id "$1" --format json | python3 -c "
import json,sys; s=json.load(sys.stdin)['status']['network_interfaces'][0]['public_ip_address']['address']; print(s.split('/')[0])"; }
