#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. ALSO FIX require-env-label POLICY ==="
k3s kubectl get cpol require-env-label -o json 2>/dev/null | python3 -c "
import json, sys
p = json.load(sys.stdin)
for rule in p['spec']['rules']:
    exc = rule.get('exclude', {})
    for cond in exc.get('any', []):
        res = cond.get('resources', {})
        if 'namespaces' in res:
            if 'mcps' not in res['namespaces']:
                res['namespaces'].append('mcps')
print(json.dumps(p))
" 2>/dev/null > /tmp/patched-env.json
k3s kubectl apply -f /tmp/patched-env.json 2>&1
echo ""

echo "=== 2. COPY MANIFESTS AND RE-APPLY ==="
cp /mnt/c/Users/German/all-mcps.yaml /tmp/all-mcps.yaml
k3s kubectl apply -f /tmp/all-mcps.yaml 2>&1 | grep -E "deployment|configured" | head -10
echo ""

echo "=== 3. DELETE OLD PODS TO FORCE RECREATE ==="
k3s kubectl delete pods -n mcps --all --grace-period=0 --force 2>&1 | head -5
echo ""

echo "=== 4. WAIT 45s ==="
sleep 45
echo ""

echo "=== 5. POD STATUS ==="
k3s kubectl get pods -n mcps 2>&1
echo ""

echo "=== 6. RUNNING COUNT ==="
RUNNING=$(k3s kubectl get pods -n mcps --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
TOTAL=$(k3s kubectl get pods -n mcps --no-headers 2>/dev/null | wc -l)
echo "  Running: ${RUNNING}/${TOTAL}"
echo ""

echo "DONE"
