#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. ADD gitea TO KYVERNO EXCLUDES ==="
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
            if 'gitea' not in res['namespaces']:
                res['namespaces'].append('gitea')
print(json.dumps(p))
" 2>/dev/null > /tmp/patched.json
  if [ -s /tmp/patched.json ]; then
    kubectl apply -f /tmp/patched.json 2>&1 | head -1
  else
    echo "FAILED"
  fi
done
echo ""

echo "=== 2. RECREATE HARBOR STS VIA HELM ==="
helm list -n harbor 2>&1
echo ""
helm upgrade harbor harbor/harbor -n harbor --reuse-values --wait --timeout 120s 2>&1 | tail -10
echo ""

echo "=== 3. DELETE FAILED CRONJOB PODS ==="
kubectl delete pod -n databases --all --force --grace-period=0 --field-selector=status.phase!=Running 2>&1 || true
kubectl delete pod -n rabbitmq --all --force --grace-period=0 --field-selector=status.phase!=Running 2>&1 || true
# Alternative: delete by name
kubectl delete pod -n databases mongo-dump-29746605-hrwz9 --force --grace-period=0 2>&1 || true
kubectl delete pod -n databases mongo-dump-29748045-pdg2s --force --grace-period=0 2>&1 || true
kubectl delete pod -n databases pg-dump-29746590-ww5xt --force --grace-period=0 2>&1 || true
kubectl delete pod -n databases pg-dump-29748030-4rlpr --force --grace-period=0 2>&1 || true
kubectl delete pod -n rabbitmq rabbitmq-export-29746620-zhlhp --force --grace-period=0 2>&1 || true
kubectl delete pod -n rabbitmq rabbitmq-export-29748060-rpxv4 --force --grace-period=0 2>&1 || true
echo ""

echo "=== 4. WAIT 60s ==="
sleep 60
echo ""

echo "=== 5. FINAL STATUS ==="
echo "--- gitea ---"
kubectl get pods -n gitea 2>&1
echo ""
echo "--- harbor ---"
kubectl get pods -n harbor 2>&1
echo ""
echo "--- not running ---"
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "DONE"
