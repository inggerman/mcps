#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. EVENTS ==="
kubectl get events -n mcps --sort-by=.lastTimestamp 2>&1 | tail -10
echo ""

echo "=== 2. DESCRIBE A PENDING POD ==="
kubectl describe pod mcp-calendar-7f77f5dfdc-htlg8 -n mcps 2>&1 | tail -15
echo ""

echo "=== 3. CHECK KYVERNO POLICY VIOLATIONS ==="
kubectl get policyreports -A 2>&1 | head -5
echo ""

echo "=== 4. CHECK IF mcps IS IN EXCLUDES ==="
kubectl get cpol require-pod-labels -o jsonpath='{.spec.rules[0].exclude}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for cond in data.get('any', []):
    ns = cond.get('resources', {}).get('namespaces', [])
    print(f'  Excluded: {ns}')
    print(f'  mcps in list: {\"mcps\" in ns}')
" 2>&1
echo ""

echo "DONE"
