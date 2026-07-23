#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. DESCRIBE A PENDING POD ==="
NEW_POD=$(k3s kubectl get pods -n mcps --sort-by=.metadata.creationTimestamp 2>/dev/null | grep "Pending" | tail -1 | awk '{print $1}')
echo "Pod: $NEW_POD"
k3s kubectl describe pod $NEW_POD -n mcps 2>&1 | tail -30
echo ""

echo "=== 2. CHECK EVENTS ==="
k3s kubectl get events -n mcps --sort-by=.lastTimestamp 2>&1 | grep -i "error\|denied\|fail\|reject\|warn" | tail -20
echo ""

echo "=== 3. DELETE ALL DEPLOYMENTS AND RECREATE CLEAN ==="
k3s kubectl delete deploy -n mcps --all 2>&1
sleep 10
echo ""

echo "=== 4. RE-APPLY ==="
cp /mnt/c/Users/German/all-mcps.yaml /tmp/all-mcps.yaml
k3s kubectl apply -f /tmp/all-mcps.yaml 2>&1 | grep "deployment" | head -10
echo ""

echo "=== 5. WAIT 60s ==="
sleep 60
echo ""

echo "=== 6. POD STATUS ==="
k3s kubectl get pods -n mcps 2>&1
echo ""

RUNNING=$(k3s kubectl get pods -n mcps --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
TOTAL=$(k3s kubectl get pods -n mcps --no-headers 2>/dev/null | wc -l)
echo "  Running: ${RUNNING}/${TOTAL}"
echo ""

echo "DONE"
