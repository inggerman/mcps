#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. DELETE OLD JOB ==="
kubectl delete job build-agents-platform -n agents-platform 2>&1 || true
echo ""

echo "=== 2. CREATE BUILD JOB IN argocd NAMESPACE ==="
cat <<'JOBEF' | kubectl apply -f - 2>&1
apiVersion: batch/v1
kind: Job
metadata:
  name: build-agents-platform
  namespace: argocd
  labels:
    app.kubernetes.io/name: build-agents
    app.kubernetes.io/part-of: agents-platform
spec:
  ttlSecondsAfterFinished: 300
  template:
    metadata:
      labels:
        app.kubernetes.io/name: build-agents
        app.kubernetes.io/part-of: agents-platform
    spec:
      securityContext:
        runAsNonRoot: false
        runAsUser: 0
      containers:
      - name: builder
        image: docker.io/python:3.12-slim
        workingDir: /tmp
        securityContext:
          privileged: false
          runAsNonRoot: false
          runAsUser: 0
          allowPrivilegeEscalation: false
        command:
        - bash
        - -c
        - |
          set -e
          echo "=== INSTALL TOOLS ==="
          apt-get update -qq 2>&1 | tail -2
          apt-get install -y -qq curl tar git 2>&1 | tail -3
          
          echo "=== INSTALL crane ==="
          curl -sL https://github.com/google/go-containerregistry/releases/download/v0.20.2/go-containerregistry_Linux_x86_64.tar.gz | tar xz crane
          chmod +x crane && mv crane /usr/local/bin/crane
          
          echo "=== LOGIN TO HARBOR ==="
          crane auth login harbor.mrrobot.fs -u admin -p Harbor12345 2>&1
          
          echo "=== CLONE agents-platform ==="
          git clone http://gitea-http-fixed.gitea.svc.cluster.local:3000/ghl-admin/agents-platform.git /tmp/agents-platform 2>&1 | tail -3
          cd /tmp/agents-platform
          ls -la Dockerfile.api Dockerfile.worker pyproject.toml 2>&1
          
          echo "=== INSTALL PYTHON DEPS ==="
          pip install --no-cache-dir -e . 2>&1 | tail -5
          
          echo "=== CREATE APP TARBALL ==="
          tar czf /tmp/app-layer.tar.gz -C /tmp/agents-platform .
          ls -lh /tmp/app-layer.tar.gz 2>&1
          
          echo "=== BUILD API IMAGE ==="
          crane append -f /tmp/app-layer.tar.gz \
            -t harbor.mrrobot.fs/ghl/agents-platform-api:latest \
            --base docker.io/python:3.12-slim \
            --set-entrypoint '["uvicorn","agents_platform.api:app","--host","0.0.0.0","--port","8000"]' \
            --set-exposed-ports 8000 2>&1
          
          echo "=== BUILD WORKER IMAGE ==="
          crane append -f /tmp/app-layer.tar.gz \
            -t harbor.mrrobot.fs/ghl/agents-platform-worker:latest \
            --base docker.io/python:3.12-slim \
            --set-entrypoint '["celery","-A","agents_platform.worker","worker","--loglevel=info","--concurrency=2"]' 2>&1
          
          echo "=== VERIFY IMAGES ==="
          crane ls harbor.mrrobot.fs/ghl/agents-platform-api 2>&1
          crane ls harbor.mrrobot.fs/ghl/agents-platform-worker 2>&1
          
          echo "=== BUILD COMPLETE ==="
        resources:
          limits:
            cpu: "2000m"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
      restartPolicy: Never
  backoffLimit: 1
JOBEF
echo ""

echo "=== 3. WAIT 20s ==="
sleep 20
echo ""

echo "=== 4. CHECK POD ==="
kubectl get pods -n argocd -l job-name=build-agents-platform 2>&1
echo ""

echo "=== 5. CHECK LOGS ==="
kubectl logs -n argocd -l job-name=build-agents-platform --tail=20 2>&1
echo ""

echo "DONE"
