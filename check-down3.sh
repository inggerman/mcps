#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== K3S STATUS ==="
systemctl is-active k3s 2>&1
echo ""

echo "=== UNKNOWN PODS ==="
kubectl get pods -A --field-selector=status.phase=Unknown 2>&1
echo ""

echo "=== NOT RUNNING ==="
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "=== GITEA PODS ==="
kubectl get pods -n gitea 2>&1
echo ""

echo "=== HARBOR PODS ==="
kubectl get pods -n harbor 2>&1
echo ""

echo "=== POSTGRESQL ==="
kubectl get pods -n databases postgresql-0 2>&1
echo ""

echo "=== UPTIME ==="
uptime 2>&1
echo ""

echo "=== K3S UPTIME ==="
systemctl show k3s --property=ActiveEnterTimestamp 2>&1
echo ""

echo "DONE"
