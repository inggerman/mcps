#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. n8n PODS ==="
kubectl get pods -n n8n -o wide 2>&1

echo ""
echo "=== 2. n8n SERVICES ==="
kubectl get svc -n n8n 2>&1

echo ""
echo "=== 3. n8n INGRESS ==="
kubectl get ingress -n n8n 2>&1

echo ""
echo "=== 4. n8n PVC ==="
kubectl get pvc -n n8n 2>&1

echo ""
echo "=== 5. n8n DEPLOYMENT ==="
kubectl get deploy -n n8n 2>&1

echo ""
echo "=== 6. n8n POD LOGS (last 30) ==="
N8N_POD=$(kubectl get pod -n n8n -l app.kubernetes.io/name=n8n -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -z "$N8N_POD" ]; then
  N8N_POD=$(kubectl get pod -n n8n -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
fi
echo "Pod: $N8N_POD"
kubectl logs -n n8n $N8N_POD --tail=30 2>&1

echo ""
echo "=== 7. n8n POD EVENTS ==="
kubectl get events -n n8n --sort-by=.lastTimestamp 2>&1 | tail -10

echo ""
echo "=== 8. n8n SECRET ==="
kubectl get secret -n n8n 2>&1

echo ""
echo "=== 9. n8n DESCRIBE POD ==="
kubectl describe pod -n n8n $N8N_POD 2>&1 | tail -40

echo ""
echo "=== 10. HEALTH CHECK ==="
kubectl exec -n n8n $N8N_POD -- wget -qO- http://localhost:5678/healthz 2>&1

echo ""
echo "=== 11. NAMESPACE EXISTS? ==="
kubectl get ns n8n 2>&1

echo "DONE"
