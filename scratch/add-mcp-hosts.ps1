# Agregar entradas DNS faltantes para MCP servers en hosts file
# Ejecutar como Administrador

$hostsPath = "C:\Windows\System32\drivers\etc\hosts"
$ip = "100.68.63.120"
$newEntries = @(
    "mcp-argocd.mrrobot.fs",
    "mcp-harbor.mrrobot.fs",
    "mcp-gitea.mrrobot.fs",
    "mcp-n8n.mrrobot.fs",
    "mcp-vault-secrets.mrrobot.fs",
    "mcp-postgres.mrrobot.fs",
    "mcp-redis.mrrobot.fs",
    "mcp-rabbitmq.mrrobot.fs",
    "mcp-vector-search.mrrobot.fs",
    "mcp-notify.mrrobot.fs",
    "mcp-cluster-doctor.mrrobot.fs",
    "mcp-image-builder.mrrobot.fs",
    "mcp-log-explorer.mrrobot.fs",
    "mcp-config-sync.mrrobot.fs",
    "mcp-health-monitor.mrrobot.fs",
    "mcp-network-doctor.mrrobot.fs",
    "mcp-storage-doctor.mrrobot.fs",
    "mcp-deploy-tracker.mrrobot.fs",
    "mcp-node-ops.mrrobot.fs",
    "mcp-documentation.mrrobot.fs",
    "mcp-smart-home.mrrobot.fs"
)

$currentContent = Get-Content $hostsPath -Raw
$linesToAdd = @()
$linesToAdd += ""
$linesToAdd += "# MCP Servers - infra nuevos (8036-8054) + documentation + smart-home"

foreach ($entry in $newEntries) {
    if ($currentContent -notmatch $entry) {
        $linesToAdd += "$ip $entry"
        Write-Host "Adding: $entry"
    } else {
        Write-Host "Already exists: $entry (skipping)"
    }
}

if ($linesToAdd.Count -gt 2) {
    $linesToAdd | Out-File -FilePath $hostsPath -Append -Encoding ASCII
    Write-Host "`nDone! Added $($linesToAdd.Count - 2) entries."
} else {
    Write-Host "`nAll entries already exist. Nothing to do."
}
