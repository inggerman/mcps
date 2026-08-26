#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. PATCH DEPLOYMENT - auth-mode=none ==="
kubectl get deploy -n argo-workflows argo-workflows-server -o json 2>/dev/null | python3 -c "
import json, sys
dep = json.load(sys.stdin)
args = dep['spec']['template']['spec']['containers'][0]['args']
new_args = []
for a in args:
    if a.startswith('--auth-mode='):
        new_args.append('--auth-mode=none')
    else:
        new_args.append(a)
if '--auth-mode=none' not in new_args:
    new_args.append('--auth-mode=none')
dep['spec']['template']['spec']['containers'][0]['args'] = new_args
print(json.dumps(dep))
" 2>/dev/null > /tmp/argo-wf-none.json
kubectl apply -f /tmp/argo-wf-none.json 2>&1
echo ""

echo "=== 2. WAIT FOR ROLLOUT ==="
kubectl rollout status deploy -n argo-workflows argo-workflows-server --timeout=60s 2>&1
echo ""

echo "=== 3. CHECK ARGS ==="
kubectl get deploy -n argo-workflows argo-workflows-server -o jsonpath='{.spec.template.spec.containers[0].args}' 2>&1
echo ""

echo "=== 4. WAIT 5s ==="
sleep 5
echo ""

echo "=== 5. SERVER LOGS ==="
kubectl logs -n argo-workflows -l app.kubernetes.io/component=server --tail=10 2>&1
echo ""

echo "DONE"
