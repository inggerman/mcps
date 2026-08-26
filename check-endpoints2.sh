#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. TEST MCP FROM INSIDE CLUSTER (using curl from argocd pod) ==="
MCP_SVC_IP=$(kubectl get svc mcp-calendar -n mcps -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "  mcp-calendar ClusterIP: $MCP_SVC_IP"

ARGOCD_POD=$(kubectl get pod -n argocd -l app.kubernetes.io/component=server -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

echo "  --- Root / ---"
kubectl exec -n argocd $ARGOCD_POD -- curl -s http://$MCP_SVC_IP/ 2>&1 | head -5
echo ""

echo "  --- /metrics ---"
kubectl exec -n argocd $ARGOCD_POD -- curl -s http://$MCP_SVC_IP/metrics 2>&1 | head -5
echo ""

echo "  --- /health ---"
kubectl exec -n argocd $ARGOCD_POD -- curl -s http://$MCP_SVC_IP/health 2>&1 | head -5
echo ""

echo "=== 2. N8N - CHECK IF METRICS ENABLED ==="
N8N_SVC_IP=$(kubectl get svc n8n -n n8n -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "  n8n ClusterIP: $N8N_SVC_IP"

echo "  --- /metrics ---"
kubectl exec -n argocd $ARGOCD_POD -- curl -s http://$N8N_SVC_IP:5678/metrics 2>&1 | head -5
echo ""

echo "  --- /healthz ---"
kubectl exec -n argocd $ARGOCD_POD -- curl -s http://$N8N_SVC_IP:5678/healthz 2>&1 | head -5
echo ""

echo "=== 3. N8N ENV - CHECK METRICS SETTINGS ==="
kubectl get deploy n8n -n n8n -o yaml 2>&1 | grep -i "metric\|PROMETHEUS" | head -5
echo ""

echo "=== 4. KUBECOST - CHECK ENV ==="
kubectl get deploy kubecost-cost-analyzer -n kubecost -o yaml 2>&1 | grep -A3 "PROMETHEUS_SERVER" | head -10
echo ""

echo "=== 5. ALERTMANAGER - CHECK FROM INSIDE ==="
AM_SVC_IP=$(kubectl get svc kube-prometheus-stack-alertmanager -n observability -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "  alertmanager ClusterIP: $AM_SVC_IP"
kubectl exec -n argocd $ARGOCD_POD -- curl -s http://$AM_SVC_IP:9093/api/v1/status 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
d = data.get('data', {})
print(f'  version: {d.get(\"versionInfo\",{}).get(\"version\")}')
print(f'  cluster.status: {d.get(\"cluster\",{}).get(\"status\")}')
print(f'  cluster.peers: {d.get(\"cluster\",{}).get(\"peers\")}')
" 2>&1
echo ""

echo "DONE"
