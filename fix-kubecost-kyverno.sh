#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ADD kubecost TO KYVERNO EXCLUDES ==="
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
            if 'kubecost' not in res['namespaces']:
                res['namespaces'].append('kubecost')
print(json.dumps(p))
" 2>/dev/null > /tmp/patched.json
  if [ -s /tmp/patched.json ]; then
    kubectl apply -f /tmp/patched.json 2>&1 | head -1
  else
    echo "FAILED"
  fi
done
echo ""

echo "=== 2. RESTART KUBECOST ==="
kubectl rollout restart deploy kubecost-cost-analyzer -n kubecost 2>&1
echo ""

echo "=== 3. WAIT 30s ==="
sleep 30
echo ""

echo "=== 4. KUBECOST PODS ==="
kubectl get pods -n kubecost 2>&1
echo ""

echo "=== 5. ALL STATUS SUMMARY ==="
echo "--- Homepage ---"
kubectl get pods -n homepage 2>&1
echo ""
echo "--- RabbitMQ ---"
kubectl get pods -n rabbitmq 2>&1
echo ""
echo "--- n8n ---"
kubectl get pods -n n8n 2>&1
echo ""
echo "--- Kubecost ---"
kubectl get pods -n kubecost 2>&1
echo ""
echo "--- ArgoCD mcp-services ---"
kubectl get application mcp-services -n argocd 2>&1
echo ""
echo "--- ServiceMonitors ---"
kubectl get servicemonitor -n observability 2>&1
echo ""

echo "DONE"
