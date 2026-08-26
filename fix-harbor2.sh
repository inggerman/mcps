#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. GET FULL HARBOR MANIFEST ==="
helm get manifest harbor -n harbor 2>&1 > /tmp/harbor-full.yaml
echo "  Lines: $(wc -l < /tmp/harbor-full.yaml)"
echo ""

echo "=== 2. SPLIT AND APPLY STS ==="
python3 << 'PYEOF'
import yaml

with open("/tmp/harbor-full.yaml") as f:
    docs = list(yaml.safe_load_all(f))

for doc in docs:
    if doc and doc.get("kind") == "StatefulSet":
        name = doc["metadata"]["name"]
        with open(f"/tmp/{name}.yaml", "w") as out:
            yaml.dump(doc, out, default_flow_style=False, sort_keys=False)
        print(f"  Saved: {name}")
PYEOF
echo ""

echo "=== 3. APPLY STS ==="
for f in /tmp/harbor-database.yaml /tmp/harbor-redis.yaml /tmp/harbor-trivy.yaml; do
  if [ -f "$f" ]; then
    echo "  Applying $(basename $f)..."
    kubectl apply -f "$f" 2>&1
  fi
done
echo ""

echo "=== 4. WAIT 45s ==="
sleep 45
echo ""

echo "=== 5. HARBOR STATUS ==="
kubectl get pods -n harbor 2>&1
echo ""

echo "=== 6. RESTART HARBOR CORE+JOBSERVICE ==="
kubectl rollout restart deploy -n harbor harbor-core harbor-jobservice 2>&1
sleep 20
echo ""

echo "=== 7. FINAL ALL STATUS ==="
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "=== 8. GITEA CHECK ==="
kubectl get pods -n gitea 2>&1
echo ""

echo "DONE"
