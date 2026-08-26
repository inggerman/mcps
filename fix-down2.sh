#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. HARBOR-CORE LOGS ==="
kubectl logs -n harbor harbor-core-587667b5d6-9pbjm --tail=20 2>&1
echo ""

echo "=== 2. SUSPEND CRONJOBS ==="
kubectl patch cronjob mongo-dump -n databases -p '{"spec":{"suspend":true}}' 2>&1
kubectl patch cronjob pg-dump -n databases -p '{"spec":{"suspend":true}}' 2>&1
kubectl patch cronjob rabbitmq-export -n rabbitmq -p '{"spec":{"suspend":true}}' 2>&1
echo ""

echo "=== 3. DELETE CRONJOB PODS ==="
kubectl delete pods -n databases --field-selector=status.phase!=Running --all --force --grace-period=0 2>&1
kubectl delete pods -n rabbitmq --field-selector=status.phase!=Running --all --force --grace-period=0 2>&1
echo ""

echo "=== 4. FORCE HARBOR STS RECREATE ==="
kubectl delete sts harbor-database -n harbor --cascade=orphan 2>&1
kubectl delete sts harbor-redis -n harbor --cascade=orphan 2>&1
echo ""

echo "=== 5. RESTART HARBOR DEPLOYMENTS ==="
kubectl rollout restart deploy -n harbor harbor-core harbor-jobservice 2>&1
echo ""

echo "=== 6. GITEA - CHECK KYVERNO EXCLUDES ==="
kubectl get cpol require-pod-labels -o jsonpath='{.spec.rules[0].exclude}' 2>&1 | python3 -c "import json,sys; d=json.load(sys.stdin); [print(c.get('resources',{}).get('namespaces',[])) for c in d.get('any',[])]" 2>/dev/null || echo "No excludes"
echo ""

echo "=== 7. PATCH GITEA DEPLOYMENT TO ADD LABELS ==="
kubectl patch deploy gitea -n gitea --type=json -p='[{"op":"add","path":"/spec/template/metadata/labels/app.kubernetes.io~1part-of","value":"platform"},{"op":"add","path":"/spec/template/metadata/labels/app.kubernetes.io~1name","value":"gitea"}]' 2>&1
echo ""

echo "=== 8. WAIT 30s ==="
sleep 30
echo ""

echo "=== 9. FINAL STATUS ==="
kubectl get pods -n gitea 2>&1
echo ""
kubectl get pods -n harbor 2>&1
echo ""
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "DONE"
