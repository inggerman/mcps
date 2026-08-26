#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. DELETE OLD JOB ==="
kubectl delete job build-agents-platform -n argocd 2>&1 || true
echo ""

echo "=== 2. CREATE KANIKO BUILD JOB ==="
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
          git clone http://gitea-http-fixed.gitea.svc.cluster.local:3000/ghl-admin/agents-platform.git /workspace/source 2>&1
          ls -la /workspace/source/Dockerfile.api /workspace/source/Dockerfile.worker /workspace/source/pyproject.toml 2>&1
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
        - "--destination=harbor.mrrobot.fs/ghl/agents-platform-api:latest"
        - "--insecure"
        - "--skip-tls-verify"
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
        - "--destination=harbor.mrrobot.fs/ghl/agents-platform-worker:latest"
        - "--insecure"
        - "--skip-tls-verify"
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
  backoffLimit: 1
JOBEF
echo ""

echo "=== 3. CREATE HARBOR DOCKER CONFIG ==="
cat <<'CFGEOF' | kubectl apply -f - 2>&1
apiVersion: v1
kind: ConfigMap
metadata:
  name: harbor-docker-config
  namespace: argocd
data:
  config.json: |
    {
      "auths": {
        "harbor.mrrobot.fs": {
          "auth": "YWRtaW46SGFyYm9yMTIzNDU="
        }
      }
    }
CFGEOF
echo ""

echo "=== 4. WAIT 30s ==="
sleep 30
echo ""

echo "=== 5. CHECK POD ==="
kubectl get pods -n argocd -l job-name=build-agents-platform 2>&1
echo ""

echo "=== 6. CHECK LOGS ==="
kubectl logs -n argocd -l job-name=build-agents-platform --tail=30 2>&1
echo ""

echo "DONE"
