#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. TEST MCP ENDPOINTS (using python from prometheus pod) ==="
MCP_SVC_IP=$(kubectl get svc mcp-calendar -n mcps -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
PROM_POD=$(kubectl get pod -n observability -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
echo "  mcp-calendar IP: $MCP_SVC_IP, prometheus pod: $PROM_POD"

echo "  --- Root / ---"
kubectl exec -n observability $PROM_POD -c prometheus -- wget -qO- --timeout=3 http://$MCP_SVC_IP/ 2>&1 | head -5
echo ""

echo "  --- /metrics ---"
kubectl exec -n observability $PROM_POD -c prometheus -- wget -qO- --timeout=3 http://$MCP_SVC_IP/metrics 2>&1 | head -5
echo ""

echo "  --- /health ---"
kubectl exec -n observability $PROM_POD -c prometheus -- wget -qO- --timeout=3 http://$MCP_SVC_IP/health 2>&1 | head -5
echo ""

echo "=== 2. N8N ENDPOINTS ==="
N8N_SVC_IP=$(kubectl get svc n8n -n n8n -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "  n8n IP: $N8N_SVC_IP"

echo "  --- /metrics ---"
kubectl exec -n observability $PROM_POD -c prometheus -- wget -qO- --timeout=3 http://$N8N_SVC_IP:5678/metrics 2>&1 | head -5
echo ""

echo "  --- /healthz ---"
kubectl exec -n observability $PROM_POD -c prometheus -- wget -qO- --timeout=3 http://$N8N_SVC_IP:5678/healthz 2>&1 | head -5
echo ""

echo "=== 3. ALERTMANAGER STATUS ==="
AM_SVC_IP=$(kubectl get svc kube-prometheus-stack-alertmanager -n observability -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "  alertmanager IP: $AM_SVC_IP"
kubectl exec -n observability $PROM_POD -c prometheus -- wget -qO- --timeout=3 http://$AM_SVC_IP:9093/api/v1/status 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
d = data.get('data', {})
print(f'  version: {d.get(\"versionInfo\",{}).get(\"version\")}')
print(f'  cluster.status: {d.get(\"cluster\",{}).get(\"status\")}')
print(f'  cluster.peers: {d.get(\"cluster\",{}).get(\"peers\")}')
" 2>&1
echo ""

echo "=== 4. KUBECOST - RESTART AFTER PROMETHEUS ENDPOINT FIX ==="
kubectl rollout restart deploy kubecost-cost-analyzer -n kubecost 2>&1
echo "  Restarted. Will need a few minutes to pick up data."
echo ""

echo "DONE"
