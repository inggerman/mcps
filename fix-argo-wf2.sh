#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ADD argo-workflows TO KYVERNO EXCLUDES ==="
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
            if 'argo-workflows' not in res['namespaces']:
                res['namespaces'].append('argo-workflows')
print(json.dumps(p))
" 2>/dev/null > /tmp/patched.json
  if [ -s /tmp/patched.json ]; then
    kubectl apply -f /tmp/patched.json 2>&1 | head -1
  else
    echo "FAILED"
  fi
done
echo ""

echo "=== 2. RESTART ARGO WORKFLOWS SERVER ==="
kubectl rollout restart deploy -n argo-workflows argo-workflows-server 2>&1
echo ""

echo "=== 3. WAIT FOR ROLLOUT ==="
kubectl rollout status deploy -n argo-workflows argo-workflows-server --timeout=60s 2>&1
echo ""

echo "=== 4. CHECK PODS ==="
kubectl get pods -n argo-workflows 2>&1
echo ""

echo "=== 5. CHECK SERVER ARGS ==="
kubectl get deploy -n argo-workflows argo-workflows-server -o jsonpath='{.spec.template.spec.containers[0].args}' 2>&1
echo ""
echo ""

echo "=== 6. TEST FROM WSL ==="
curl -sI http://workflows.mrrobot.fs/ 2>&1 | head -10
echo ""

echo "=== 7. TEST OAUTH REDIRECT ==="
curl -sI "http://workflows.mrrobot.fs/oauth2/redirect?redirect=http://workflows.mrrobot.fs/" 2>&1 | head -10
echo ""

echo "DONE"
