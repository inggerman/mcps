#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. PATCH - REMOVE auth-mode FLAG ENTIRELY ==="
kubectl get deploy -n argo-workflows argo-workflows-server -o json 2>/dev/null | python3 -c "
import json, sys
dep = json.load(sys.stdin)
args = dep['spec']['template']['spec']['containers'][0]['args']
new_args = [a for a in args if not a.startswith('--auth-mode')]
dep['spec']['template']['spec']['containers'][0]['args'] = new_args
print(json.dumps(dep))
" 2>/dev/null > /tmp/argo-wf-noauth.json
kubectl apply -f /tmp/argo-wf-noauth.json 2>&1
echo ""

echo "=== 2. WAIT FOR ROLLOUT ==="
kubectl rollout status deploy -n argo-workflows argo-workflows-server --timeout=90s 2>&1
echo ""

echo "=== 3. CHECK ARGS ==="
kubectl get deploy -n argo-workflows argo-workflows-server -o jsonpath='{.spec.template.spec.containers[0].args}' 2>&1
echo ""
echo ""

echo "=== 4. PODS ==="
kubectl get pods -n argo-workflows 2>&1
echo ""

echo "=== 5. WAIT 5s ==="
sleep 5
echo ""

echo "=== 6. LOGS ==="
kubectl logs -n argo-workflows -l app.kubernetes.io/component=server --tail=15 2>&1
echo ""

echo "DONE"
