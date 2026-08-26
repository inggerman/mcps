#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ARGO WORKFLOWS PODS ==="
kubectl get pods -n argo-workflows 2>&1
echo ""

echo "=== 2. ARGO WORKFLOWS SVC ==="
kubectl get svc -n argo-workflows 2>&1
echo ""

echo "=== 3. ARGO WORKFLOWS INGRESS ==="
kubectl get ingress -n argo-workflows 2>&1
echo ""

echo "=== 4. ARGO WORKFLOWS CONFIGMAP ==="
kubectl get cm -n argo-workflows 2>&1
echo ""

echo "=== 5. WORKFLOW CONTROLLER CONFIG ==="
kubectl get cm workflow-controller-configmap -n argo-workflows -o yaml 2>&1
echo ""

echo "=== 6. ARGO WORKFLOWS SERVER LOGS ==="
kubectl logs -n argo-workflows -l app=argo-server --tail=30 2>&1
echo ""

echo "=== 7. CHECK SECRET FOR SSO ==="
kubectl get secret -n argo-workflows 2>&1
echo ""

echo "=== 8. DESCRIBE INGRESS ==="
kubectl describe ingress -n argo-workflows 2>&1
echo ""

echo "DONE"
