#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== RabbitMQ secrets ==="
kubectl get secret -n rabbitmq 2>&1
echo ""

echo "=== RabbitMQ secret details ==="
kubectl get secret rabbitmq -n rabbitmq -o yaml 2>&1 | head -30
echo ""

echo "=== Try default credentials test ==="
kubectl exec -n rabbitmq rabbitmq-0 -- rabbitmqctl list_users 2>&1
echo ""

echo "=== Redis test ==="
kubectl exec -n databases redis-master-0 -- redis-cli ping 2>&1
echo ""

echo "=== Redis auth check ==="
kubectl get secret -n databases 2>&1 | grep redis
echo ""

kubectl get secret -n databases -o yaml 2>&1 | grep -A5 redis
echo ""

echo "DONE"
