#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ARGOCD ADMIN SECRET ==="
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath='{.data.password}' 2>/dev/null | base64 -d 2>&1
echo ""

echo "=== 2. CHECK IF SECRET EXISTS ==="
kubectl get secret -n argocd 2>&1 | grep -i admin
echo ""

echo "=== 3. ARGOCD RBAC ==="
kubectl get cm argocd-rbac-cm -n argocd -o yaml 2>&1 | head -20
echo ""

echo "DONE"
