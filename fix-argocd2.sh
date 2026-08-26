#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ADD argocd TO KYVERNO EXCLUDES ==="
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
            if 'argocd' not in res['namespaces']:
                res['namespaces'].append('argocd')
print(json.dumps(p))
" 2>/dev/null > /tmp/patched.json
  if [ -s /tmp/patched.json ]; then
    kubectl apply -f /tmp/patched.json 2>&1 | head -1
  else
    echo "FAILED"
  fi
done
echo ""

echo "=== 2. RESTART ARGOCD SERVER ==="
kubectl rollout restart deploy argocd-server -n argocd 2>&1
echo ""

echo "=== 3. WAIT FOR ROLLOUT ==="
kubectl rollout status deploy argocd-server -n argocd --timeout=90s 2>&1
echo ""

echo "=== 4. CHECK PODS ==="
kubectl get pods -n argocd 2>&1
echo ""

echo "=== 5. WAIT 5s ==="
sleep 5
echo ""

echo "=== 6. TEST FROM WSL ==="
curl -sI http://argocd.mrrobot.fs/ 2>&1 | head -10
echo ""

echo "DONE"
