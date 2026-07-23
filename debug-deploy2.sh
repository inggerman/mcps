#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. RE-APPLY MANIFESTS WITH FULL OUTPUT ==="
cd /tmp/mcps-deploy
k3s kubectl apply -f k8s/all-mcps.yaml 2>&1 | head -80
echo ""

echo "=== 2. CHECK DEPLOYMENTS ==="
k3s kubectl get deploy -n mcps 2>&1
echo ""

echo "=== 3. CHECK EVENTS FOR ERRORS ==="
k3s kubectl get events -n mcps --sort-by=.lastTimestamp 2>&1 | grep -i "error\|warn\|fail\|denied\|reject" | tail -20
echo ""

echo "=== 4. PATCH KYVERNO TO EXCLUDE mcps NAMESPACE ==="
for POLICY in disallow-privileged-containers disallow-root-user require-env-label require-pod-labels require-resource-limits restrict-image-registries; do
  echo "  Patching $POLICY..."
  k3s kubectl get cpol $POLICY -o json 2>/dev/null | python3 -c "
import json,sys
p = json.load(sys.stdin)
excludes = p['spec'].setdefault('exclude', [])
ns_exists = any(
    any(f.get('key') == 'request.namespace' and 'mcps' in str(f.get('value','')) for f in e.get('any',[]))
    for e in excludes
)
if not ns_exists:
    excludes.append({
        'any': [{
            'resources': ['namespaces'],
            'subjects': [{'kind': 'ServiceAccount', 'name': '*', 'namespace': 'mcps'}]
        }]
    })
    # Also add namespace exclude
    for r in p['spec'].get('rules', []):
        if 'exclude' not in r:
            r['exclude'] = {}
        r.setdefault('exclude', {})
print(json.dumps(p))
" 2>/dev/null > /tmp/patched-policy.json
  
  if [ -s /tmp/patched-policy.json ]; then
    k3s kubectl apply -f /tmp/patched-policy.json 2>&1 || echo "  Failed to patch $POLICY"
  fi
done
echo ""

echo "=== 5. SIMPLE APPROACH: ADD mcps TO EXCLUDES ==="
for POLICY in disallow-privileged-containers disallow-root-user require-env-label require-pod-labels require-resource-limits restrict-image-registries; do
  echo -n "  $POLICY: "
  # Get current exclude namespaces
  CURRENT=$(k3s kubectl get cpol $POLICY -o jsonpath='{.spec.exclude}' 2>/dev/null)
  echo "$CURRENT" | head -c 100
  echo ""
done
echo ""

echo "DONE"
