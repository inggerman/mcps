#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK gitea-runner NAMESPACE ==="
kubectl get ns gitea-runner 2>&1
echo ""

echo "=== 2. CHECK NETWORKPOLICIES IN gitea-runner ==="
kubectl get netpol -n gitea-runner 2>&1
echo ""

echo "=== 3. CHECK HARBOR REGISTRY SVC ==="
kubectl get svc -n harbor 2>&1 | grep registry
echo ""

echo "=== 4. DELETE OLD JOB ==="
kubectl delete job build-agents-platform -n harbor 2>&1 || true
echo ""

echo "=== 5. CREATE KANIKO JOB IN gitea-runner NAMESPACE ==="
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
  ttlSecondsAfterFinished: 600
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
          echo "=== CLONE agents-platform ==="
          git clone "http://ghl-admin:ChangeMe123!@gitea-http-fixed.gitea.svc.cluster.local:3000/ghl/agents-platform.git" /workspace/source 2>&1
          ls -la /workspace/source/Dockerfile.api /workspace/source/Dockerfile.worker /workspace/source/pyproject.toml 2>&1
          echo "=== CLONE DONE ==="
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
  backoffLimit: 2
JOBEF
echo ""

echo "=== 6. CREATE DOCKER CONFIG ==="
cat <<'CFGEOF' | kubectl apply -f - 2>&1
apiVersion: v1
kind: ConfigMap
metadata:
  name: harbor-docker-config
  namespace: gitea-runner
data:
  config.json: |
    {
      "auths": {
        "harbor-registry.harbor.svc.cluster.local:5000": {
          "auth": "YWRtaW46SGFyYm9yMTIzNDU="
        }
      }
    }
CFGEOF
echo ""

echo "=== 7. WAIT 90s ==="
sleep 90
echo ""

echo "=== 8. CHECK POD ==="
kubectl get pods -n gitea-runner -l job-name=build-agents-platform 2>&1
echo ""

echo "=== 9. CHECK LOGS ==="
POD=$(kubectl get pods -n gitea-runner -l job-name=build-agents-platform -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
echo "Pod: $POD"
echo ""
echo "--- INIT ---"
kubectl logs -n gitea-runner $POD -c clone 2>&1
echo ""
echo "--- KANIKO-API ---"
kubectl logs -n gitea-runner $POD -c kaniko-api --tail=20 2>&1
echo ""
echo "--- KANIKO-WORKER ---"
kubectl logs -n gitea-runner $POD -c kaniko-worker --tail=20 2>&1
echo ""

echo "DONE"
