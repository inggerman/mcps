#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. FIX KONG LBIPAM ANNOTATION ==="
kubectl annotate svc kong-kong-proxy -n kong "io.cilium/lb-ipam-ips=100.68.63.120" --overwrite 2>&1
echo ""

echo "=== 2. WAIT FOR CILIUM TO PICK UP ==="
sleep 10
echo ""

echo "=== 3. CHECK KONG SVC ==="
kubectl get svc kong-kong-proxy -n kong 2>&1
echo ""

echo "=== 4. VERIFY EXTERNAL IPs ==="
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

echo "=== 5. TEST ACCESS ==="
curl -sI -H "Host: gitea.mrrobot.fs" http://100.68.63.120/ 2>&1 | head -3
echo ""

echo "DONE"
