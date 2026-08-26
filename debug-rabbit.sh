#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== RabbitMQ password decoded ==="
kubectl get secret rabbitmq -n rabbitmq -o jsonpath='{.data.rabbitmq-password}' 2>&1 | base64 -d 2>&1
echo ""
echo ""

echo "=== RabbitMQ-credentials secret ==="
kubectl get secret rabbitmq-credentials -n rabbitmq -o yaml 2>&1 | grep -E "username|password"
echo ""

echo "=== Decode rabbitmq-credentials ==="
kubectl get secret rabbitmq-credentials -n rabbitmq -o jsonpath='{.data}' 2>&1
echo ""

echo "=== Try rabbitmqctl list_users ==="
kubectl exec -n rabbitmq rabbitmq-0 -- rabbitmqctl list_users 2>&1
echo ""

echo "=== Test AMQP connection from inside cluster ==="
kubectl exec -n rabbitmq rabbitmq-0 -- rabbitmqctl status 2>&1 | head -10
echo ""

echo "=== Check actual env in worker pod ==="
kubectl exec -n agents-platform agents-platform-worker-5cc44b648d-fpnxl -- env 2>&1 | grep -E "RABBIT|REDIS|IMAP" 2>&1
echo ""

echo "DONE"
