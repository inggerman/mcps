#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. Apply WORKER deployment with harbor.mrrobot.fs ==="
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

echo "=== 2. Apply DAEMON deployment with harbor.mrrobot.fs ==="
cat <<YAMLEOF2 | kubectl apply -f - 2>&1
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agents-platform-daemon
  namespace: agents-platform
  labels:
    app.kubernetes.io/name: agents-platform-daemon
    app.kubernetes.io/part-of: agents-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: agents-platform-daemon
  template:
    metadata:
      labels:
        app.kubernetes.io/name: agents-platform-daemon
        app.kubernetes.io/part-of: agents-platform
    spec:
      containers:
        - name: daemon
          image: harbor.mrrobot.fs/ghl/agents-platform-worker:latest
          command: ["python", "-m", "agents_platform.daemon"]
          env:
            - name: AGENTS_REDIS_URL
              value: "redis://:RedisLocal123!@redis-master.databases.svc.cluster.local:6379/2"
            - name: AGENTS_RABBITMQ_URL
              value: "amqp://user:RabbitLocal123!@rabbitmq.rabbitmq.svc.cluster.local:5672"
            - name: AGENTS_IMAP_HOST
              value: ""
            - name: AGENTS_IMAP_USER
              value: ""
            - name: AGENTS_IMAP_PASS
              value: "none"
          resources:
            requests:
              memory: 128Mi
              cpu: 100m
            limits:
              memory: 256Mi
              cpu: 250m
YAMLEOF2
echo ""

echo "=== 3. Apply API deployment with harbor.mrrobot.fs ==="
cat <<YAMLEOF3 | kubectl apply -f - 2>&1
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agents-platform-api
  namespace: agents-platform
  labels:
    app.kubernetes.io/name: agents-platform-api
    app.kubernetes.io/part-of: agents-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: agents-platform-api
  template:
    metadata:
      labels:
        app.kubernetes.io/name: agents-platform-api
        app.kubernetes.io/part-of: agents-platform
    spec:
      serviceAccountName: agents-platform-api
      containers:
        - name: api
          image: harbor.mrrobot.fs/ghl/agents-platform-api:latest
          ports:
            - containerPort: 8000
              name: http
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
            - name: AGENTS_SLACK_BOT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: agents-platform-secrets
                  key: slack-bot-token
            - name: AGENTS_SLACK_SIGNING_SECRET
              valueFrom:
                secretKeyRef:
                  name: agents-platform-secrets
                  key: slack-signing-secret
            - name: AGENTS_SLACK_CHANNEL_ID
              value: "#agents-platform"
            - name: AGENTS_NOTIFY_SLACK_ENABLED
              value: "false"
            - name: AGENTS_SMTP_HOST
              value: ""
            - name: AGENTS_SMTP_USER
              value: ""
            - name: AGENTS_SMTP_PASS
              valueFrom:
                secretKeyRef:
                  name: agents-platform-secrets
                  key: smtp-password
            - name: AGENTS_SMTP_FROM
              value: ""
            - name: AGENTS_SMTP_TO
              value: ""
            - name: AGENTS_NOTIFY_EMAIL_ENABLED
              value: "false"
            - name: AGENTS_IMAP_HOST
              value: ""
            - name: AGENTS_IMAP_USER
              value: ""
            - name: AGENTS_IMAP_PASS
              valueFrom:
                secretKeyRef:
                  name: agents-platform-secrets
                  key: imap-password
            - name: AGENTS_WEB_SEARCH_ENABLED
              value: "true"
            - name: AGENTS_GROUNDING_ENABLED
              value: "true"
            - name: AGENTS_GROUNDING_THRESHOLD
              value: "0.3"
          resources:
            requests:
              memory: 256Mi
              cpu: 250m
            limits:
              memory: 512Mi
              cpu: 500m
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 15
            periodSeconds: 20
YAMLEOF3
echo ""

echo "=== 4. Apply MCP deployments with harbor.mrrobot.fs ==="
cat <<YAMLEOF4 | kubectl apply -f - 2>&1
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-web-search
  namespace: agents-platform
  labels:
    app.kubernetes.io/name: mcp-web-search
    app.kubernetes.io/part-of: agents-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: mcp-web-search
  template:
    metadata:
      labels:
        app.kubernetes.io/name: mcp-web-search
        app.kubernetes.io/part-of: agents-platform
    spec:
      containers:
        - name: mcp-web-search
          image: harbor.mrrobot.fs/ghl/mcp-web-search:latest
          ports:
            - containerPort: 8037
              name: mcp
          env:
            - name: MCP_TRANSPORT
              value: "streamable-http"
            - name: MCP_PORT
              value: "8037"
            - name: MCP_WEB_SEARCH_PROVIDER
              value: "duckduckgo"
          resources:
            requests:
              memory: 128Mi
              cpu: 100m
            limits:
              memory: 256Mi
              cpu: 250m
          readinessProbe:
            httpGet:
              path: /health
              port: mcp
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: mcp
            initialDelaySeconds: 15
            periodSeconds: 20
YAMLEOF4
echo ""

cat <<YAMLEOF5 | kubectl apply -f - 2>&1
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-source-validator
  namespace: agents-platform
  labels:
    app.kubernetes.io/name: mcp-source-validator
    app.kubernetes.io/part-of: agents-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: mcp-source-validator
  template:
    metadata:
      labels:
        app.kubernetes.io/name: mcp-source-validator
        app.kubernetes.io/part-of: agents-platform
    spec:
      containers:
        - name: mcp-source-validator
          image: harbor.mrrobot.fs/ghl/mcp-source-validator:latest
          ports:
            - containerPort: 8038
              name: mcp
          env:
            - name: MCP_TRANSPORT
              value: "streamable-http"
            - name: MCP_PORT
              value: "8038"
          resources:
            requests:
              memory: 128Mi
              cpu: 100m
            limits:
              memory: 256Mi
              cpu: 250m
          readinessProbe:
            httpGet:
              path: /health
              port: mcp
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: mcp
            initialDelaySeconds: 15
            periodSeconds: 20
YAMLEOF5
echo ""

echo "=== 5. Delete all old pods to force fresh start ==="
kubectl delete pods -n agents-platform --all --force 2>&1
echo ""

echo "=== 6. Wait 60s ==="
sleep 60
echo ""

echo "=== 7. Check pods ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== 8. Check logs ==="
for pod in $(kubectl get pods -n agents-platform -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
  PHASE=$(kubectl get pod -n agents-platform $pod -o jsonpath='{.status.phase}' 2>/dev/null)
  echo "--- $pod ($PHASE) ---"
  kubectl logs -n agents-platform $pod --tail=5 2>&1
  echo ""
done

echo "DONE"
