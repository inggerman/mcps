#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. WAIT 30s ==="
sleep 30
echo ""

echo "=== 2. RABBITMQ ==="
kubectl get pods -n rabbitmq 2>&1
echo ""

echo "=== 3. HOMEPAGE ==="
kubectl get pods -n homepage 2>&1
echo ""

echo "=== 4. KUBECOST PODS ==="
kubectl get pods -n kubecost 2>&1
echo ""

echo "=== 5. PROMETHEUS TARGETS (MCP/n8n/agents) ==="
kubectl exec -n observability prometheus-kube-prometheus-stack-prometheus-0 -c prometheus -- wget -qO- "http://localhost:9090/api/v1/targets" 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
targets = data.get('data', {}).get('activeTargets', [])
for t in targets:
    labels = t.get('labels', {})
    job = labels.get('job', '')
    if 'mcp' in job.lower() or 'n8n' in job.lower() or 'agent' in job.lower():
        print(f'  {job}: {t.get(\"health\")} - {labels.get(\"instance\",\"\")}')
" 2>&1
echo ""

echo "=== 6. ALL PROMETHEUS TARGETS COUNT ==="
kubectl exec -n observability prometheus-kube-prometheus-stack-prometheus-0 -c prometheus -- wget -qO- "http://localhost:9090/api/v1/targets" 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
targets = data.get('data', {}).get('activeTargets', [])
up = sum(1 for t in targets if t.get('health') == 'up')
down = sum(1 for t in targets if t.get('health') == 'down')
print(f'  Total: {len(targets)}  Up: {up}  Down: {down}')
for t in targets:
    if t.get('health') == 'down':
        job = t.get('labels', {}).get('job', '')
        print(f'  DOWN: {job} - {t.get(\"scrapeError\",\"\")}')
" 2>&1
echo ""

echo "DONE"
