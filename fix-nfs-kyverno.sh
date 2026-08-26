#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. NFS DEPLOYMENT ==="
kubectl get deploy nfs-subdir-provisioner-nfs-subdir-external-provisioner -n nfs-storage -o yaml 2>&1 | head -30
echo ""

echo "=== 2. NFS EVENTS ==="
kubectl get events -n nfs-storage --sort-by=.lastTimestamp 2>&1 | tail -10
echo ""

echo "=== 3. CHECK IF nfs-storage IN KYVERNO EXCLUDES ==="
kubectl get cpol require-pod-labels -o jsonpath='{.spec.rules[0].exclude}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for cond in data.get('any', []):
    ns = cond.get('resources', {}).get('namespaces', [])
    print(f'  Excluded namespaces: {ns}')
" 2>&1
echo ""

echo "=== 4. ADD nfs-storage TO KYVERNO EXCLUDES ==="
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
            if 'nfs-storage' not in res['namespaces']:
                res['namespaces'].append('nfs-storage')
print(json.dumps(p))
" 2>/dev/null > /tmp/patched.json
  if [ -s /tmp/patched.json ]; then
    kubectl apply -f /tmp/patched.json 2>&1 | head -1
  else
    echo "FAILED"
  fi
done
echo ""

echo "=== 5. RESTART NFS ==="
kubectl rollout restart deploy nfs-subdir-provisioner-nfs-subdir-external-provisioner -n nfs-storage 2>&1
echo ""

echo "=== 6. WAIT 15s ==="
sleep 15
echo ""

echo "=== 7. NFS POD ==="
kubectl get pods -n nfs-storage 2>&1
echo ""

echo "DONE"
