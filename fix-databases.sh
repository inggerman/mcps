#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. CHECK EVENTS IN databases ==="
kubectl get events -n databases --sort-by=.lastTimestamp 2>&1 | tail -20
echo ""

echo "=== 2. ADD databases TO KYVERNO EXCLUDES ==="
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
            if 'databases' not in res['namespaces']:
                res['namespaces'].append('databases')
print(json.dumps(p))
" 2>/dev/null > /tmp/patched.json
  if [ -s /tmp/patched.json ]; then
    kubectl apply -f /tmp/patched.json 2>&1 | head -1
  else
    echo "FAILED"
  fi
done
echo ""

echo "=== 3. RESTART DEPLOYMENTS ==="
kubectl rollout restart deploy -n databases mongodb mongo-express pgadmin4 2>&1
echo ""

echo "=== 4. DELETE STS PODS TO FORCE RECREATE ==="
kubectl delete pod -n databases postgresql-0 --force --grace-period=0 2>&1 | grep -v Warning || true
kubectl delete pod -n databases kafka-controller-0 --force --grace-period=0 2>&1 | grep -v Warning || true
kubectl delete pod -n databases redis-master-0 --force --grace-period=0 2>&1 | grep -v Warning || true
echo ""

echo "=== 5. WAIT 30s ==="
sleep 30
echo ""

echo "=== 6. STATUS ==="
kubectl get pods -n databases 2>&1
echo ""

echo "=== 7. IF STILL NOT CREATING, SCALE DOWN AND UP ==="
for dep in mongodb mongo-express pgadmin4; do
  kubectl scale deploy -n databases $dep --replicas=0 2>&1
done
kubectl scale sts -n databases postgresql --replicas=0 2>&1
kubectl scale sts -n databases kafka-controller --replicas=0 2>&1
kubectl scale sts -n databases redis-master --replicas=0 2>&1
sleep 5
echo "  Scaling back up..."
for dep in mongodb mongo-express pgadmin4; do
  kubectl scale deploy -n databases $dep --replicas=1 2>&1
done
kubectl scale sts -n databases postgresql --replicas=1 2>&1
kubectl scale sts -n databases kafka-controller --replicas=1 2>&1
kubectl scale sts -n databases redis-master --replicas=1 2>&1
echo ""

echo "=== 8. WAIT 30s ==="
sleep 30
echo ""

echo "=== 9. FINAL STATUS ==="
kubectl get pods -n databases 2>&1
echo ""
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""
TOTAL=$(kubectl get pods -A --no-headers 2>/dev/null | wc -l)
RUNNING=$(kubectl get pods -A --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
echo "  Total: $TOTAL  Running: $RUNNING"
echo ""

echo "DONE"
