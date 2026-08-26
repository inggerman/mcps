#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== ALL SERVICES ==="
kubectl get svc --all-namespaces 2>&1 | grep -E "redis|rabbitmq|amqp|qdrant"
echo ""

echo "=== rabbitmq namespace ==="
kubectl get svc -n rabbitmq 2>&1
echo ""

echo "=== databases namespace ==="
kubectl get svc -n databases 2>&1
echo ""

echo "=== agents-platform namespace ==="
kubectl get svc -n agents-platform 2>&1
echo ""

echo "=== RabbitMQ pods ==="
kubectl get pods -n rabbitmq 2>&1
echo ""

echo "=== Redis pods (any namespace) ==="
kubectl get pods --all-namespaces 2>&1 | grep -i redis
echo ""

echo "=== Check redis in agents-platform ==="
kubectl get svc -n agents-platform 2>&1
echo ""

echo "DONE"
