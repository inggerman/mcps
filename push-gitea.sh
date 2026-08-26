#!/bin/bash
cd ~/boilerplate-infra-ghl 2>/dev/null || exit 1
git pull github main 2>&1
git push gitea main 2>&1
echo "DONE"
