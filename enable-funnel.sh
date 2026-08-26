#!/bin/bash
# Try new funnel syntax
echo "===FUNNEL HELP==="
echo 12345 | sudo -S tailscale funnel --help 2>&1 | head -20
echo "===TRY FUNNEL==="
echo 12345 | sudo -S tailscale funnel 443 on 2>&1
echo "===TRY FUNNEL2==="
echo 12345 | sudo -S tailscale funnel --bg --https=443 http://localhost:80 2>&1
echo "===STATUS==="
echo 12345 | sudo -S tailscale funnel status 2>&1
