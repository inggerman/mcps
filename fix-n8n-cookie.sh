#!/bin/bash
# Reset and use a different port for funnel to avoid Kong 443 conflict
echo 12345 | sudo -S tailscale funnel reset 2>&1
echo 12345 | sudo -S tailscale serve reset 2>&1
# Use port 8443 for funnel
echo 12345 | sudo -S tailscale funnel --bg --https=8443 "http://10.43.197.130:80" 2>&1
echo "===STATUS==="
echo 12345 | sudo -S tailscale funnel status 2>&1
echo "===TEST==="
sleep 3
curl -s -X POST "https://k3s-worker.tail901264.ts.net:8443/webhook/validar-estatus" -d "command=/validar-estatus" 2>&1
echo "EXIT: $?"
