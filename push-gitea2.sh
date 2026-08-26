#!/bin/bash
git clone https://github.com/inggerman/boilerplate-infra-ghl.git ~/boilerplate-infra-ghl 2>&1
cd ~/boilerplate-infra-ghl
git remote add gitea "http://ghl-admin:ChangeMe123!@gitea.mrrobot.fs/ghl-admin/boilerplate-infra-ghl.git" 2>/dev/null || true
git push gitea main 2>&1
echo "DONE"
