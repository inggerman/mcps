#!/bin/bash
cd /tmp/mcps-deploy
git config --global --add safe.directory /tmp/mcps-deploy

# Copy updated files from Windows mount
cp /mnt/c/Users/German/Documents/engineering/mcps/DEPLOYMENT.md . 2>/dev/null || true
cp /mnt/c/Users/German/Documents/engineering/mcps/setup-network.ps1 . 2>/dev/null || true
cp /mnt/c/Users/German/Documents/engineering/mcps/k8s/generate_manifests.py k8s/ 2>/dev/null || true
cp /mnt/c/Users/German/Documents/engineering/mcps/k8s/all-mcps.yaml k8s/ 2>/dev/null || true
cp /mnt/c/Users/German/Documents/engineering/mcps/.gitea/workflows/deploy-mcps.yml .gitea/workflows/ 2>/dev/null || true

git add -A
git commit -m "docs: add deployment documentation and network setup" 2>&1 || echo "Nothing to commit"

git remote remove origin 2>/dev/null || true
git remote add origin "http://ghl-admin:ChangeMe123!@10.0.0.79:3000/ghl-admin/mcps.git"
git push origin main 2>&1 | tail -5
echo "DONE"
