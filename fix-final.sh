#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. SUSPEND CRONJOBS ==="
kubectl patch cronjob mongo-dump -n databases -p '{"spec":{"suspend":true}}' 2>&1
kubectl patch cronjob pg-dump -n databases -p '{"spec":{"suspend":true}}' 2>&1
kubectl patch cronjob rabbitmq-export -n rabbitmq -p '{"spec":{"suspend":true}}' 2>&1
echo ""

echo "=== 2. DELETE ALL FAILED CRONJOB PODS ==="
kubectl delete pod -n databases mongo-dump-29746605-djg4v --force --grace-period=0 2>&1
kubectl delete pod -n databases mongo-dump-29748045-66wz8 --force --grace-period=0 2>&1
kubectl delete pod -n databases pg-dump-29746590-xj9fc --force --grace-period=0 2>&1
kubectl delete pod -n databases pg-dump-29748030-mk8g8 --force --grace-period=0 2>&1
kubectl delete pod -n rabbitmq rabbitmq-export-29746620-hjsnm --force --grace-period=0 2>&1
kubectl delete pod -n rabbitmq rabbitmq-export-29748060-vz2zn --force --grace-period=0 2>&1
echo ""

echo "=== 3. WAIT 20s ==="
sleep 20
echo ""

echo "=== 4. FINAL STATUS ==="
echo "--- Not running pods ---"
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "--- Harbor ---"
kubectl get pods -n harbor 2>&1
echo ""

echo "--- Gitea ---"
kubectl get pods -n gitea 2>&1
echo ""

echo "--- MCPS ---"
kubectl get pods -n mcps 2>&1 | head -15
echo ""

echo "--- ArgoCD ---"
kubectl get pods -n argocd 2>&1
echo ""

echo "--- n8n ---"
kubectl get pods -n n8n 2>&1
echo ""

echo "=== 5. TOTAL PODS ==="
TOTAL=$(kubectl get pods -A --no-headers 2>/dev/null | wc -l)
RUNNING=$(kubectl get pods -A --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
echo "  Total: $TOTAL  Running: $RUNNING"
echo ""

echo "DONE"
