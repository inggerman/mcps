#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

HARBOR="harbor.mrrobot.fs"
HARBOR_USER="admin"
HARBOR_PASS="Harbor12345"

echo "=== 1. CREATE BUILD JOB (crane-based, no privileged) ==="
cat <<'JOBEF' | kubectl apply -f - 2>&1
apiVersion: batch/v1
kind: Job
metadata:
  name: build-agents-platform
  namespace: default
  labels:
    app.kubernetes.io/name: build-agents
    app.kubernetes.io/part-of: platform
spec:
  ttlSecondsAfterFinished: 300
  template:
    metadata:
      labels:
        app.kubernetes.io/name: build-agents
        app.kubernetes.io/part-of: platform
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: builder
        image: docker.io/python:3.12-slim
        workingDir: /tmp
        env:
        - name: HARBOR_USER
          value: "admin"
        - name: HARBOR_PASS
          value: "Harbor12345"
        - name: HARBOR
          value: "harbor.mrrobot.fs"
        command:
        - bash
        - -c
        - |
          set -e
          echo "=== INSTALL crane ==="
          apt-get update -qq && apt-get install -y -qq curl tar git 2>&1 | tail -3
          curl -sL https://github.com/google/go-containerregistry/releases/download/v0.20.2/go-containerregistry_Linux_x86_64.tar.gz | tar xz crane
          mv crane /usr/local/bin/crane
          chmod +x /usr/local/bin/crane
          
          echo "=== LOGIN TO HARBOR ==="
          crane auth login harbor.mrrobot.fs -u admin -p Harbor12345 2>&1
          
          echo "=== CLONE agents-platform ==="
          git clone http://gitea-http-fixed.gitea.svc.cluster.local:3000/ghl-admin/agents-platform.git /tmp/agents-platform 2>&1 | tail -3
          cd /tmp/agents-platform
          
          echo "=== INSTALL DEPS IN VENV ==="
          pip install --no-cache-dir -e . 2>&1 | tail -5
          
          echo "=== CREATE APP TARBALL ==="
          tar czf /tmp/app-layer.tar.gz -C /tmp/agents-platform .
          
          echo "=== BUILD API IMAGE (crane append on python:3.12-slim) ==="
          crane append -f /tmp/app-layer.tar.gz -t harbor.mrrobot.fs/ghl/agents-platform-api:latest --base docker.io/python:3.12-slim --set-entrypoint '["uvicorn","agents_platform.api:app","--host","0.0.0.0","--port","8000"]' --set-exposed-ports 8000 2>&1
          
          echo "=== BUILD WORKER IMAGE ==="
          crane append -f /tmp/app-layer.tar.gz -t harbor.mrrobot.fs/ghl/agents-platform-worker:latest --base docker.io/python:3.12-slim --set-entrypoint '["celery","-A","agents_platform.worker","worker","--loglevel=info","--concurrency=2"]' 2>&1
          
          echo "=== DONE ==="
        resources:
          limits:
            cpu: "2000m"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
      restartPolicy: Never
  backoffLimit: 2
JOBEF
echo ""

echo "=== 2. WAIT FOR JOB (up to 10min) ==="
sleep 10
kubectl get job build-agents-platform 2>&1
echo ""

echo "=== 3. CHECK POD ==="
kubectl get pods -l job-name=build-agents-platform 2>&1
echo ""

echo "DONE"
