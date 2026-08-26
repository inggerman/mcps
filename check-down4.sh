#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. GITEA DEPLOYMENT ==="
kubectl get deploy -n gitea 2>&1
kubectl describe deploy -n gitea gitea 2>&1 | tail -20
echo ""

echo "=== 2. HARBOR STS ==="
kubectl get sts -n harbor 2>&1
echo ""

echo "=== 3. HARBOR-DATABASE POD ==="
kubectl get pod -n harbor -l app.kubernetes.io/component=database 2>&1
echo ""

echo "=== 4. HARBOR-REDIS POD ==="
kubectl get pod -n harbor -l app.kubernetes.io/component=redis 2>&1
echo ""

echo "=== 5. HARBOR-JOBSERVICE ==="
kubectl get pod -n harbor -l app.kubernetes.io/component=jobservice 2>&1
echo ""

echo "=== 6. ALL HARBOR PODS ==="
kubectl get pods -n harbor 2>&1
echo ""

echo "=== 7. SUSPEND CRONJOBS ==="
kubectl get cronjob -A 2>&1
echo ""

echo "=== 8. GITEA PODS ==="
kubectl get pods -n gitea 2>&1
echo ""

echo "DONE"
