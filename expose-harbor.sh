#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. Create NodePort for Harbor registry ==="
cat <<EOF | k3s kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: harbor-registry-nodeport
  namespace: harbor
spec:
  type: NodePort
  selector:
    app: harbor
    component: registry
    release: harbor
  ports:
  - port: 5000
    targetPort: 5000
    nodePort: 30500
    name: registry
EOF
echo ""

echo "=== 2. Verify NodePort ==="
k3s kubectl get svc -n harbor harbor-registry-nodeport 2>&1
echo ""

echo "=== 3. Get server IP ==="
hostname -I | awk '{print $1}'
echo ""

echo "=== 4. Test connectivity ==="
curl -s -o /dev/null -w '%{http_code}' http://localhost:30500/v2/ 2>&1
echo " (localhost:30500)"
echo ""

echo "DONE"
