#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. GET HARBOR STS FROM HELM MANIFEST ==="
helm get manifest harbor -n harbor 2>&1 | grep -A 50 "kind: StatefulSet" | head -120 > /tmp/harbor-sts.yaml
echo "  Saved to /tmp/harbor-sts.yaml"
echo ""

echo "=== 2. EXTRACT REDIS AND DATABASE STS ==="
python3 -c "
import yaml, sys

with open('/tmp/harbor-sts.yaml') as f:
    docs = list(yaml.safe_load_all(f))

for doc in docs:
    if doc and doc.get('kind') == 'StatefulSet':
        name = doc['metadata']['name']
        print(f'  Found STS: {name}')
        with open(f'/tmp/{name}-sts.yaml', 'w') as out:
            yaml.dump(doc, out, default_flow_style=False)
" 2>&1
echo ""

echo "=== 3. APPLY STS ==="
for f in /tmp/harbor-redis-sts.yaml /tmp/harbor-database-sts.yaml; do
  if [ -f "$f" ]; then
    echo "  Applying $(basename $f)..."
    kubectl apply -f "$f" 2>&1
  else
    echo "  $(basename $f) not found"
  fi
done
echo ""

echo "=== 4. ALSO EXTRACT AND APPLY SERVICES ==="
helm get manifest harbor -n harbor 2>&1 | python3 -c "
import yaml, sys

docs = list(yaml.safe_load_all(sys.stdin))
for doc in docs:
    if doc and doc.get('kind') == 'Service':
        name = doc['metadata']['name']
        ns = doc['metadata'].get('namespace', 'harbor')
        if 'redis' in name or 'database' in name:
            print(f'  Found Service: {name}')
            with open(f'/tmp/{name}-svc.yaml', 'w') as out:
                yaml.dump(doc, out, default_flow_style=False)
" 2>&1
for f in /tmp/harbor-redis-svc.yaml /tmp/harbor-database-svc.yaml /tmp/harbor-redis-headless-svc.yaml /tmp/harbor-database-headless-svc.yaml; do
  if [ -f "$f" ]; then
    echo "  Applying $(basename $f)..."
    kubectl apply -f "$f" 2>&1
  fi
done
echo ""

echo "=== 5. WAIT 30s ==="
sleep 30
echo ""

echo "=== 6. HARBOR STATUS ==="
kubectl get pods -n harbor 2>&1
echo ""

echo "=== 7. NOT RUNNING ==="
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "DONE"
