#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. ADD harbor TO KYVERNO EXCLUDES ==="
for POLICY in require-pod-labels disallow-root-user require-resource-limits disallow-privileged-containers restrict-image-registries; do
  echo -n "  Patching $POLICY... "
  kubectl get cpol $POLICY -o json 2>/dev/null | python3 -c "
import json, sys
p = json.load(sys.stdin)
for rule in p['spec']['rules']:
    exc = rule.get('exclude', {})
    for cond in exc.get('any', []):
        res = cond.get('resources', {})
        if 'namespaces' in res:
            if 'harbor' not in res['namespaces']:
                res['namespaces'].append('harbor')
print(json.dumps(p))
" 2>/dev/null > /tmp/patched.json
  if [ -s /tmp/patched.json ]; then
    kubectl apply -f /tmp/patched.json 2>&1 | head -1
  else
    echo "FAILED"
  fi
done
echo ""

echo "=== 2. APPLY HARBOR STS ==="
kubectl apply -f /tmp/harbor-database.yaml 2>&1
kubectl apply -f /tmp/harbor-redis.yaml 2>&1
echo ""

echo "=== 3. WAIT 45s ==="
sleep 45
echo ""

echo "=== 4. HARBOR STATUS ==="
kubectl get pods -n harbor 2>&1
echo ""

echo "=== 5. RESTART HARBOR CORE+JOBSERVICE ==="
kubectl rollout restart deploy -n harbor harbor-core harbor-jobservice 2>&1
sleep 20
echo ""

echo "=== 6. FINAL STATUS ==="
kubectl get pods -n harbor 2>&1
echo ""
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "DONE"
