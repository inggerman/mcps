#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. TEST MCP ENDPOINTS ==="
# Test what endpoints an MCP pod exposes
MCP_POD=$(kubectl get pod -n mcps -l app.kubernetes.io/name=mcp-calendar -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
echo "  Pod: $MCP_POD"

echo "  --- Root / ---"
kubectl exec -n mcps $MCP_POD -- wget -qO- http://localhost:8000/ 2>&1 | head -3
echo ""

echo "  --- /metrics ---"
kubectl exec -n mcps $MCP_POD -- wget -qO- http://localhost:8000/metrics 2>&1 | head -3
echo ""

echo "  --- /health ---"
kubectl exec -n mcps $MCP_POD -- wget -qO- http://localhost:8000/health 2>&1 | head -3
echo ""

echo "  --- /ready ---"
kubectl exec -n mcps $MCP_POD -- wget -qO- http://localhost:8000/ready 2>&1 | head -3
echo ""

echo "=== 2. TEST N8N ENDPOINTS ==="
N8N_POD=$(kubectl get pod -n n8n -l app.kubernetes.io/name=n8n -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
echo "  Pod: $N8N_POD"

echo "  --- /metrics ---"
kubectl exec -n n8n $N8N_POD -- wget -qO- http://localhost:5678/metrics 2>&1 | head -5
echo ""

echo "  --- /healthz ---"
kubectl exec -n n8n $N8N_POD -- wget -qO- http://localhost:5678/healthz 2>&1 | head -3
echo ""

echo "=== 3. KUBECOST - CHECK PROMETHEUS CONNECTION ==="
kubectl logs -n kubecost deploy/kubecost-cost-analyzer -c cost-analyzer --tail=10 2>&1 | grep -i "prometheus\|error\|connect" | head -5
echo ""

echo "=== 4. ALERTMANAGER STATUS ==="
kubectl exec -n observability alertmanager-kube-prometheus-stack-alertmanager-0 -c alertmanager -- wget -qO- http://localhost:9093/api/v1/status 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  cluster: {data.get(\"data\",{}).get(\"cluster\",{})}')
" 2>&1
echo ""

echo "DONE"
