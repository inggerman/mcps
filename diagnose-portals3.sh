#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "========== 1. HOMEPAGE CONFIG =========="
kubectl get cm homepage-config -n homepage -o yaml 2>&1
echo ""

echo "========== 2. ALERTMANAGER CONFIG SECRET =========="
kubectl get secret alertmanager-kube-prometheus-stack-alertmanager -n observability -o jsonpath='{.data.alertmanager\.yaml}' 2>&1 | base64 -d 2>/dev/null
echo ""

echo "========== 3. RABBITMQ STATEFULSET =========="
kubectl get statefulset rabbitmq -n rabbitmq -o yaml 2>&1 | grep -A20 "spec:" | head -30
echo ""

echo "========== 4. RABBITMQ EVENTS =========="
kubectl get events -n rabbitmq --sort-by=.lastTimestamp 2>&1 | tail -10
echo ""

echo "========== 5. KUBECOST PROMETHEUS ENDPOINT =========="
kubectl get secret -n kubecost | grep prometheus
kubectl get deploy kubecost-cost-analyzer -n kubecost -o yaml 2>&1 | grep -B2 -A2 "PROMETHEUS_SERVER_ENDPOINT" | head -10
echo ""

echo "========== 6. LOKI GATEWAY - WHAT IT RETURNS =========="
kubectl exec -n observability deploy/loki-gateway -- wget -qO- http://localhost:80/ 2>&1 | head -5
echo ""

echo "========== 7. TEMPO - WHAT IT RETURNS =========="
kubectl exec -n observability tempo-0 -- wget -qO- http://localhost:3100/ 2>&1 | head -5
echo ""

echo "========== 8. HOMEPAGE SERVICE =========="
kubectl get svc -n homepage 2>&1
echo ""

echo "DONE"
