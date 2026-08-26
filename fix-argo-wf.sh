#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. REMOVE kong-key-auth FROM INGRESS ==="
kubectl annotate ingress argo-workflows-kong -n argo-workflows konghq.com/plugins- 2>&1
echo ""

echo "=== 2. PATCH ARGO WORKFLOWS SERVER DEPLOYMENT - authMode=server ==="
kubectl get deploy -n argo-workflows argo-workflows-server -o json 2>/dev/null | python3 -c "
import json, sys
dep = json.load(sys.stdin)
# Add --auth-mode=server to args
args = dep['spec']['template']['spec']['containers'][0]['args']
if '--auth-mode=server' not in args:
    args.append('--auth-mode=server')
dep['spec']['template']['spec']['containers'][0]['args'] = args
print(json.dumps(dep))
" 2>/dev/null > /tmp/argo-wf-patched.json
kubectl apply -f /tmp/argo-wf-patched.json 2>&1
echo ""

echo "=== 3. WAIT FOR ROLLOUT ==="
kubectl rollout status deploy -n argo-workflows argo-workflows-server --timeout=60s 2>&1
echo ""

echo "=== 4. CHECK NEW ARGS ==="
kubectl get deploy -n argo-workflows argo-workflows-server -o jsonpath='{.spec.template.spec.containers[0].args}' 2>&1
echo ""
echo ""

echo "=== 5. TEST FROM WINDOWS ==="
curl -sI http://workflows.mrrobot.fs/ 2>&1 | head -10
echo ""

echo "=== 6. TEST OAUTH REDIRECT ==="
curl -sI "http://workflows.mrrobot.fs/oauth2/redirect?redirect=http://workflows.mrrobot.fs/" 2>&1 | head -10
echo ""

echo "=== 7. CHECK INGRESS ANNOTATIONS ==="
kubectl get ingress argo-workflows-kong -n argo-workflows -o jsonpath='{.metadata.annotations}' 2>&1
echo ""

echo "DONE"
