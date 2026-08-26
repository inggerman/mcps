#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. EXISTING WORKFLOWS ==="
kubectl get wf -A 2>&1
echo ""

echo "=== 2. WORKFLOW TEMPLATES ==="
kubectl get workflowtemplates -A 2>&1
echo ""

echo "=== 3. CLUSTER WORKFLOW TEMPLATES ==="
kubectl get clusterworkflowtemplates 2>&1
echo ""

echo "=== 4. CHECK RBAC FOR ARGO SERVER ==="
kubectl get clusterrolebinding -o wide 2>&1 | grep argo
echo ""

echo "=== 5. ARGO WORKFLOWS CONFIG ==="
kubectl get cm argo-workflows-workflow-controller-configmap -n argo-workflows -o yaml 2>&1 | grep -A5 "containerRuntimeExecutor\|namespace\|nodeEvents"
echo ""

echo "=== 6. CREATE A SAMPLE WORKFLOW ==="
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

echo "=== 7. CHECK WORKFLOW ==="
sleep 5
kubectl get wf -n argo-workflows 2>&1
echo ""

echo "=== 8. WORKFLOW LOGS ==="
kubectl logs -n argo-workflows -l app.kubernetes.io/component=workflow-controller --tail=10 2>&1
echo ""

echo "DONE"
