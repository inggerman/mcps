#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "========== FIX 1: HOMEPAGE - cambiar HTTPS a HTTP =========="
# The homepage siteMonitor uses https:// but all services are HTTP-only
# This causes the page to hang waiting for timeouts
kubectl get cm homepage-config -n homepage -o json | python3 -c "
import json, sys
cm = json.load(sys.stdin)
for key in cm['data']:
    cm['data'][key] = cm['data'][key].replace('https://', 'http://')
print(json.dumps(cm))
" > /tmp/homepage-cm.json 2>&1
kubectl apply -f /tmp/homepage-cm.json 2>&1
kubectl rollout restart deploy homepage -n homepage 2>&1
echo ""

echo "========== FIX 2: RABBITMQ - agregar a Kyverno excludes =========="
for POLICY in require-pod-labels disallow-root-user require-resource-limits disallow-privileged-containers restrict-image-registries; do
  echo -n "  Patching $POLICY... "
  kubectl get cpol $POLICY -o json 2>/dev/null | python3 -c "
import json, sys
p = json.load(sys.stdin)
for rule in p['spec']['rules']:
    exc = rule.get('exclude', {})
    for cond in exc.get('any', []):
        res = cond.get('resources', {})
        if 'namespaces' in res:
            if 'rabbitmq' not in res['namespaces']:
                res['namespaces'].append('rabbitmq')
print(json.dumps(p))
" 2>/dev/null > /tmp/patched.json
  if [ -s /tmp/patched.json ]; then
    kubectl apply -f /tmp/patched.json 2>&1 | head -1
  else
    echo "FAILED"
  fi
done
echo ""

echo "========== FIX 3: KUBECOST - arreglar Prometheus endpoint =========="
KUBECOST_CM=$(kubectl get cm -n kubecost -o name 2>/dev/null | grep -i prometheus | head -1)
echo "  Found: $KUBECOST_CM"
# Check current value
kubectl get deploy kubecost-cost-analyzer -n kubecost -o yaml 2>&1 | grep -A5 "PROMETHEUS_SERVER_ENDPOINT" | head -8
echo ""

# Patch kubecost to use internal prometheus
kubectl set env deploy/kubecost-cost-analyzer -n kubecost PROMETHEUS_SERVER_ENDPOINT=http://prometheus-kube-prometheus-stack-prometheus.observability.svc.cluster.local:9090 2>&1
echo ""

echo "========== FIX 4: SERVICE MONITORS para MCP, n8n, agents-platform =========="
# Create ServiceMonitor for MCPs
cat <<'EOF' | kubectl apply -f - 2>&1
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: mcp-services
  namespace: observability
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchExpressions:
      - key: app.kubernetes.io/part-of
        operator: In
        values: [mcp-services]
  namespaceSelector:
    matchNames: [mcps]
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
EOF
echo ""

# Create ServiceMonitor for n8n
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

# Create ServiceMonitor for agents-platform
cat <<'EOF' | kubectl apply -f - 2>&1
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: agents-platform
  namespace: observability
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchExpressions:
      - key: app.kubernetes.io/part-of
        operator: In
        values: [agents-platform]
  namespaceSelector:
    matchNames: [agents-platform]
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
EOF
echo ""

echo "========== FIX 5: ALERTMANAGER - agregar config basica =========="
# Alertmanager "disabled" is because cluster mode isn't configured properly
# Patch the alertmanager to enable cluster mode
kubectl patch alertmanager kube-prometheus-stack-alertmanager -n observability --type=merge -p '{"spec":{"cluster":{"enableClusterAPI":true}}}' 2>&1 || echo "  (already configured or CRD doesn't support this field)"
echo ""

echo "========== FIX 6: LOKI/TEMPO - son backends, no UI =========="
echo "  Loki and Tempo are backend services, not UIs."
echo "  They are queried through Grafana data sources."
echo "  Loki ingress returns 'ok' (health check) - this is correct."
echo "  Tempo ingress returns 404 at / - this is correct (no UI)."
echo "  To use them: go to Grafana -> Explore -> select Loki or Tempo data source."
echo ""

echo "========== VERIFY =========="
sleep 10
echo "--- Homepage ---"
kubectl get pods -n homepage 2>&1
echo ""
echo "--- RabbitMQ ---"
kubectl rollout restart statefulset rabbitmq -n rabbitmq 2>&1
sleep 10
kubectl get pods -n rabbitmq 2>&1
echo ""
echo "--- ServiceMonitors ---"
kubectl get servicemonitor -n observability 2>&1
echo ""
echo "--- Kubecost ---"
kubectl get pods -n kubecost 2>&1 | head -3
echo ""

echo "DONE"
