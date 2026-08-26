#!/bin/bash

echo "=== 1. VERIFY WSL.CONF ==="
cat /etc/wsl.conf 2>&1
echo ""

echo "=== 2. VERIFY SYSTEMD SERVICES ENABLED ==="
echo -n "  k3s: "
systemctl is-enabled k3s 2>&1
echo -n "  tailscaled: "
systemctl is-enabled tailscaled 2>&1
echo ""

echo "=== 3. VERIFY TAILSCALE AUTH ==="
tailscale status 2>&1 | head -3
echo ""

echo "=== 4. VERIFY K3S NODE IP ==="
export KUBECONFIG=/home/german/.kube/config
kubectl get nodes -o wide 2>&1
echo ""

echo "=== 5. VERIFY KONG LB ==="
kubectl get svc kong-kong-proxy -n kong 2>&1
echo ""

echo "=== 6. VERIFY ALL PODS ==="
TOTAL=$(kubectl get pods -A --no-headers 2>/dev/null | wc -l)
RUNNING=$(kubectl get pods -A --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
echo "  Total: $TOTAL  Running: $RUNNING"
echo ""

echo "=== 7. VERIFY NO OLD IPs ==="
kubectl get svc kong-kong-proxy -n kong -o json 2>&1 | python3 -c "
import json,sys
svc=json.load(sys.stdin)
anns=svc.get('metadata',{}).get('annotations',{})
lbipam=anns.get('io.cilium/lb-ipam-ips','')
ext_ips=svc.get('spec',{}).get('externalIPs',[])
print(f'  lb-ipam-ips: {lbipam}')
print(f'  externalIPs: {ext_ips}')
if '192.168.100.210' in lbipam or '192.168.100.210' in str(ext_ips):
    print('  WARNING: old IP still present!')
else:
    print('  OK: no old IPs')
" 2>&1
echo ""

echo "DONE"
