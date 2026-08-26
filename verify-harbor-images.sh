#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

HARBOR_INTERNAL="harbor-core.harbor.svc.cluster.local"

echo "=== 1. CHECK HARBOR REPOS VIA API ==="
curl -s "http://$HARBOR_INTERNAL/api/v2.0/projects/ghl/repositories" -u "admin:Harbor12345" 2>&1 | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for r in data:
        name = r.get('name','')
        if 'agent' in name or 'mcp-web' in name or 'mcp-source' in name:
            print(f'  FOUND: {name}')
    print(f'  Total repos: {len(data)}')
except Exception as e:
    print(f'  Error: {e}')
" 2>&1
echo ""

echo "=== 2. CHECK SPECIFIC REPOS ==="
curl -s "http://$HARBOR_INTERNAL/api/v2.0/projects/ghl/repositories/agents-platform-api/artifacts" -u "admin:Harbor12345" 2>&1 | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'  agents-platform-api: {len(data)} artifacts')
    for a in data:
        print(f'    digest: {a.get(\"digest\",\"\")[:20]}, tags: {[t.get(\"name\") for t in a.get(\"tags\",[])]}')
except:
    print('  No artifacts or repo does not exist')
" 2>&1
echo ""

curl -s "http://$HARBOR_INTERNAL/api/v2.0/projects/ghl/repositories/agents-platform-worker/artifacts" -u "admin:Harbor12345" 2>&1 | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'  agents-platform-worker: {len(data)} artifacts')
    for a in data:
        print(f'    digest: {a.get(\"digest\",\"\")[:20]}, tags: {[t.get(\"name\") for t in a.get(\"tags\",[])]}')
except:
    print('  No artifacts or repo does not exist')
" 2>&1
echo ""

echo "=== 3. CHECK ARGO CD APPS STATUS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 4. CHECK PODS IN agents-platform ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== 5. FORCE REFRESH ARGO CD ==="
kubectl patch application agents-platform-prod -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "DONE"
