#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== API LOGS ==="
kubectl logs -n agents-platform agents-platform-api-6495b69d86-lsq9x --tail=20 2>&1
echo ""

echo "=== WORKER LOGS ==="
kubectl logs -n agents-platform agents-platform-worker-bbd8b4f57-fpwhj --tail=20 2>&1
echo ""

echo "=== DAEMON LOGS (running) ==="
kubectl logs -n agents-platform agents-platform-daemon-f9d979b75-cnzjh --tail=10 2>&1
echo ""

echo "DONE"
