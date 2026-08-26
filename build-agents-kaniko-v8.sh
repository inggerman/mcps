#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

HARBOR="harbor.mrrobot.fs"
HARBOR_USER="admin"
HARBOR_PASS="Harbor12345"

echo "=== 1. COPY python:3.12-slim TO HARBOR ==="
crane copy docker.io/library/python:3.12-slim "$HARBOR/ghl/python:3.12-slim" 2>&1
echo ""

echo "=== 2. VERIFY ==="
crane ls "$HARBOR/ghl/python" 2>&1
echo ""

echo "=== 3. DELETE OLD JOB ==="
kubectl delete job build-agents-platform -n gitea-runner 2>&1 || true
echo ""

echo "=== 4. CREATE KANIKO JOB WITH HARBOR BASE IMAGE ==="
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
          
          # Replace base image in Dockerfiles to use Harbor mirror
          sed -i 's|FROM docker.io/python:3.12-slim|FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim|g' /workspace/source/Dockerfile.api
          sed -i 's|FROM docker.io/python:3.12-slim|FROM harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim|g' /workspace/source/Dockerfile.worker
          
          echo "=== Modified Dockerfile.api ==="
          head -3 /workspace/source/Dockerfile.api
          echo "=== Modified Dockerfile.worker ==="
          head -3 /workspace/source/Dockerfile.worker
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

echo "=== 5. POLL EVERY 30s FOR 8min ==="
for i in $(seq 1 16); do
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
echo "=== 6. JOB STATUS ==="
kubectl get job build-agents-platform -n gitea-runner 2>&1
echo ""

echo "DONE"
