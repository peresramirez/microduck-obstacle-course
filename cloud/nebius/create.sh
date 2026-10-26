#!/usr/bin/env bash
# Create the phase 3 workstation: security group (+ rules for this Mac's IP only), a 250 GiB boot disk from the
# CUDA 13 image, and the RTX PRO 6000 VM with a static public IP and our SSH key. Safe to re-run: existing pieces
# (found by name) are reused. COSTS MONEY once the VM runs ($1.80/h) and while the disk exists (~$0.58/day).
# Usage: cloud/nebius/create.sh
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"
IP="$(my_ip)"; [[ "$IP" =~ ^[0-9.]+$ ]] || { log "could not read this Mac's public IPv4"; exit 1; }
log "Mac public IPv4: $IP"

SG=$(id_by_name vpc security-group get-by-name --parent-id "$PROJECT" --name "$SG_NAME")
if [ -z "$SG" ]; then
  log "creating security group $SG_NAME (only this one is attached: the network's default group allows ALL ingress)"
  SG=$(nebius vpc security-group create --parent-id "$PROJECT" --network-id "$NETWORK" --name "$SG_NAME" --format json \
       | python3 -c "import json,sys; print(json.load(sys.stdin)['metadata']['id'])")
  for p in $TCP_PORTS; do
    nebius vpc security-rule create --parent-id "$SG" --name "in-tcp-$p-mac" --access allow --protocol tcp \
      --ingress-source-cidrs "$IP/32" --ingress-destination-ports "$p" --format json >/dev/null
  done
  for p in $UDP_PORTS; do
    nebius vpc security-rule create --parent-id "$SG" --name "in-udp-$p-mac" --access allow --protocol udp \
      --ingress-source-cidrs "$IP/32" --ingress-destination-ports "$p" --format json >/dev/null
  done
  nebius vpc security-rule create --parent-id "$SG" --name "out-any" --access allow --protocol any \
    --egress-destination-cidrs "0.0.0.0/0" --format json >/dev/null
fi
log "security group: $SG"

DISK=$(id_by_name compute disk get-by-name --parent-id "$PROJECT" --name "$DISK_NAME")
if [ -z "$DISK" ]; then
  log "creating boot disk $DISK_NAME ($DISK_GIB GiB network_ssd from $IMAGE_FAMILY)"
  DISK=$(nebius compute disk create --parent-id "$PROJECT" --name "$DISK_NAME" --type network_ssd \
           --size-gibibytes "$DISK_GIB" --source-image-family-image-family "$IMAGE_FAMILY" \
           --source-image-family-parent-id "$IMAGE_PARENT" --format json \
         | python3 -c "import json,sys; print(json.load(sys.stdin)['metadata']['id'])")
fi
log "boot disk: $DISK"

VM=$(vm_id)
if [ -z "$VM" ]; then
  log "creating VM $VM_NAME ($PLATFORM / $PRESET, on-demand, static public IP)"
  KEY="$(cat "$SSH_KEY.pub")"
  USERDATA=$(printf '#cloud-config\nusers:\n  - name: %s\n    sudo: ALL=(ALL) NOPASSWD:ALL\n    shell: /bin/bash\n    ssh_authorized_keys:\n      - %s\n' "$VM_USER" "$KEY")
  NICS=$(printf '[{"name":"eth0","subnet_id":"%s","ip_address":{},"public_ip_address":{"static":true},"security_groups":[{"id":"%s"}]}]' "$SUBNET" "$SG")
  VM=$(nebius compute instance create --parent-id "$PROJECT" --name "$VM_NAME" \
         --resources-platform "$PLATFORM" --resources-preset "$PRESET" \
         --boot-disk-existing-disk-id "$DISK" --boot-disk-attach-mode read_write \
         --network-interfaces "$NICS" --cloud-init-user-data "$USERDATA" --format json \
       | python3 -c "import json,sys; print(json.load(sys.stdin)['metadata']['id'])")
fi
log "VM: $VM, state $(vm_state "$VM")"
for _ in $(seq 60); do [ "$(vm_state "$VM")" = RUNNING ] && break; sleep 10; done
log "VM state: $(vm_state "$VM"), public IP $(vm_ip "$VM")"
