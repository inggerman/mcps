#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. PATCH WORKER DEPLOYMENT ==="
kubectl set image deployment/agents-platform-worker -n agents-platform \
  worker=harbor-registry.harbor.svc.cluster.local:5000/ghl/agents-platform-worker:latest 2>&1
echo ""

kubectl set env deployment/agents-platform-worker -n agents-platform \
  AGENTS_RABBITMQ_URL=amqp://user:RabbitLocal123!@rabbitmq.rabbitmq.svc.cluster.local:5672 \
  AGENTS_REDIS_URL=redis://:RedisLocal123!@redis-master.databases.svc.cluster.local:6379/2 \
  AGENTS_NOTIFY_SLACK_ENABLED=false \
  AGENTS_NOTIFY_EMAIL_ENABLED=false 2>&1
echo ""

echo "=== 2. PATCH API DEPLOYMENT ==="
kubectl set image deployment/agents-platform-api -n agents-platform \
  api=harbor-registry.harbor.svc.cluster.local:5000/ghl/agents-platform-api:latest 2>&1
echo ""

kubectl set env deployment/agents-platform-api -n agents-platform \
  AGENTS_RABBITMQ_URL=amqp://user:RabbitLocal123!@rabbitmq.rabbitmq.svc.cluster.local:5672 \
  AGENTS_REDIS_URL=redis://:RedisLocal123!@redis-master.databases.svc.cluster.local:6379/2 \
  AGENTS_NOTIFY_SLACK_ENABLED=false \
  AGENTS_NOTIFY_EMAIL_ENABLED=false 2>&1
echo ""

echo "=== 3. PATCH DAEMON DEPLOYMENT ==="
kubectl set image deployment/agents-platform-daemon -n agents-platform \
  daemon=harbor-registry.harbor.svc.cluster.local:5000/ghl/agents-platform-worker:latest 2>&1
echo ""

kubectl set env deployment/agents-platform-daemon -n agents-platform \
  AGENTS_RABBITMQ_URL=amqp://user:RabbitLocal123!@rabbitmq.rabbitmq.svc.cluster.local:5672 \
  AGENTS_REDIS_URL=redis://:RedisLocal123!@redis-master.databases.svc.cluster.local:6379/2 \
  AGENTS_IMAP_HOST= 2>&1
echo ""

echo "=== 4. PATCH MCP DEPLOYMENTS ==="
kubectl set image deployment/mcp-web-search -n agents-platform \
  mcp-web-search=harbor-registry.harbor.svc.cluster.local:5000/ghl/mcp-web-search:latest 2>&1

kubectl set image deployment/mcp-source-validator -n agents-platform \
  mcp-source-validator=harbor-registry.harbor.svc.cluster.local:5000/ghl/mcp-source-validator:latest 2>&1
echo ""

echo "=== 5. ROLLOUT RESTART ==="
kubectl rollout restart deployment/agents-platform-api -n agents-platform 2>&1
kubectl rollout restart deployment/agents-platform-worker -n agents-platform 2>&1
kubectl rollout restart deployment/agents-platform-daemon -n agents-platform 2>&1
kubectl rollout restart deployment/mcp-web-search -n agents-platform 2>&1
kubectl rollout restart deployment/mcp-source-validator -n agents-platform 2>&1
echo ""

echo "=== 6. WAIT 60s ==="
sleep 60
echo ""

echo "=== 7. CHECK PODS ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== 8. CHECK LOGS FOR NON-RUNNING PODS ==="
for pod in $(kubectl get pods -n agents-platform -o jsonpath='{.items[?(@.status.phase!="Running")].metadata.name}' 2>/dev/null); do
  echo "--- $pod ---"
  kubectl logs -n agents-platform $pod --tail=15 2>&1
  echo ""
done

echo "=== 9. ALL POD LOGS (tail=5) ==="
for pod in $(kubectl get pods -n agents-platform -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
  echo "--- $pod ---"
  kubectl logs -n agents-platform $pod --tail=5 2>&1
  echo ""
done

echo "DONE"
