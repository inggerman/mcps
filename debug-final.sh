#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. Check new worker pod env ==="
kubectl get pod -n agents-platform agents-platform-worker-75cf5db4df-gd7sv -o yaml 2>&1 | grep -A2 "image:"
echo ""

echo "=== 2. Check daemon new pod ==="
kubectl get pod -n agents-platform agents-platform-daemon-7766f6658d-ggc8d -o yaml 2>&1 | grep -A2 "image:"
echo ""

echo "=== 3. Events for worker ==="
kubectl describe pod -n agents-platform agents-platform-worker-75cf5db4df-gd7sv 2>&1 | tail -15
echo ""

echo "=== 4. Test RabbitMQ from inside rabbitmq pod ==="
kubectl exec -n rabbitmq rabbitmq-0 -- rabbitmqctl authenticate_user user RabbitLocal123! 2>&1
echo ""

echo "=== 5. Delete old stuck pods ==="
kubectl delete pod -n agents-platform agents-platform-worker-5cc44b648d-drrt7 --force 2>&1
kubectl delete pod -n agents-platform agents-platform-worker-5cc44b648d-fpnxl --force 2>&1
kubectl delete pod -n agents-platform agents-platform-daemon-78cdd649b4-cnxds --force 2>&1
echo ""

echo "=== 6. Wait 30s ==="
sleep 30
echo ""

echo "=== 7. Check pods ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== 8. Worker logs ==="
for pod in $(kubectl get pods -n agents-platform -l app.kubernetes.io/name=agents-platform-worker -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
  echo "--- $pod ---"
  kubectl logs -n agents-platform $pod --tail=15 2>&1
  echo ""
done

echo "=== 9. Daemon logs ==="
for pod in $(kubectl get pods -n agents-platform -l app.kubernetes.io/name=agents-platform-daemon -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
  echo "--- $pod ---"
  kubectl logs -n agents-platform $pod --tail=10 2>&1
  echo ""
done

echo "DONE"
