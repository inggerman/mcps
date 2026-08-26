@echo off
:: Agregar entradas DNS para MCP servers - ejecutar como Admin
set IP=100.68.63.120
set HOSTS=C:\Windows\System32\drivers\etc\hosts

echo. >> %HOSTS%
echo # MCP Servers - infra nuevos + documentation + smart-home >> %HOSTS%

for %%e in (mcp-argocd mcp-harbor mcp-gitea mcp-n8n mcp-vault-secrets mcp-postgres mcp-redis mcp-rabbitmq mcp-vector-search mcp-notify mcp-cluster-doctor mcp-image-builder mcp-log-explorer mcp-config-sync mcp-health-monitor mcp-network-doctor mcp-storage-doctor mcp-deploy-tracker mcp-node-ops mcp-documentation mcp-smart-home) do (
    echo %IP% %%e.mrrobot.fs >> %HOSTS%
    echo Added: %%e.mrrobot.fs
)

echo.
echo Done - 21 entries added
pause
