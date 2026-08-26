#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK IF MINIO SECRET EXISTS IN MINIO NS ==="
kubectl get secret minio-credentials -n minio 2>&1
echo ""

echo "=== 2. COPY MINIO SECRET TO ARGO-WORKFLOWS NS ==="
kubectl get secret minio-credentials -n minio -o yaml 2>/dev/null | sed 's/namespace: minio/namespace: argo-workflows/' | kubectl apply -f - 2>&1
echo ""

echo "=== 3. DELETE STUCK WORKFLOW ==="
kubectl delete wf hello-world -n argo-workflows 2>&1
echo ""

echo "=== 4. CREATE SIMPLE WORKFLOW WITHOUT ARTIFACTS ==="
cat <<'EOF' | kubectl apply -f - 2>&1
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: hello-world
  namespace: argo-workflows
spec:
  entrypoint: whalesay
  templates:
    - name: whalesay
      container:
        image: docker/whalesay:latest
        command: [cowsay]
        args: ["hello world from Argo Workflows!"]
EOF
echo ""

echo "=== 5. WAIT ==="
sleep 20
echo ""

echo "=== 6. CHECK WORKFLOW ==="
kubectl get wf -n argo-workflows 2>&1
echo ""

echo "=== 7. CHECK POD ==="
kubectl get pods -n argo-workflows 2>&1
echo ""

echo "=== 8. POD LOGS ==="
kubectl logs hello-world -n argo-workflows --all-containers 2>&1 | tail -10
echo ""

echo "DONE"
