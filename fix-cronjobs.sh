#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. DELETE CRONJOBS ==="
kubectl delete cronjob mongo-dump -n databases 2>&1
kubectl delete cronjob pg-dump -n databases 2>&1
kubectl delete cronjob rabbitmq-export -n rabbitmq 2>&1
echo ""

echo "=== 2. DELETE REMAINING PODS ==="
kubectl delete pods -n databases --all --force --grace-period=0 2>&1 | grep -v Warning || true
kubectl delete pods -n rabbitmq --field-selector=status.phase!=Running --all --force --grace-period=0 2>&1 | grep -v Warning || true
echo ""

echo "=== 3. WAIT 10s ==="
sleep 10
echo ""

echo "=== 4. FINAL CHECK ==="
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""
TOTAL=$(kubectl get pods -A --no-headers 2>/dev/null | wc -l)
RUNNING=$(kubectl get pods -A --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
echo "  Total: $TOTAL  Running: $RUNNING"
echo ""

echo "DONE"
