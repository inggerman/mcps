#!/bin/bash
cp /mnt/c/Users/German/DEPLOYMENT.md /tmp/mcps-deploy/
cd /tmp/mcps-deploy
git add -A
git commit -m "docs: deployment documentation"
git push origin main 2>&1 | tail -5
echo "DONE"
