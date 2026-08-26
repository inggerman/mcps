#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ARGOCD PODS ==="
kubectl get pods -n argocd 2>&1
echo ""

echo "=== 2. ARGOCD SERVER SVC ==="
kubectl get svc -n argocd argocd-server 2>&1
echo ""

echo "=== 3. ARGOCD INGRESS ==="
kubectl get ingress -n argocd 2>&1
echo ""

echo "=== 4. ARGOCD SERVER ARGS ==="
kubectl get deploy -n argocd argocd-server -o jsonpath='{.spec.template.spec.containers[0].args}' 2>&1
echo ""
echo ""

echo "=== 5. ARGOCD SERVER ENV ==="
kubectl get deploy -n argocd argocd-server -o jsonpath='{.spec.template.spec.containers[0].env}' 2>&1
echo ""
echo ""

echo "=== 6. ARGOCD CONFIGMAP ==="
kubectl get cm argocd-cmd-params-cm -n argocd -o yaml 2>&1
echo ""

echo "=== 7. TEST INTERNAL ==="
kubectl exec -n argocd deploy/argocd-server -- curl -sI http://localhost:8080/ 2>&1 | head -5
echo ""

echo "=== 8. ARGOCD APPLICATIONS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 9. ARGOCD APPPROJECTS ==="
kubectl get appprojects -A 2>&1
echo ""

echo "DONE"
