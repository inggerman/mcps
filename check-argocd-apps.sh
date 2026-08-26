#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ARGOCD APPLICATIONS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 2. ARGOCD APPSETS ==="
kubectl get applicationsets -A 2>&1
echo ""

echo "=== 3. MCP DEPLOYMENTS (deployed directly) ==="
kubectl get deploy -n mcps 2>&1
echo ""

echo "=== 4. CHECK GITOPS APPS DIR ==="
echo "Apps in GitOps repo:"
kubectl get applications -A -o jsonpath='{range .items[*]}{.metadata.name}{" -> "}{.spec.source.path}{"\n"}{end}' 2>&1
echo ""

echo "DONE"
