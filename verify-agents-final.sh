#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK HARBOR REPOS ==="
curl -s -k "https://harbor.mrrobot.fs/api/v2.0/projects/ghl/repositories" -u "admin:Harbor12345" 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data:
    name = r.get('name','')
    if 'agent' in name or 'mcp-web' in name or 'mcp-source' in name:
        print(f'  {name}')
" 2>&1 || echo "  Could not query Harbor"
echo ""

echo "=== 2. CHECK agents-platform-qa STATUS ==="
kubectl get application agents-platform-qa -n argocd -o jsonpath='{.status.operationState}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  phase: {data.get(\"phase\")}')
print(f'  message: {data.get(\"message\",\"\")}')
" 2>&1
echo ""

echo "=== 3. CHECK ERRIMAGEPULL DETAILS ==="
kubectl describe pod -n agents-platform agents-platform-api-7f5d68c5f5-4n8g2 2>&1 | grep -A3 "Failed\|Error" | head -10
echo ""

echo "=== 4. ALL APPS FINAL STATUS ==="
kubectl get applications -A 2>&1
echo ""

echo "DONE"
