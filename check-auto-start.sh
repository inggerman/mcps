#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. TAILSCALE STATUS ==="
systemctl is-enabled tailscaled 2>&1
systemctl is-active tailscaled 2>&1
tailscale status 2>&1 | head -5
echo ""

echo "=== 2. TAILSCALE IP ==="
tailscale ip -4 2>&1
echo ""

echo "=== 3. K3S STATUS ==="
systemctl is-enabled k3s 2>&1
systemctl is-active k3s 2>&1
echo ""

echo "=== 4. WSL.CONF ==="
cat /etc/wsl.conf 2>&1
echo ""

echo "=== 5. KONG SERVICE - CURRENT EXTERNAL IPs ==="
kubectl get svc kong-kong-proxy -n kong -o jsonpath='{.spec.externalIPs}' 2>&1
echo ""
kubectl get svc kong-kong-proxy -n kong -o jsonpath='{.metadata.annotations}' 2>&1
echo ""
echo ""

echo "=== 6. KONG LB STATUS ==="
kubectl get svc kong-kong-proxy -n kong 2>&1
echo ""

echo "=== 7. CILIUM LBIPAM ==="
kubectl get ciliumloadbalancerippool -A 2>&1 || echo "  No LBIPAM pools"
echo ""

echo "=== 8. CHECK IF 192.168.100.210 STILL IN KONG ==="
kubectl get svc kong-kong-proxy -n kong -o json 2>&1 | python3 -c "
import json,sys
svc=json.load(sys.stdin)
ext_ips=svc.get('spec',{}).get('externalIPs',[])
print(f'  externalIPs: {ext_ips}')
anns=svc.get('metadata',{}).get('annotations',{})
lbipam=anns.get('io.cilium/lb-ipam-ips','')
print(f'  lb-ipam-ips: {lbipam}')
ingress=svc.get('status',{}).get('loadBalancer',{}).get('ingress',[])
print(f'  lb ingress: {[i.get(\"ip\") for i in ingress]}')
" 2>&1
echo ""

echo "DONE"
