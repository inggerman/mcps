#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. PATCH DEPLOYMENT - auth-mode=client ==="
kubectl get deploy -n argo-workflows argo-workflows-server -o json 2>/dev/null | python3 -c "
import json, sys
dep = json.load(sys.stdin)
args = dep['spec']['template']['spec']['containers'][0]['args']
# Replace --auth-mode=server with --auth-mode=client
new_args = []
for a in args:
    if a == '--auth-mode=server':
        new_args.append('--auth-mode=client')
    else:
        new_args.append(a)
dep['spec']['template']['spec']['containers'][0]['args'] = new_args
print(json.dumps(dep))
" 2>/dev/null > /tmp/argo-wf-patched2.json
kubectl apply -f /tmp/argo-wf-patched2.json 2>&1
echo ""

echo "=== 2. WAIT FOR ROLLOUT ==="
kubectl rollout status deploy -n argo-workflows argo-workflows-server --timeout=60s 2>&1
echo ""

echo "=== 3. CHECK ARGS ==="
kubectl get deploy -n argo-workflows argo-workflows-server -o jsonpath='{.spec.template.spec.containers[0].args}' 2>&1
echo ""
echo ""

echo "=== 4. CHECK PODS ==="
kubectl get pods -n argo-workflows 2>&1
echo ""

echo "=== 5. WAIT 5s ==="
sleep 5
echo ""

echo "=== 6. TEST API ==="
curl -s http://workflows.mrrobot.fs/api/v1/info 2>&1
echo ""

echo "=== 7. TEST MAIN PAGE ==="
curl -sI http://workflows.mrrobot.fs/ 2>&1 | head -5
echo ""

echo "=== 8. SERVER LOGS ==="
kubectl logs -n argo-workflows -l app=argo-server --tail=10 2>&1
echo ""

echo "DONE"
