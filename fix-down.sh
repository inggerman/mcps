#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. DELETE UNKNOWN PODS ==="
kubectl delete pod -n gitea gitea-574f6757f5-mm45n --force --grace-period=0 2>&1
kubectl delete pod -n harbor harbor-database-0 --force --grace-period=0 2>&1
kubectl delete pod -n harbor harbor-redis-0 --force --grace-period=0 2>&1
kubectl delete pod -n harbor harbor-trivy-0 --force --grace-period=0 2>&1
echo ""

echo "=== 2. DELETE FAILED CRONJOB PODS ==="
kubectl delete pod -n databases mongo-dump-29746605-89pzb --force --grace-period=0 2>&1
kubectl delete pod -n databases mongo-dump-29748045-q8wlp --force --grace-period=0 2>&1
kubectl delete pod -n databases pg-dump-29746590-fr8j8 --force --grace-period=0 2>&1
kubectl delete pod -n databases pg-dump-29748030-wcbjk --force --grace-period=0 2>&1
kubectl delete pod -n rabbitmq rabbitmq-export-29746620-rx9cj --force --grace-period=0 2>&1
kubectl delete pod -n rabbitmq rabbitmq-export-29748060-bfxpm --force --grace-period=0 2>&1
echo ""

echo "=== 3. HARBOR JOBSERVICE LOGS ==="
kubectl logs -n harbor harbor-jobservice-9754784b6-46blh --tail=15 2>&1
echo ""

echo "=== 4. WAIT 30s ==="
sleep 30
echo ""

echo "=== 5. STATUS AFTER FIX ==="
echo "--- gitea ---"
kubectl get pods -n gitea 2>&1
echo ""
echo "--- harbor ---"
kubectl get pods -n harbor 2>&1
echo ""
echo "--- not running ---"
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "DONE"
