#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== NODES ==="
kubectl get nodes 2>&1
echo ""

echo "=== NOT RUNNING PODS ==="
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "=== TOTAL ==="
TOTAL=$(kubectl get pods -A --no-headers 2>/dev/null | wc -l)
RUNNING=$(kubectl get pods -A --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
echo "  Total: $TOTAL  Running: $RUNNING"
echo ""

echo "=== KYVERNO POLICIES EXCLUDES ==="
for POLICY in require-pod-labels disallow-root-user require-resource-limits disallow-privileged-containers restrict-image-registries; do
  echo -n "  $POLICY: "
  kubectl get cpol $POLICY -o json 2>/dev/null | python3 -c "
import json,sys
p=json.load(sys.stdin)
for r in p['spec']['rules']:
    for c in r.get('exclude',{}).get('any',[]):
        ns=c.get('resources',{}).get('namespaces',[])
        print(','.join(ns))
        break
    break
" 2>/dev/null || echo "ERROR"
done
echo ""

echo "=== HARBOR ==="
kubectl get pods -n harbor 2>&1
echo ""

echo "=== GITEA ==="
kubectl get pods -n gitea 2>&1
echo ""

echo "=== DATABASES ==="
kubectl get pods -n databases 2>&1
echo ""

echo "=== K3S SERVICE ==="
systemctl is-active k3s 2>&1
echo ""

echo "=== CRONJOBS ==="
kubectl get cj -A 2>&1
echo ""

echo "DONE"
