#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. DELETE OLD JOB ==="
kubectl delete job build-agents-platform -n gitea-runner 2>&1 || true
echo ""

echo "=== 2. CREATE JOB TO COPY python:3.12-slim TO HARBOR ==="
cat <<'JOBEF' | kubectl apply -f - 2>&1
apiVersion: batch/v1
kind: Job
metadata:
  name: copy-python-base
  namespace: gitea-runner
  labels:
    app.kubernetes.io/name: copy-python
    app.kubernetes.io/part-of: agents-platform
spec:
  ttlSecondsAfterFinished: 3600
  template:
    metadata:
      labels:
        app.kubernetes.io/name: copy-python
        app.kubernetes.io/part-of: agents-platform
    spec:
      securityContext:
        runAsNonRoot: false
        runAsUser: 0
      containers:
      - name: crane
        image: docker.io/alpine:latest
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
          echo "=== INSTALL crane ==="
          apk add --no-cache curl 2>&1 | tail -2
          curl -sL https://github.com/google/go-containerregistry/releases/download/v0.20.2/go-containerregistry_Linux_x86_64.tar.gz | tar xz crane
          chmod +x crane && mv crane /usr/local/bin/crane
          
          echo "=== LOGIN TO HARBOR (internal) ==="
          crane auth login harbor-registry.harbor.svc.cluster.local:5000 -u admin -p Harbor12345 --insecure 2>&1
          
          echo "=== COPY python:3.12-slim TO HARBOR ==="
          crane copy docker.io/library/python:3.12-slim harbor-registry.harbor.svc.cluster.local:5000/ghl/python:3.12-slim --insecure 2>&1
          
          echo "=== VERIFY ==="
          crane ls harbor-registry.harbor.svc.cluster.local:5000/ghl/python --insecure 2>&1
          
          echo "=== DONE ==="
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
          requests:
            cpu: "200m"
            memory: "128Mi"
      restartPolicy: Never
  backoffLimit: 0
JOBEF
echo ""

echo "=== 3. POLL EVERY 20s FOR 3min ==="
for i in $(seq 1 9); do
  sleep 20
  POD=$(kubectl get pods -n gitea-runner -l job-name=copy-python-base -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  PHASE=$(kubectl get pod -n gitea-runner $POD -o jsonpath='{.status.phase}' 2>/dev/null)
  echo "[$i] Pod: $POD Phase: $PHASE"
  
  if [ "$PHASE" = "Running" ]; then
    kubectl logs -n gitea-runner $POD --tail=5 2>&1
  elif [ "$PHASE" = "Failed" ] || [ "$PHASE" = "Succeeded" ]; then
    echo "=== FINAL ==="
    kubectl logs -n gitea-runner $POD --tail=20 2>&1
    break
  fi
  echo ""
done

echo ""
echo "=== 4. JOB STATUS ==="
kubectl get job copy-python-base -n gitea-runner 2>&1
echo ""

echo "DONE"
