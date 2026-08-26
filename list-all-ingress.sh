#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== ALL INGRESSES ==="
kubectl get ingress -A -o jsonpath='{range .items[*]}{.spec.rules[0].host}{"\n"}{end}' 2>&1 | sort -u
echo ""

echo "=== ALL INGRESSES WITH NS ==="
kubectl get ingress -A 2>&1
echo ""

echo "=== ALL SVC WITH LOADBALANCER/NODEPORT ==="
kubectl get svc -A -o wide 2>&1 | grep -i "LoadBalancer\|NodePort" | grep -v kubernetes
echo ""

echo "DONE"
