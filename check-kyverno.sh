#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK KYVERNO POLICIES ==="
kubectl get cpol -A 2>&1 | grep -i "disallow\|require"
echo ""

echo "=== 2. CHECK disallow-privileged DETAILS ==="
kubectl get cpol disallow-privileged-containers -o yaml 2>&1 | grep -A10 "pattern\|anyPattern\|validate" | head -20
echo ""

echo "=== 3. CHECK disallow-root-user DETAILS ==="
kubectl get cpol disallow-root-user -o yaml 2>&1 | grep -A10 "pattern\|anyPattern\|validate" | head -20
echo ""

echo "=== 4. CHECK require-labels DETAILS ==="
kubectl get cpol require-pod-labels -o yaml 2>&1 | grep -A10 "pattern\|anyPattern\|validate" | head -20
echo ""

echo "=== 5. CHECK require-limits DETAILS ==="
kubectl get cpol require-resource-limits -o yaml 2>&1 | grep -A10 "pattern\|anyPattern\|validate" | head -20
echo ""

echo "=== 6. CHECK DEFAULT NAMESPACE EXCLUDES ==="
kubectl get cpol disallow-privileged-containers -o yaml 2>&1 | grep -A5 "exclude\|namespace" | head -15
echo ""

echo "DONE"
