#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== NODES ==="
kubectl get nodes 2>&1
echo ""

echo "=== NOT RUNNING PODS ==="
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
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

echo "=== RABBITMQ ==="
kubectl get pods -n rabbitmq 2>&1
echo ""

echo "=== ARGOCD ==="
kubectl get pods -n argocd 2>&1
echo ""

echo "=== N8N ==="
kubectl get pods -n n8n 2>&1
echo ""

echo "=== TOTAL ==="
TOTAL=$(kubectl get pods -A --no-headers 2>/dev/null | wc -l)
RUNNING=$(kubectl get pods -A --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
echo "  Total: $TOTAL  Running: $RUNNING"
echo ""

echo "DONE"
