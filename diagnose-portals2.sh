#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "========== 1. HOMEPAGE DETAILS =========="
kubectl get deploy -n homepage -o yaml 2>&1 | grep -A10 "containers:" | head -15
kubectl get ingress -n homepage -o yaml 2>&1 | grep -A5 "rules:"
kubectl logs -n homepage deploy/homepage --tail=10 2>&1
echo ""

echo "========== 2. ALERTMANAGER DETAILS =========="
kubectl get pods -n observability | grep alertmanager
kubectl get alertmanager -A 2>&1
kubectl get secret -n observability | grep alertmanager
kubectl get deploy -n observability | grep alertmanager
echo ""

echo "========== 3. LOKI INGRESS =========="
kubectl get ingress -n observability 2>&1 | grep loki
kubectl get ingress loki-kong -n observability -o yaml 2>&1 | grep -A10 "rules:"
echo ""

echo "========== 4. TEMPO INGRESS =========="
kubectl get ingress tempo-kong -n observability -o yaml 2>&1 | grep -A10 "rules:"
echo ""

echo "========== 5. RABBITMQ =========="
kubectl get statefulset -n rabbitmq 2>&1
kubectl get pods -n rabbitmq 2>&1
kubectl get all -n rabbitmq 2>&1
echo ""

echo "========== 6. KUBECOST PROMETHEUS =========="
kubectl get deploy kubecost-cost-analyzer -n kubecost -o yaml 2>&1 | grep -i "prometheus\|PROMETHEUS" | head -10
echo ""

echo "========== 7. HOMEPAGE CONFIGMAP =========="
kubectl get cm -n homepage 2>&1
kubectl get cm homepage -n homepage -o yaml 2>&1 | head -40
echo ""

echo "DONE"
