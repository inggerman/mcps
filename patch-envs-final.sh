#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. PATCH WORKER DEPLOYMENT (full env rewrite) ==="
kubectl patch deployment agents-platform-worker -n agents-platform --type=json -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/image","value":"harbor-registry.harbor.svc.cluster.local:5000/ghl/agents-platform-worker:latest"},
  {"op":"replace","path":"/spec/template/spec/containers/0/env","value":[
    {"name":"AGENTS_ORCHESTRATOR_PROVIDER","value":"lmstudio"},
    {"name":"AGENTS_ORCHESTRATOR_MODEL","value":"mistralai/devstral-small-2-2512"},
    {"name":"AGENTS_LMSTUDIO_URL","value":"http://100.73.65.63:1234/v1"},
    {"name":"AGENTS_QDRANT_URL","value":"http://qdrant.agents-platform.svc.cluster.local:6333"},
    {"name":"AGENTS_RABBITMQ_URL","value":"amqp://user:RabbitLocal123!@rabbitmq.rabbitmq.svc.cluster.local:5672"},
    {"name":"AGENTS_REDIS_URL","value":"redis://:RedisLocal123!@redis-master.databases.svc.cluster.local:6379/2"},
    {"name":"AGENTS_NOTIFY_SLACK_ENABLED","value":"false"},
    {"name":"AGENTS_NOTIFY_EMAIL_ENABLED","value":"false"},
    {"name":"AGENTS_WEB_SEARCH_ENABLED","value":"true"},
    {"name":"AGENTS_GROUNDING_ENABLED","value":"true"},
    {"name":"AGENTS_GROUNDING_THRESHOLD","value":"0.3"}
  ]}
]' 2>&1
echo ""

echo "=== 2. PATCH DAEMON DEPLOYMENT (full env rewrite) ==="
kubectl patch deployment agents-platform-daemon -n agents-platform --type=json -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/image","value":"harbor-registry.harbor.svc.cluster.local:5000/ghl/agents-platform-worker:latest"},
  {"op":"replace","path":"/spec/template/spec/containers/0/env","value":[
    {"name":"AGENTS_REDIS_URL","value":"redis://:RedisLocal123!@redis-master.databases.svc.cluster.local:6379/2"},
    {"name":"AGENTS_RABBITMQ_URL","value":"amqp://user:RabbitLocal123!@rabbitmq.rabbitmq.svc.cluster.local:5672"},
    {"name":"AGENTS_IMAP_HOST","value":""},
    {"name":"AGENTS_IMAP_USER","value":""},
    {"name":"AGENTS_IMAP_PASS","value":"none"}
  ]}
]' 2>&1
echo ""

echo "=== 3. PATCH API DEPLOYMENT (full env rewrite) ==="
kubectl patch deployment agents-platform-api -n agents-platform --type=json -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/image","value":"harbor-registry.harbor.svc.cluster.local:5000/ghl/agents-platform-api:latest"},
  {"op":"replace","path":"/spec/template/spec/containers/0/env","value":[
    {"name":"AGENTS_ORCHESTRATOR_PROVIDER","value":"lmstudio"},
    {"name":"AGENTS_ORCHESTRATOR_MODEL","value":"mistralai/devstral-small-2-2512"},
    {"name":"AGENTS_LMSTUDIO_URL","value":"http://100.73.65.63:1234/v1"},
    {"name":"AGENTS_QDRANT_URL","value":"http://qdrant.agents-platform.svc.cluster.local:6333"},
    {"name":"AGENTS_RABBITMQ_URL","value":"amqp://user:RabbitLocal123!@rabbitmq.rabbitmq.svc.cluster.local:5672"},
    {"name":"AGENTS_REDIS_URL","value":"redis://:RedisLocal123!@redis-master.databases.svc.cluster.local:6379/2"},
    {"name":"AGENTS_SLACK_BOT_TOKEN","valueFrom":{"secretKeyRef":{"name":"agents-platform-secrets","key":"slack-bot-token"}}},
    {"name":"AGENTS_SLACK_SIGNING_SECRET","valueFrom":{"secretKeyRef":{"name":"agents-platform-secrets","key":"slack-signing-secret"}}},
    {"name":"AGENTS_SLACK_CHANNEL_ID","value":"#agents-platform"},
    {"name":"AGENTS_NOTIFY_SLACK_ENABLED","value":"false"},
    {"name":"AGENTS_SMTP_HOST","value":""},
    {"name":"AGENTS_SMTP_USER","value":""},
    {"name":"AGENTS_SMTP_PASS","valueFrom":{"secretKeyRef":{"name":"agents-platform-secrets","key":"smtp-password"}}},
    {"name":"AGENTS_SMTP_FROM","value":""},
    {"name":"AGENTS_SMTP_TO","value":""},
    {"name":"AGENTS_NOTIFY_EMAIL_ENABLED","value":"false"},
    {"name":"AGENTS_IMAP_HOST","value":""},
    {"name":"AGENTS_IMAP_USER","value":""},
    {"name":"AGENTS_IMAP_PASS","valueFrom":{"secretKeyRef":{"name":"agents-platform-secrets","key":"imap-password"}}},
    {"name":"AGENTS_WEB_SEARCH_ENABLED","value":"true"},
    {"name":"AGENTS_GROUNDING_ENABLED","value":"true"},
    {"name":"AGENTS_GROUNDING_THRESHOLD","value":"0.3"}
  ]}
]' 2>&1
echo ""

echo "=== 4. WAIT 60s ==="
sleep 60
echo ""

echo "=== 5. CHECK PODS ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== 6. CHECK LOGS ==="
for pod in $(kubectl get pods -n agents-platform -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
  PHASE=$(kubectl get pod -n agents-platform $pod -o jsonpath='{.status.phase}' 2>/dev/null)
  echo "--- $pod ($PHASE) ---"
  kubectl logs -n agents-platform $pod --tail=8 2>&1
  echo ""
done

echo "DONE"
