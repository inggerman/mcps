#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. DATABASES NAMESPACE - ALL RESOURCES ==="
kubectl get all -n databases 2>&1
echo ""

echo "=== 2. CHECK IF ARGOCD MANAGES DATABASES ==="
kubectl get applications -n argocd -o wide 2>&1 | grep -i data || echo "  No ArgoCD app for databases"
echo ""

echo "=== 3. CHECK ARGOCD APPS ==="
kubectl get applications -n argocd 2>&1
echo ""

echo "=== 4. CHECK HELM RELEASES IN DATABASES ==="
helm list -n databases 2>&1
echo ""

echo "=== 5. CHECK WHAT EXISTS IN databases NAMESPACE ==="
kubectl get deployments,sts,svc,configmaps,secrets,pvc -n databases 2>&1
echo ""

echo "=== 6. CHECK KAFKA NAMESPACE ==="
kubectl get all -n kafka 2>&1 || echo "  No kafka namespace"
echo ""

echo "=== 7. CHECK ALL NAMESPACES ==="
kubectl get ns 2>&1
echo ""

echo "DONE"
