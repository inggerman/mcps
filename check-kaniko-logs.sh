#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. INIT CONTAINER LOGS ==="
kubectl logs -n argocd build-agents-platform-qfnfm -c clone 2>&1
echo ""

echo "=== 2. POD EVENTS ==="
kubectl describe pod -n argocd build-agents-platform-qfnfm 2>&1 | grep -A20 "Events:" | head -25
echo ""

echo "=== 3. CHECK GITEA ACCESS FROM argocd NAMESPACE ==="
kubectl exec -n argocd deployment/argocd-repo-server -- curl -s -o /dev/null -w "%{http_code}" http://gitea-http-fixed.gitea.svc.cluster.local:3000 2>&1
echo ""

echo "DONE"
