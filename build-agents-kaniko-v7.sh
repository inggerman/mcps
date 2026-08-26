#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ADD NETWORKPOLICY: ALLOW gitea-runner -> harbor ==="
cat <<'NPEOF' | kubectl apply -f - 2>&1
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-gitea-runner-ingress
  namespace: harbor
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: gitea-runner
NPEOF
echo ""

echo "=== 2. DELETE OLD JOB ==="
kubectl delete job build-agents-platform -n gitea-runner 2>&1 || true
echo ""

echo "=== 3. CREATE KANIKO JOB ==="
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
          ls /workspace/source/Dockerfile.api /workspace/source/Dockerfile.worker /workspace/source/pyproject.toml 2>&1
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

echo "=== 4. POLL EVERY 20s FOR 6min ==="
for i in $(seq 1 18); do
  sleep 20
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
    kubectl logs -n gitea-runner $POD -c kaniko-api --tail=20 2>&1
    echo "--- worker ---"
    kubectl logs -n gitea-runner $POD -c kaniko-worker --tail=20 2>&1
    break
  fi
  echo ""
done

echo ""
echo "=== 5. JOB STATUS ==="
kubectl get job build-agents-platform -n gitea-runner 2>&1
echo ""

echo "DONE"
