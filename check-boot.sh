#!/bin/bash

echo "=== 1. CHECK K3S SERVICE ==="
systemctl is-enabled k3s 2>&1
systemctl is-active k3s 2>&1
echo ""

echo "=== 2. CHECK WSL.CONF ==="
cat /etc/wsl.conf 2>/dev/null || echo "  No /etc/wsl.conf"
echo ""

echo "=== 3. CHECK BOOT SCRIPT ==="
ls -la /etc/profile.d/k3s* 2>/dev/null || echo "  No k3s profile.d script"
ls -la /etc/rc.local 2>/dev/null || echo "  No rc.local"
echo ""

echo "=== 4. CHECK SYSTEMD IN WSL ==="
ps -p 1 -o comm= 2>&1
echo ""

echo "=== 5. CHECK K3S.SERVICE FILE ==="
cat /etc/systemd/system/k3s.service 2>/dev/null | head -20
echo ""

echo "DONE"
