# Hosts file cleanup script - run as admin
# Remove old 127.0.0.1 mrrobot.fs entries and keep only Tailscale-based ones

$hostsPath = "C:\Windows\System32\drivers\etc\hosts"
$content = Get-Content $hostsPath

# Filter out old mrrobot entries pointing to 127.0.0.1 (except MCP ones)
$newContent = $content | Where-Object {
    $_ -notmatch "^127\.0\.0\.1\s+(argocd|gitea|harbor|vault|grafana|kubecost|minio|minio-api|pgadmin|mongo-express|rabbitmq|backstage|workflows|api|mrrobot|headlamp|prometheus|alertmanager|n8n|sonar|demo|demo-qa|demo-stg|hubble|loki|tempo)\.mrrobot\.fs" -and
    $_ -notmatch "^100\.68\.63\.120\s+(argocd|gitea|harbor|vault|grafana|kubecost|minio|minio-api|pgadmin|mongo-express|rabbitmq|backstage|workflows|api|mrrobot|headlamp|prometheus|alertmanager|n8n|sonar|demo|demo-qa|demo-stg|hubble|loki|tempo)\.mrrobot\.fs"
}

# Add clean Tailscale entries
$clusterEntries = @(
    "",
    "# K3s Cluster - Kong Ingress via Tailscale (stable across reboots)",
    "100.68.63.120 gitea.mrrobot.fs",
    "100.68.63.120 harbor.mrrobot.fs",
    "100.68.63.120 argocd.mrrobot.fs",
    "100.68.63.120 grafana.mrrobot.fs",
    "100.68.63.120 prometheus.mrrobot.fs",
    "100.68.63.120 alertmanager.mrrobot.fs",
    "100.68.63.120 n8n.mrrobot.fs",
    "100.68.63.120 minio.mrrobot.fs",
    "100.68.63.120 minio-api.mrrobot.fs",
    "100.68.63.120 kubecost.mrrobot.fs",
    "100.68.63.120 headlamp.mrrobot.fs",
    "100.68.63.120 vault.mrrobot.fs",
    "100.68.63.120 sonar.mrrobot.fs",
    "100.68.63.120 rabbitmq.mrrobot.fs",
    "100.68.63.120 pgadmin.mrrobot.fs",
    "100.68.63.120 mongo-express.mrrobot.fs",
    "100.68.63.120 backstage.mrrobot.fs",
    "100.68.63.120 demo.mrrobot.fs",
    "100.68.63.120 demo-qa.mrrobot.fs",
    "100.68.63.120 demo-stg.mrrobot.fs",
    "100.68.63.120 workflows.mrrobot.fs",
    "100.68.63.120 hubble.mrrobot.fs",
    "100.68.63.120 loki.mrrobot.fs",
    "100.68.63.120 tempo.mrrobot.fs"
)

$newContent += $clusterEntries
$newContent | Set-Content $hostsPath -Encoding ASCII
Write-Host "Hosts file cleaned and updated"
