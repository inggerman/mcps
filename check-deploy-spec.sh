#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== Worker deployment spec ==="
kubectl get deployment agents-platform-worker -n agents-platform -o jsonpath='{.spec.template.spec.containers[0].image}' 2>&1
echo ""
kubectl get deployment agents-platform-worker -n agents-platform -o jsonpath='{.spec.template.spec.containers[0].env}' 2>&1 | python3 -m json.tool 2>&1
echo ""

echo "=== Daemon deployment spec ==="
kubectl get deployment agents-platform-daemon -n agents-platform -o jsonpath='{.spec.template.spec.containers[0].image}' 2>&1
echo ""
kubectl get deployment agents-platform-daemon -n agents-platform -o jsonpath='{.spec.template.spec.containers[0].env}' 2>&1 | python3 -m json.tool 2>&1
echo ""

echo "=== API deployment spec ==="
kubectl get deployment agents-platform-api -n agents-platform -o jsonpath='{.spec.template.spec.containers[0].image}' 2>&1
echo ""

echo "DONE"
