#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. WAIT 30s for n8n ==="
sleep 30
echo ""

echo "=== 2. N8N POD ==="
kubectl get pods -n n8n 2>&1
echo ""

echo "=== 3. TEST N8N /metrics ==="
N8N_SVC_IP=$(kubectl get svc n8n -n n8n -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
PROM_POD=$(kubectl get pod -n observability -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
kubectl exec -n observability $PROM_POD -c prometheus -- wget -qO- --timeout=5 http://$N8N_SVC_IP:5678/metrics 2>&1 | head -10
echo ""

echo "=== 4. CREATE N8N ServiceMonitor (correct port) ==="
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

echo "=== 5. KUBECOST STATUS ==="
kubectl get pods -n kubecost 2>&1
echo ""

echo "=== 6. HOMEPAGE - TEST FROM INSIDE ==="
HOMEPAGE_IP=$(kubectl get svc homepage -n homepage -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
kubectl exec -n observability $PROM_POD -c prometheus -- wget -qO- --timeout=5 http://$HOMEPAGE_IP:3000/ 2>&1 | head -10
echo ""

echo "DONE"
