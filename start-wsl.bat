@echo off
:: Auto-start WSL on Windows boot
:: This ensures K3s and all cluster services are running when Windows starts

echo Starting WSL...
wsl.exe -d Debian -- echo "WSL started successfully"
echo Done.
