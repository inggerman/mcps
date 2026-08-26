#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. KUBECOST - CHECK WHY COST-ANALYZER IS DOWN ==="
kubectl get pods -n kubecost -l app.kubernetes.io/name=cost-analyzer 2>&1
kubectl describe deploy kubecost-cost-analyzer -n kubecost 2>&1 | grep -A5 "Replicas:" | head -8
kubectl get events -n kubecost --sort-by=.lastTimestamp 2>&1 | tail -10
echo ""

echo "=== 2. KUBECOST - SCALE UP ==="
kubectl scale deploy kubecost-cost-analyzer -n kubecost --replicas=1 2>&1
echo ""

echo "=== 3. N8N - RECREATE ServiceMonitor ==="
cat <<'EOF' | kubectl apply -f - 2>&1
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: n8n
  namespace: observability
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: n8n
  namespaceSelector:
    matchNames: [n8n]
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
EOF
echo ""

echo "=== 4. WAIT 15s ==="
sleep 15
echo ""

echo "=== 5. N8N /metrics TEST ==="
N8N_SVC_IP=$(kubectl get svc n8n -n n8n -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
PROM_POD=$(kubectl get pod -n observability -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
kubectl exec -n observability $PROM_POD -c prometheus -- wget -qO- --timeout=5 http://$N8N_SVC_IP/metrics 2>&1 | head -10
echo ""

echo "=== 6. KUBECOST POD ==="
kubectl get pods -n kubecost 2>&1
echo ""

echo "DONE"
