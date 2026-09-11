# Run this script as Administrator
# It updates the hosts file and sets up port forwarding for MCP access

Write-Host "=== MCP Network Setup ===" -ForegroundColor Cyan

# 1. Update hosts file - point all mcp-*.mrrobot.fs to 100.68.63.120 (Tailscale K3s node IP)
$hostsPath = "C:\Windows\System32\drivers\etc\hosts"
$hostsContent = Get-Content $hostsPath

# Remove old mcp- entries
$hostsContent = $hostsContent | Where-Object { $_ -notmatch 'mcp-.*mrrobot\.fs' }

# Add new entries pointing to K3s node IP
$k3sNodeIP = "100.68.63.120"
$mcps = @(
    "mcp-tabular", "mcp-calendar", "mcp-markdown", "mcp-prompt-engineer",
    "mcp-structured-output", "mcp-fetch", "mcp-docker", "mcp-kafka",
    "mcp-project-memory", "mcp-llm-router", "mcp-git", "mcp-github",
    "mcp-code-quality", "mcp-architecture", "mcp-event-driven",
    "mcp-orchestrator", "mcp-best-practices", "mcp-ci-cd",
    "mcp-design-patterns", "mcp-security-champion", "mcp-snyk",
    "mcp-sonar", "mcp-database", "mcp-filesystem", "mcp-documents",
    "mcp-browser", "mcp-kubernetes", "mcp-object-storage",
    "mcp-observability", "mcp-openapi", "mcp-personal-vault",
    "mcp-agent-runner", "mcp-java-build", "mcp-terraform",
    "mcp-gob-mexico"
)

foreach ($mcp in $mcps) {
    $hostsContent += "$k3sNodeIP ${mcp}.mrrobot.fs"
}

$hostsContent | Set-Content $hostsPath -Force
Write-Host "  Hosts file updated: $($mcps.Count) entries -> $k3sNodeIP" -ForegroundColor Green

# 2. Set up port forwarding: port 80 -> 30124 (Kong NodePort)
netsh interface portproxy add v4tov4 listenport=80 listenaddress=0.0.0.0 connectport=30124 connectaddress=$k3sNodeIP
Write-Host "  Port forwarding: 0.0.0.0:80 -> ${k3sNodeIP}:30124" -ForegroundColor Green

# 3. Also forward 443 -> 30694 (Kong HTTPS NodePort)
netsh interface portproxy add v4tov4 listenport=443 listenaddress=0.0.0.0 connectport=30694 connectaddress=$k3sNodeIP
Write-Host "  Port forwarding: 0.0.0.0:443 -> ${k3sNodeIP}:30694" -ForegroundColor Green

# 4. Test
Write-Host ""
Write-Host "=== Testing mcp-tabular ===" -ForegroundColor Cyan
$json = '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
$result = curl.exe -s --connect-timeout 5 -X POST "http://mcp-tabular.mrrobot.fs/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d $json 2>&1
if ($result -match '"serverInfo"') {
    Write-Host "  mcp-tabular: OK" -ForegroundColor Green
} else {
    Write-Host "  mcp-tabular: FAILED" -ForegroundColor Red
    Write-Host "  Response: $result" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host "  MCPs accessible at: http://mcp-XXX.mrrobot.fs/mcp" -ForegroundColor White
Write-Host "  35 MCPs on ports 8001-8035 (via Kong ingress)" -ForegroundColor White
