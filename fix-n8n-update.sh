#!/bin/bash
set -e
export GIT_PAGER=cat PAGER=cat

cd /tmp
rm -rf platform
git clone http://ghl-admin:ChangeMe123!@gitea.mrrobot.fs/ghl/platform.git
cd platform
git config user.email "cascade@mrrobot.fs"
git config user.name "Cascade"

# 1. Update image in values.yaml
sed -i 's|docker.io/n8nio/n8n:1.95.2|docker.io/n8nio/n8n:2.32.3|' gitops/apps/n8n/values.yaml

# 2. Add N8N_SECURE_COOKIE=false after EXECUTIONS_MODE line in deployment.yaml
sed -i '/value: "regular"/a\            - name: N8N_SECURE_COOKIE\n              value: "false"' gitops/apps/n8n/templates/deployment.yaml

# Show diff
git --no-pager diff

# Commit and push
git add -A
git commit -m "fix: update n8n to 2.32.3 + disable secure cookie for HTTP"
git push origin main
