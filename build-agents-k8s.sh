#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

HARBOR="harbor.mrrobot.fs"
HARBOR_USER="admin"
HARBOR_PASS="Harbor12345"

echo "=== 1. CHECK crane append CAPABILITY ==="
crane append --help 2>&1 | head -5
echo ""

echo "=== 2. CREATE BUILD JOB IN K8s ==="
cat <<'JOBEF' | kubectl apply -f - 2>&1
apiVersion: batch/v1
kind: Job
metadata:
  name: build-agents-platform
  namespace: default
spec:
  ttlSecondsAfterFinished: 300
  template:
    spec:
      securityContext:
        runAsUser: 0
      containers:
      - name: builder
        image: docker.io/library/docker:24-dind
        securityContext:
          privileged: true
        env:
        - name: HARBOR_USER
          value: "admin"
        - name: HARBOR_PASS
          value: "Harbor12345"
        - name: HARBOR
          value: "harbor.mrrobot.fs"
        command:
        - sh
        - -c
        - |
          echo "=== START DOCKER DAEMON ==="
          dockerd-entrypoint.sh &
          sleep 10
          
          echo "=== LOGIN TO HARBOR ==="
          docker login harbor.mrrobot.fs -u admin -p Harbor12345 2>&1
          
          echo "=== CLONE agents-platform REPO ==="
          apk add --no-cache git 2>&1 | tail -2
          git clone http://gitea-http-fixed.gitea.svc.cluster.local:3000/ghl-admin/agents-platform.git /tmp/agents-platform 2>&1 | tail -3
          
          if [ ! -d /tmp/agents-platform ]; then
            echo "Repo not found, trying alternative URL"
            git clone http://10.43.200.50:3000/ghl-admin/agents-platform.git /tmp/agents-platform 2>&1 | tail -3
          fi
          
          cd /tmp/agents-platform
          
          echo "=== BUILD API IMAGE ==="
          docker build -f Dockerfile.api -t harbor.mrrobot.fs/ghl/agents-platform-api:latest . 2>&1 | tail -10
          
          echo "=== BUILD WORKER IMAGE ==="
          docker build -f Dockerfile.worker -t harbor.mrrobot.fs/ghl/agents-platform-worker:latest . 2>&1 | tail -10
          
          echo "=== PUSH API ==="
          docker push harbor.mrrobot.fs/ghl/agents-platform-api:latest 2>&1 | tail -5
          
          echo "=== PUSH WORKER ==="
          docker push harbor.mrrobot.fs/ghl/agents-platform-worker:latest 2>&1 | tail -5
          
          echo "=== DONE ==="
      restartPolicy: Never
  backoffLimit: 2
JOBEF
echo ""

echo "=== 3. WAIT FOR JOB ==="
kubectl wait job/build-agents-platform --for=condition=complete --timeout=600s 2>&1 &
WAIT_PID=$!
echo "  Waiting up to 10min..."
echo ""

echo "=== 4. CHECK JOB STATUS ==="
kubectl get job build-agents-platform 2>&1
echo ""

echo "=== 5. CHECK POD LOGS ==="
kubectl logs job/build-agents-platform 2>&1 | tail -30
echo ""

echo "DONE"
