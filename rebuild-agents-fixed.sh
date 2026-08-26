#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. DELETE OLD JOB ==="
kubectl delete job build-agents-platform -n gitea-runner 2>&1 || true
echo ""

echo "=== 2. CREATE KANIKO JOB WITH DOCKERFILE FIXES ==="
cat <<'JOBEF' | kubectl apply -f - 2>&1
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
          git clone "http://ghl-admin:ChangeMe123!@gitea-http-fixed.gitea.svc.cluster.local:3000/ghl/agents-platform.git" /workspace/source 2>&1
          cd /workspace/source
          
          # Fix base images to use Harbor mirror
          sed -i 's|FROM docker.io/python:3.12-slim|FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim|g' Dockerfile.api
          sed -i 's|FROM docker.io/python:3.12-slim|FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim|g' Dockerfile.worker
          
          # Fix: add pip install and PYTHONPATH in final stage
          # For Dockerfile.api
          sed -i '/^COPY \. \.$/a RUN pip install --no-cache-dir .\n\nENV PYTHONPATH=/app' Dockerfile.api
          # For Dockerfile.worker  
          sed -i '/^COPY \. \.$/a RUN pip install --no-cache-dir .\n\nENV PYTHONPATH=/app' Dockerfile.worker
          
          echo "=== Dockerfile.api ==="
          cat Dockerfile.api
          echo ""
          echo "=== Dockerfile.worker ==="
          cat Dockerfile.worker
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

echo "=== 3. POLL EVERY 30s FOR 10min ==="
for i in $(seq 1 20); do
  sleep 30
  POD=$(kubectl get pods -n gitea-runner -l job-name=build-agents-platform -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  PHASE=$(kubectl get pod -n gitea-runner $POD -o jsonpath='{.status.phase}' 2>/dev/null)
  echo "[$i] Pod: $POD Phase: $PHASE"
  
  if [ "$PHASE" = "Running" ]; then
    echo "  api:"
    kubectl logs -n gitea-runner $POD -c kaniko-api --tail=3 2>&1
    echo "  worker:"
    kubectl logs -n gitea-runner $POD -c kaniko-worker --tail=3 2>&1
  elif [ "$PHASE" = "Failed" ] || [ "$PHASE" = "Succeeded" ]; then
    echo "=== FINAL ==="
    echo "--- api ---"
    kubectl logs -n gitea-runner $POD -c kaniko-api --tail=25 2>&1
    echo "--- worker ---"
    kubectl logs -n gitea-runner $POD -c kaniko-worker --tail=25 2>&1
    break
  fi
  echo ""
done

echo ""
echo "=== 4. JOB STATUS ==="
kubectl get job build-agents-platform -n gitea-runner 2>&1
echo ""

echo "DONE"
