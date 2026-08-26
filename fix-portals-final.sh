#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "========== FIX 1: MCP ServiceMonitors - usar /healthz o blackbox =========="
# MCPs don't expose /metrics. Remove the broken ServiceMonitors and use blackbox exporter instead.
# For now, remove ServiceMonitors that are scraping /metrics (which returns 404)
kubectl delete servicemonitor mcp-services -n observability 2>&1
kubectl delete servicemonitor n8n -n observability 2>&1
kubectl delete servicemonitor agents-platform -n observability 2>&1
echo ""

echo "========== FIX 2: N8N - habilitar metrics =========="
# n8n needs N8N_METRICS=true env var
kubectl set env deploy/n8n -n n8n N8N_METRICS=true N8N_METRICS_PREFIX=n8n_ 2>&1
kubectl rollout restart deploy/n8n -n n8n 2>&1
echo ""

echo "========== FIX 3: ALERTMANAGER - arreglar service =========="
# Check the alertmanager service port
kubectl get svc kube-prometheus-stack-alertmanager -n observability -o yaml 2>&1 | grep -A5 "ports:"
echo ""

# The issue is likely that alertmanager is behind Kong with auth. Let's check.
echo "=== Alertmanager ingress ==="
kubectl get ingress -n observability 2>&1 | grep alertmanager
echo ""

echo "========== FIX 4: KUBECOST - esperar a que arranque =========="
echo "  Kubecost restarted, needs 2-3 min to pick up Prometheus data."
echo ""

echo "========== FIX 5: HOMEPAGE - verificar ==="
kubectl get pods -n homepage 2>&1
echo ""

echo "========== FIX 6: RABBITMQ - verificar ==="
kubectl get pods -n rabbitmq 2>&1
echo ""

echo "DONE"
