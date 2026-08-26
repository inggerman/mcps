#!/bin/bash
# =============================================================================
# Build all 4 agents-platform images via Kaniko + deploy + verify
# =============================================================================
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

GITEA_IP=$(kubectl get svc gitea-http-fixed -n gitea -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "Gitea IP: $GITEA_IP"

echo "=== 1. DELETE OLD JOB ==="
kubectl delete job build-agents-platform -n gitea-runner 2>&1 || true
echo ""

# Write Job manifest to temp file
cat > /tmp/kaniko-job-final.yaml <<EOF
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

          # Fix syntax error in slack_notifier.py (missing ] in context[:2900])
          sed -i 's/2900}/2900]}/g' notifications/slack_notifier.py
          echo "=== Fixed slack_notifier.py ==="
          grep -n '2900' notifications/slack_notifier.py

          # Fix api/__init__.py to export app (api.py is shadowed by api/ dir)
          printf '"""API REST FastAPI — Entry point para requerimientos y webhooks.\\n"""\\nfrom __future__ import annotations\\nimport logging\\nimport uuid\\nfrom typing import Any\\nfrom fastapi import FastAPI, HTTPException\\nfrom pydantic import BaseModel\\nfrom agents_platform.api.webhook import router as webhook_router\\nfrom agents_platform.templates import RequirementTemplate, validate_yaml\\n\\nlogger = logging.getLogger(__name__)\\n\\napp = FastAPI(\\n    title="Autonomous Agents Platform API",\\n    description="Plataforma de agentes autonomos",\\n    version="0.1.0",\\n)\\napp.include_router(webhook_router)\\n\\nclass RequirementInput(BaseModel):\\n    yaml_content: str | None = None\\n    json_content: dict[str, Any] | None = None\\n\\nclass JobResponse(BaseModel):\\n    job_id: str\\n    status: str\\n    message: str\\n\\n_jobs: dict[str, dict[str, Any]] = {}\\n\\n@app.get("/health")\\nasync def health() -> dict[str, str]:\\n    return {"status": "healthy"}\\n\\n@app.post("/api/v1/requirement", response_model=JobResponse)\\nasync def submit_requirement(input: RequirementInput) -> JobResponse:\\n    if input.yaml_content:\\n        try:\\n            req = validate_yaml(input.yaml_content)\\n        except ValueError as exc:\\n            raise HTTPException(status_code=422, detail=str(exc))\\n    elif input.json_content:\\n        try:\\n            req = RequirementTemplate(**input.json_content)\\n        except Exception as exc:\\n            raise HTTPException(status_code=422, detail=str(exc))\\n    else:\\n        raise HTTPException(status_code=400, detail="Must provide yaml_content or json_content")\\n    job_id = str(uuid.uuid4())\\n    _jobs[job_id] = {"job_id": job_id, "status": "queued", "requirement": req.to_dict(), "result": None, "error": None}\\n    logger.info(f"Job {job_id} queued: {req.title}")\\n    return JobResponse(job_id=job_id, status="queued", message=f"Requirement {req.title!r} queued")\\n\\n@app.get("/api/v1/jobs/{job_id}")\\nasync def get_job(job_id: str) -> dict[str, Any]:\\n    if job_id not in _jobs:\\n        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")\\n    return _jobs[job_id]\\n\\n@app.get("/api/v1/jobs")\\nasync def list_jobs(limit: int = 20) -> dict[str, Any]:\\n    jobs = list(_jobs.values())[-limit:]\\n    return {"jobs": jobs, "total": len(_jobs)}\\n\\n__all__ = ["app", "webhook_router"]\\n' > api/__init__.py
          echo "=== Fixed api/__init__.py ==="
          head -5 api/__init__.py

          # Fix worker.py to use settings instead of hardcoded URLs
          sed -i 's|broker="amqp://rabbitmq.rabbitmq.svc.cluster.local:5672"|broker=settings.rabbitmq_url|g' worker.py
          sed -i 's|backend="redis://redis.databases.svc.cluster.local:6379/2"|backend=settings.redis_url|g' worker.py
          if ! grep -q 'from agents_platform.config import settings' worker.py; then
            sed -i '/from celery import Celery/a from agents_platform.config import settings' worker.py
          fi
          echo "=== Fixed worker.py ==="
          grep -n 'settings\.' worker.py

          # Fix Dockerfiles to use Harbor base image + symlink + PYTHONPATH
          sed -i 's|FROM docker.io/python:3.12-slim|FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim|g' Dockerfile.api
          sed -i 's|FROM docker.io/python:3.12-slim|FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim|g' Dockerfile.worker
          sed -i '/^RUN pip install --no-cache-dir \.$/d' Dockerfile.api
          sed -i '/^RUN pip install --no-cache-dir \.$/d' Dockerfile.worker
          sed -i '/^COPY \. \.\$/a RUN ln -s /app /app/agents_platform\n\nENV PYTHONPATH=/app' Dockerfile.api
          sed -i '/^COPY \. \.\$/a RUN ln -s /app /app/agents_platform\n\nENV PYTHONPATH=/app' Dockerfile.worker

          echo "=== Dockerfile.api ==="
          cat Dockerfile.api
          echo ""

          # Create Dockerfile.mcp-web-search
          printf 'FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim AS builder\\nWORKDIR /app\\nRUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*\\nCOPY pyproject.toml ./\\nRUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir build && pip install --no-cache-dir . || pip install --no-cache-dir pydantic>=2.0 pydantic-settings>=2.0 pyyaml>=6.0 langgraph>=0.2.0 langchain-core>=0.3.0 langchain-openai>=0.2.0 langchain-anthropic>=0.2.0 qdrant-client>=1.12.0 celery>=5.4.0 fastapi>=0.115.0 uvicorn>=0.32.0 httpx>=0.27.0 structlog>=24.1.0 aiosmtplib>=3.0.0 slack-sdk>=3.27.0 slack-bolt>=1.20.0 redis>=5.0.0 imapclient>=3.0.0 duckduckgo-search>=7.0 beautifulsoup4>=4.12\\nFROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim\\nWORKDIR /app\\nCOPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages\\nCOPY --from=builder /usr/local/bin /usr/local/bin\\nCOPY . .\\nRUN ln -s /app /app/agents_platform\\nENV PYTHONPATH=/app\\nEXPOSE 8037\\nCMD ["python", "-m", "agents_platform.search"]\\n' > Dockerfile.mcp-web-search

          # Create Dockerfile.mcp-source-validator
          printf 'FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim AS builder\\nWORKDIR /app\\nRUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*\\nCOPY pyproject.toml ./\\nRUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir build && pip install --no-cache-dir . || pip install --no-cache-dir pydantic>=2.0 pydantic-settings>=2.0 pyyaml>=6.0 langgraph>=0.2.0 langchain-core>=0.3.0 langchain-openai>=0.2.0 langchain-anthropic>=0.2.0 qdrant-client>=1.12.0 celery>=5.4.0 fastapi>=0.115.0 uvicorn>=0.32.0 httpx>=0.27.0 structlog>=24.1.0 aiosmtplib>=3.0.0 slack-sdk>=3.27.0 slack-bolt>=1.20.0 redis>=5.0.0 imapclient>=3.0.0 duckduckgo-search>=7.0 beautifulsoup4>=4.12\\nFROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim\\nWORKDIR /app\\nCOPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages\\nCOPY --from=builder /usr/local/bin /usr/local/bin\\nCOPY . .\\nRUN ln -s /app /app/agents_platform\\nENV PYTHONPATH=/app\\nEXPOSE 8038\\nCMD ["python", "-m", "agents_platform.grounding"]\\n' > Dockerfile.mcp-source-validator

          # Create search/__main__.py (HTTP server wrapper)
          printf '"""MCP Web Search Server — HTTP wrapper.\\n"""\\nfrom __future__ import annotations\\nimport logging\\nimport os\\nfrom typing import Any\\nfrom fastapi import FastAPI\\nfrom pydantic import BaseModel\\nfrom agents_platform.search.web_search import web_search, search_for_context\\n\\nlogger = logging.getLogger(__name__)\\napp = FastAPI(title="MCP Web Search", version="0.1.0")\\n\\nclass SearchRequest(BaseModel):\\n    query: str\\n    max_results: int = 5\\n\\nclass ContextSearchRequest(BaseModel):\\n    query: str\\n    technology: str = ""\\n    max_results: int = 5\\n\\n@app.get("/health")\\nasync def health() -> dict[str, str]:\\n    return {"status": "healthy", "service": "mcp-web-search"}\\n\\n@app.post("/search")\\nasync def search(req: SearchRequest) -> dict[str, Any]:\\n    results = await web_search(req.query, req.max_results)\\n    return {"query": req.query, "results": results, "count": len(results)}\\n\\n@app.post("/search/context")\\nasync def search_context(req: ContextSearchRequest) -> dict[str, Any]:\\n    context = await search_for_context(req.query, req.technology, req.max_results)\\n    return {"query": req.query, "context": context}\\n\\nif __name__ == "__main__":\\n    import uvicorn\\n    port = int(os.environ.get("MCP_PORT", "8037"))\\n    uvicorn.run(app, host="0.0.0.0", port=port)\\n' > search/__main__.py

          # Create grounding/__main__.py (HTTP server wrapper)
          printf '"""MCP Source Validator Server — HTTP wrapper.\\n"""\\nfrom __future__ import annotations\\nimport logging\\nimport os\\nfrom typing import Any\\nfrom fastapi import FastAPI\\nfrom pydantic import BaseModel\\nfrom agents_platform.grounding.verifier import get_verifier\\n\\nlogger = logging.getLogger(__name__)\\napp = FastAPI(title="MCP Source Validator", version="0.1.0")\\n\\nclass VerifyRequest(BaseModel):\\n    response: str\\n    sources: str\\n\\n@app.get("/health")\\nasync def health() -> dict[str, str]:\\n    return {"status": "healthy", "service": "mcp-source-validator"}\\n\\n@app.post("/verify")\\nasync def verify(req: VerifyRequest) -> dict[str, Any]:\\n    verifier = get_verifier()\\n    return verifier.verify_response(req.response, req.sources)\\n\\n@app.post("/hallucination_score")\\nasync def hallucination_score(req: VerifyRequest) -> dict[str, Any]:\\n    verifier = get_verifier()\\n    score = verifier.hallucination_score(req.response, req.sources)\\n    return {"hallucination_score": score}\\n\\nif __name__ == "__main__":\\n    import uvicorn\\n    port = int(os.environ.get("MCP_PORT", "8038"))\\n    uvicorn.run(app, host="0.0.0.0", port=port)\\n' > grounding/__main__.py

          echo "=== All files ready ==="
          ls -la Dockerfile* search/__main__.py grounding/__main__.py
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
EOF

echo "=== 2. APPLY JOB ==="
kubectl apply -f /tmp/kaniko-job-final.yaml 2>&1
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
    kubectl logs -n gitea-runner $POD -c clone --tail=15 2>&1
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

echo "=== 5. ROLLOUT RESTART ALL ==="
kubectl rollout restart deployment/agents-platform-api -n agents-platform 2>&1
kubectl rollout restart deployment/agents-platform-worker -n agents-platform 2>&1
kubectl rollout restart deployment/agents-platform-daemon -n agents-platform 2>&1
kubectl rollout restart deployment/mcp-web-search -n agents-platform 2>&1
kubectl rollout restart deployment/mcp-source-validator -n agents-platform 2>&1
echo ""

echo "=== 6. FORCE ARGO CD REFRESH ==="
kubectl patch application agents-platform-prod -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== 7. WAIT 60s ==="
sleep 60
echo ""

echo "=== 8. CHECK PODS ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== 9. CHECK LOGS FOR NON-RUNNING PODS ==="
for pod in $(kubectl get pods -n agents-platform -o jsonpath='{.items[?(@.status.phase!="Running")].metadata.name}' 2>/dev/null); do
  echo "--- $pod ---"
  kubectl logs -n agents-platform $pod --tail=15 2>&1
  echo ""
done

echo "=== 10. ARGO CD STATUS ==="
kubectl get applications -A 2>&1
echo ""

echo "DONE"
