#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== Worker env ==="
kubectl get deployment agents-platform-worker -n agents-platform -o jsonpath='{.spec.template.spec.containers[0].env[4]}' 2>&1
echo ""
kubectl get deployment agents-platform-worker -n agents-platform -o jsonpath='{.spec.template.spec.containers[0].env[5]}' 2>&1
echo ""

echo "=== Worker image ==="
kubectl get deployment agents-platform-worker -n agents-platform -o jsonpath='{.spec.template.spec.containers[0].image}' 2>&1
echo ""

echo "=== Force apply again ==="
cat <<YAMLEOF | kubectl apply -f - 2>&1
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agents-platform-worker
  namespace: agents-platform
  labels:
    app.kubernetes.io/name: agents-platform-worker
    app.kubernetes.io/part-of: agents-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: agents-platform-worker
  template:
    metadata:
      labels:
        app.kubernetes.io/name: agents-platform-worker
        app.kubernetes.io/part-of: agents-platform
    spec:
      containers:
        - name: worker
          image: harbor.mrrobot.fs/ghl/agents-platform-worker:latest
          env:
            - name: AGENTS_ORCHESTRATOR_PROVIDER
              value: "lmstudio"
            - name: AGENTS_ORCHESTRATOR_MODEL
              value: "mistralai/devstral-small-2-2512"
            - name: AGENTS_LMSTUDIO_URL
              value: "http://100.73.65.63:1234/v1"
            - name: AGENTS_QDRANT_URL
              value: "http://qdrant.agents-platform.svc.cluster.local:6333"
            - name: AGENTS_RABBITMQ_URL
              value: "amqp://user:RabbitLocal123!@rabbitmq.rabbitmq.svc.cluster.local:5672"
            - name: AGENTS_REDIS_URL
              value: "redis://:RedisLocal123!@redis-master.databases.svc.cluster.local:6379/2"
            - name: AGENTS_NOTIFY_SLACK_ENABLED
              value: "false"
            - name: AGENTS_NOTIFY_EMAIL_ENABLED
              value: "false"
            - name: AGENTS_WEB_SEARCH_ENABLED
              value: "true"
            - name: AGENTS_GROUNDING_ENABLED
              value: "true"
            - name: AGENTS_GROUNDING_THRESHOLD
              value: "0.3"
          resources:
            requests:
              memory: 512Mi
              cpu: 500m
            limits:
              memory: 2Gi
              cpu: 2000m
YAMLEOF
echo ""

echo "=== Delete worker pods ==="
kubectl delete pods -n agents-platform -l app.kubernetes.io/name=agents-platform-worker --force 2>&1
echo ""

echo "=== Wait 45s ==="
sleep 45
echo ""

echo "=== Check pods ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== Worker logs ==="
for pod in $(kubectl get pods -n agents-platform -l app.kubernetes.io/name=agents-platform-worker -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
  echo "--- $pod ---"
  kubectl logs -n agents-platform $pod --tail=10 2>&1
  echo ""
done

echo "DONE"
