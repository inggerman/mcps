#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. REMOVE KONG KEY-AUTH FROM ALERTMANAGER INGRESS ==="
kubectl annotate ingress alertmanager-kong -n observability konghq.com/plugins- 2>&1
echo ""

echo "=== 2. REMOVE KONG KEY-AUTH FROM OTHER OBSERVABILITY INGRESSES ==="
for ING in grafana-kong prometheus-kong loki-kong tempo-kong; do
  echo -n "  Removing auth from $ING... "
  kubectl annotate ingress $ING -n observability konghq.com/plugins- 2>&1
done
echo ""

echo "=== 3. N8N - CHECK SERVICE PORT NAME ==="
kubectl get svc n8n -n n8n -o yaml 2>&1 | grep -A10 "ports:"
echo ""

echo "=== 4. N8N - CHECK ENV ==="
kubectl get deploy n8n -n n8n -o yaml 2>&1 | grep -i "N8N_METRICS\|N8N_PORT\|port" | head -10
echo ""

echo "=== 5. KUBECOST - CHECK COST-ANALYZER ==="
kubectl get pods -n kubecost 2>&1
kubectl get deploy kubecost-cost-analyzer -n kubecost 2>&1
echo ""

echo "=== 6. REMOVE KONG KEY-AUTH FROM RABBITMQ INGRESS ==="
kubectl annotate ingress rabbitmq-kong -n rabbitmq konghq.com/plugins- 2>&1
echo ""

echo "=== 7. REMOVE KONG KEY-AUTH FROM KUBECOST INGRESS ==="
kubectl get ingress -n kubecost 2>&1
kubectl annotate ingress -n kubecost konghq.com/plugins- --all 2>&1
echo ""

echo "DONE"
