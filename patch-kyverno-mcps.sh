#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== PATCHING KYVERNO POLICIES TO EXCLUDE mcps NAMESPACE ==="

for POLICY in disallow-privileged-containers disallow-root-user require-env-label require-pod-labels require-resource-limits restrict-image-registries; do
  echo -n "  Patching $POLICY... "
  
  # Get the policy as JSON, add "mcps" to all namespace exclude lists, and re-apply
  k3s kubectl get cpol $POLICY -o json 2>/dev/null | python3 -c "
import json, sys
p = json.load(sys.stdin)
for rule in p['spec']['rules']:
    exc = rule.get('exclude', {})
    for cond in exc.get('any', []):
        res = cond.get('resources', {})
        if 'namespaces' in res:
            if 'mcps' not in res['namespaces']:
                res['namespaces'].append('mcps')
# Also check spec-level exclude
for cond in p['spec'].get('exclude', []):
    for c in cond.get('any', []):
        res = c.get('resources', {})
        if 'namespaces' in res:
            if 'mcps' not in res['namespaces']:
                res['namespaces'].append('mcps')
print(json.dumps(p))
" 2>/dev/null > /tmp/patched.json
  
  if [ -s /tmp/patched.json ]; then
    k3s kubectl apply -f /tmp/patched.json 2>&1 | head -1
  else
    echo "FAILED to generate patch"
  fi
done
echo ""

echo "=== VERIFY EXCLUSIONS ==="
for POLICY in disallow-privileged-containers disallow-root-user require-env-label require-pod-labels require-resource-limits restrict-image-registries; do
  echo -n "  $POLICY: "
  k3s kubectl get cpol $POLICY -o json 2>/dev/null | python3 -c "
import json,sys
p = json.load(sys.stdin)
found = False
for rule in p['spec']['rules']:
    for cond in rule.get('exclude',{}).get('any',[]):
        ns = cond.get('resources',{}).get('namespaces',[])
        if 'mcps' in ns:
            found = True
if found:
    print('mcps excluded OK')
else:
    print('mcps NOT in excludes')
" 2>/dev/null
done
echo ""

echo "=== RE-APPLY DEPLOYMENTS ==="
cd /tmp/mcps-deploy
k3s kubectl apply -f k8s/all-mcps.yaml 2>&1 | grep -E "deployment|error" | head -20
echo ""

echo "=== WAIT 30s ==="
sleep 30
echo ""

echo "=== POD STATUS ==="
k3s kubectl get pods -n mcps 2>&1
echo ""

echo "DONE"
