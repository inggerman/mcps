#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "========== 1. HOMEPAGE =========="
kubectl get deploy -n homepage 2>&1
kubectl get pods -n homepage 2>&1
kubectl get ingress -n homepage 2>&1
kubectl get svc -n homepage 2>&1
echo ""

echo "========== 2. PROMETHEUS TARGETS =========="
kubectl get pods -n observability 2>&1
kubectl get servicemonitors -A 2>&1 | head -20
echo ""

echo "========== 3. ALERTMANAGER =========="
kubectl get deploy alertmanager -n observability -o yaml 2>&1 | grep -A5 "args:\|command:" | head -15
kubectl get amd -A 2>&1 2>/dev/null || echo "No AlertmanagerConfig CRD"
kubectl get secret alertmanager-alertmanager -n observability 2>&1
echo ""

echo "========== 4. LOKI =========="
kubectl get deploy -n observability 2>&1 | grep loki
kubectl get pods -n observability 2>&1 | grep loki
kubectl get svc -n observability 2>&1 | grep loki
echo ""

echo "========== 5. TEMPO =========="
kubectl get deploy -n observability 2>&1 | grep tempo
kubectl get pods -n observability 2>&1 | grep tempo
kubectl get svc -n observability 2>&1 | grep tempo
kubectl get ingress -n observability 2>&1 | grep tempo
echo ""

echo "========== 6. RABBITMQ =========="
kubectl get pods -n rabbitmq 2>&1
kubectl get svc -n rabbitmq 2>&1
kubectl get ingress -n rabbitmq 2>&1
echo ""

echo "========== 7. KUBECOST =========="
kubectl get pods -n kubecost 2>&1
kubectl get svc -n kubecost 2>&1
echo ""

echo "========== 8. SERVICE MONITORS FOR MCP/N8N/AGENTS =========="
kubectl get servicemonitor -A 2>&1
kubectl get podmonitor -A 2>&1
echo ""

echo "========== 9. PROMETHEUS CONFIG =========="
kubectl get prometheus -A 2>&1
kubectl get secret prometheus-prometheus -n observability -o jsonpath='{.data.prometheus\.yaml}' 2>&1 | base64 -d 2>/dev/null | head -50
echo ""

echo "DONE"
