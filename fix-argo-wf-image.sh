#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. DELETE OLD WORKFLOW ==="
kubectl delete wf hello-world -n argo-workflows 2>&1
echo ""

echo "=== 2. CREATE WORKFLOW WITH MODERN IMAGE ==="
cat <<'EOF' | kubectl apply -f - 2>&1
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: hello-world
  namespace: argo-workflows
spec:
  entrypoint: say-hello
  templates:
    - name: say-hello
      container:
        image: harbor.mrrobot.fs/ghl/mcp-architecture:latest
        command: [sh, -c]
        args: ["echo 'Hello World from Argo Workflows!' && echo 'Cluster is working correctly'"]
EOF
echo ""

echo "=== 3. WAIT ==="
sleep 30
echo ""

echo "=== 4. CHECK WORKFLOW ==="
kubectl get wf -n argo-workflows 2>&1
echo ""

echo "=== 5. CHECK PODS ==="
kubectl get pods -n argo-workflows 2>&1
echo ""

echo "=== 6. LOGS ==="
kubectl logs hello-world -n argo-workflows -c main 2>&1
echo ""

echo "DONE"
