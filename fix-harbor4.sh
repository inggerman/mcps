#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. PATCH STS YAML TO ADD RESOURCE LIMITS ==="
python3 << 'PYEOF'
import yaml

for name in ["harbor-database", "harbor-redis"]:
    with open(f"/tmp/{name}.yaml") as f:
        doc = yaml.safe_load(f)
    
    # Add namespace
    doc["metadata"]["namespace"] = "harbor"
    
    # Add resource limits to containers
    for c in doc["spec"]["template"]["spec"]["containers"]:
        if "resources" not in c:
            c["resources"] = {}
        if "limits" not in c["resources"]:
            c["resources"]["limits"] = {"cpu": "500m", "memory": "512Mi"}
        if "requests" not in c["resources"]:
            c["resources"]["requests"] = {"cpu": "50m", "memory": "64Mi"}
    
    # Add labels for kyverno
    labels = doc["spec"]["template"]["metadata"].setdefault("labels", {})
    labels.setdefault("app.kubernetes.io/name", name)
    labels.setdefault("app.kubernetes.io/part-of", "harbor")
    
    with open(f"/tmp/{name}-fixed.yaml", "w") as out:
        yaml.dump(doc, out, default_flow_style=False, sort_keys=False)
    print(f"  Fixed: {name}")

PYEOF
echo ""

echo "=== 2. APPLY FIXED STS ==="
kubectl apply -f /tmp/harbor-database-fixed.yaml 2>&1
kubectl apply -f /tmp/harbor-redis-fixed.yaml 2>&1
echo ""

echo "=== 3. WAIT 45s ==="
sleep 45
echo ""

echo "=== 4. HARBOR STATUS ==="
kubectl get pods -n harbor 2>&1
echo ""

echo "=== 5. RESTART HARBOR CORE+JOBSERVICE ==="
kubectl rollout restart deploy -n harbor harbor-core harbor-jobservice 2>&1
sleep 20
echo ""

echo "=== 6. FINAL STATUS ==="
kubectl get pods -n harbor 2>&1
echo ""
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "DONE"
