#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

HARBOR="harbor.mrrobot.fs"
HARBOR_USER="admin"
HARBOR_PASS="Harbor12345"

echo "=== 1. CHECK AVAILABLE BUILD TOOLS ==="
which crane 2>&1
which buildah 2>&1
which nerdctl 2>&1
which ctr 2>&1
which podman 2>&1
which docker 2>&1
echo ""

echo "=== 2. CHECK K3S CONTAINERD ==="
sudo k3s crictl version 2>&1 || k3s crictl version 2>&1
echo ""

echo "=== 3. CHECK IF WE CAN USE crane + tarball ==="
crane --help 2>&1 | head -3
echo ""

echo "=== 4. CHECK HARBOR REPOS FOR agents-platform ==="
curl -s -k "https://$HARBOR/api/v2.0/projects/ghl/repositories" -u "$HARBOR_USER:$HARBOR_PASS" 2>&1 | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for r in data:
        name = r.get('name','')
        print(f'  {name}')
except:
    print('  Could not parse response')
" 2>&1
echo ""

echo "DONE"
