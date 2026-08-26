#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

GITEA_IP=$(kubectl get svc gitea-http-fixed -n gitea -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "Gitea IP: $GITEA_IP"

echo "=== 1. DELETE OLD JOB ==="
kubectl delete job build-agents-platform -n gitea-runner 2>&1 || true
echo ""

echo "=== 2. CREATE KANIKO JOB (proper syntax fix) ==="
cat <<JOBEF | kubectl apply -f - 2>&1
apiVersion: batch/v1
kind: Job
metadata:
  name: build-agents-platform
  namespace: gitea-runner
  labels:
    app.kubernetes.io/name: build-agents
    app.kubernetes.io/part-of: agents-platform
spec:
  ttlSecondsAfterFinished: 3600
  template:
    metadata:
      labels:
        app.kubernetes.io/name: build-agents
        app.kubernetes.io/part-of: agents-platform
    spec:
      securityContext:
        runAsNonRoot: false
        runAsUser: 0
      initContainers:
      - name: clone
        image: docker.io/alpine/git:latest
        securityContext:
          privileged: false
          runAsNonRoot: false
          runAsUser: 0
          allowPrivilegeEscalation: false
        command:
        - sh
        - -c
        - |
          set -e
          GIT_URL="http://ghl-admin:ChangeMe123!@${GITEA_IP}:3000/ghl/agents-platform.git"
          echo "Cloning..."
          git clone "\$GIT_URL" /workspace/source 2>&1
          cd /workspace/source
          
          # Fix syntax error: replace 2900} with 2900]} (missing closing bracket)
          sed -i 's/2900}/2900]}/g' notifications/slack_notifier.py
          echo "=== Fixed line ==="
          grep -n '2900' notifications/slack_notifier.py
          
          # Fix base images to use Harbor mirror
          sed -i 's|FROM docker.io/python:3.12-slim|FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim|g' Dockerfile.api
          sed -i 's|FROM docker.io/python:3.12-slim|FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim|g' Dockerfile.worker
          
          # Fix: add symlink + PYTHONPATH
          sed -i '/^COPY \. \.$/a RUN ln -s /app /app/agents_platform\n\nENV PYTHONPATH=/app' Dockerfile.api
          sed -i '/^COPY \. \.$/a RUN ln -s /app /app/agents_platform\n\nENV PYTHONPATH=/app' Dockerfile.worker
          
          # Create Dockerfiles for MCP services
          cat > Dockerfile.mcp-web-search <<'MCP1'
          FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim AS builder
          WORKDIR /app
          RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*
          COPY pyproject.toml ./
          RUN pip install --no-cache-dir --upgrade pip && \
              pip install --no-cache-dir build && \
              pip install --no-cache-dir . \
              || pip install --no-cache-dir \
                  pydantic>=2.0 pydantic-settings>=2.0 pyyaml>=6.0 \
                  langgraph>=0.2.0 langchain-core>=0.3.0 langchain-openai>=0.2.0 \
                  langchain-anthropic>=0.2.0 qdrant-client>=1.12.0 \
                  celery>=5.4.0 fastapi>=0.115.0 uvicorn>=0.32.0 \
                  httpx>=0.27.0 structlog>=24.1.0 aiosmtplib>=3.0.0 \
                  slack-sdk>=3.27.0 slack-bolt>=1.20.0 redis>=5.0.0 \
                  imapclient>=3.0.0 duckduckgo-search>=7.0 beautifulsoup4>=4.12
          FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim
          WORKDIR /app
          COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
          COPY --from=builder /usr/local/bin /usr/local/bin
          COPY . .
          RUN ln -s /app /app/agents_platform
          ENV PYTHONPATH=/app
          EXPOSE 8037
          CMD ["python", "-m", "agents_platform.search.web_search"]
          MCP1
          
          cat > Dockerfile.mcp-source-validator <<'MCP2'
          FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim AS builder
          WORKDIR /app
          RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*
          COPY pyproject.toml ./
          RUN pip install --no-cache-dir --upgrade pip && \
              pip install --no-cache-dir build && \
              pip install --no-cache-dir . \
              || pip install --no-cache-dir \
                  pydantic>=2.0 pydantic-settings>=2.0 pyyaml>=6.0 \
                  langgraph>=0.2.0 langchain-core>=0.3.0 langchain-openai>=0.2.0 \
                  langchain-anthropic>=0.2.0 qdrant-client>=1.12.0 \
                  celery>=5.4.0 fastapi>=0.115.0 uvicorn>=0.32.0 \
                  httpx>=0.27.0 structlog>=24.1.0 aiosmtplib>=3.0.0 \
                  slack-sdk>=3.27.0 slack-bolt>=1.20.0 redis>=5.0.0 \
                  imapclient>=3.0.0 duckduckgo-search>=7.0 beautifulsoup4>=4.12
          FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim
          WORKDIR /app
          COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
          COPY --from=builder /usr/local/bin /usr/local/bin
          COPY . .
          RUN ln -s /app /app/agents_platform
          ENV PYTHONPATH=/app
          EXPOSE 8038
          CMD ["python", "-m", "agents_platform.grounding.verifier"]
          MCP2
          
          echo "=== All Dockerfiles ready ==="
          ls -la Dockerfile*
        volumeMounts:
        - name: workspace
          mountPath: /workspace
        resources:
          limits:
            cpu: "500m"
            memory: "256Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
      containers:
      - name: kaniko-api
        image: gcr.io/kaniko-project/executor:latest
        securityContext:
          privileged: false
          runAsNonRoot: false
          runAsUser: 0
          allowPrivilegeEscalation: false
        args:
        - "--dockerfile=Dockerfile.api"
        - "--context=dir:///workspace/source"
        - "--destination=harbor-registry.harbor.svc.cluster.local:5000/ghl/agents-platform-api:latest"
        - "--insecure"
        - "--skip-tls-verify"
        - "--insecure-registry=harbor-registry.harbor.svc.cluster.local:5000"
        volumeMounts:
        - name: workspace
          mountPath: /workspace
        - name: docker-config
          mountPath: /kaniko/.docker
        resources:
          limits:
            cpu: "2000m"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
      - name: kaniko-worker
        image: gcr.io/kaniko-project/executor:latest
        securityContext:
          privileged: false
          runAsNonRoot: false
          runAsUser: 0
          allowPrivilegeEscalation: false
        args:
        - "--dockerfile=Dockerfile.worker"
        - "--context=dir:///workspace/source"
        - "--destination=harbor-registry.harbor.svc.cluster.local:5000/ghl/agents-platform-worker:latest"
        - "--insecure"
        - "--skip-tls-verify"
        - "--insecure-registry=harbor-registry.harbor.svc.cluster.local:5000"
        volumeMounts:
        - name: workspace
          mountPath: /workspace
        - name: docker-config
          mountPath: /kaniko/.docker
        resources:
          limits:
            cpu: "2000m"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
      - name: kaniko-web-search
        image: gcr.io/kaniko-project/executor:latest
        securityContext:
          privileged: false
          runAsNonRoot: false
          runAsUser: 0
          allowPrivilegeEscalation: false
        args:
        - "--dockerfile=Dockerfile.mcp-web-search"
        - "--context=dir:///workspace/source"
        - "--destination=harbor-registry.harbor.svc.cluster.local:5000/ghl/mcp-web-search:latest"
        - "--insecure"
        - "--skip-tls-verify"
        - "--insecure-registry=harbor-registry.harbor.svc.cluster.local:5000"
        volumeMounts:
        - name: workspace
          mountPath: /workspace
        - name: docker-config
          mountPath: /kaniko/.docker
        resources:
          limits:
            cpu: "2000m"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
      - name: kaniko-source-validator
        image: gcr.io/kaniko-project/executor:latest
        securityContext:
          privileged: false
          runAsNonRoot: false
          runAsUser: 0
          allowPrivilegeEscalation: false
        args:
        - "--dockerfile=Dockerfile.mcp-source-validator"
        - "--context=dir:///workspace/source"
        - "--destination=harbor-registry.harbor.svc.cluster.local:5000/ghl/mcp-source-validator:latest"
        - "--insecure"
        - "--skip-tls-verify"
        - "--insecure-registry=harbor-registry.harbor.svc.cluster.local:5000"
        volumeMounts:
        - name: workspace
          mountPath: /workspace
        - name: docker-config
          mountPath: /kaniko/.docker
        resources:
          limits:
            cpu: "2000m"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
      volumes:
      - name: workspace
        emptyDir: {}
      - name: docker-config
        configMap:
          name: harbor-docker-config
      restartPolicy: Never
  backoffLimit: 0
JOBEF
echo ""

echo "=== 3. POLL EVERY 30s FOR 12min ==="
for i in $(seq 1 24); do
  sleep 30
  POD=$(kubectl get pods -n gitea-runner -l job-name=build-agents-platform -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  PHASE=$(kubectl get pod -n gitea-runner $POD -o jsonpath='{.status.phase}' 2>/dev/null)
  echo "[$i] Pod: $POD Phase: $PHASE"
  
  if [ "$PHASE" = "Running" ]; then
    echo "  api:"
    kubectl logs -n gitea-runner $POD -c kaniko-api --tail=2 2>&1
    echo "  worker:"
    kubectl logs -n gitea-runner $POD -c kaniko-worker --tail=2 2>&1
  elif [ "$PHASE" = "Failed" ] || [ "$PHASE" = "Succeeded" ]; then
    echo "=== FINAL ==="
    echo "--- init ---"
    kubectl logs -n gitea-runner $POD -c clone --tail=10 2>&1
    echo "--- api ---"
    kubectl logs -n gitea-runner $POD -c kaniko-api --tail=10 2>&1
    echo "--- worker ---"
    kubectl logs -n gitea-runner $POD -c kaniko-worker --tail=10 2>&1
    echo "--- web-search ---"
    kubectl logs -n gitea-runner $POD -c kaniko-web-search --tail=5 2>&1
    echo "--- source-validator ---"
    kubectl logs -n gitea-runner $POD -c kaniko-source-validator --tail=5 2>&1
    break
  fi
  echo ""
done

echo ""
echo "=== 4. JOB STATUS ==="
kubectl get job build-agents-platform -n gitea-runner 2>&1
echo ""

echo "DONE"
