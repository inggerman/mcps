# Test multiple MCP servers
$servers = @("mcp-agent-runner", "mcp-documentation", "mcp-tabular", "mcp-calendar", "mcp-argocd")
$headers = @{
    'Accept' = 'application/json, text/event-stream'
    'Content-Type' = 'application/json'
}
$body = '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

foreach ($s in $servers) {
    $url = "http://$s.mrrobot.fs/mcp"
    try {
        $r = Invoke-WebRequest -Uri $url -Method POST -Body $body -Headers $headers -TimeoutSec 10
        Write-Host "$s -> $($r.StatusCode) OK"
    } catch {
        $status = ""
        if ($_.Exception.Response) {
            $status = [int]$_.Exception.Response.StatusCode
        }
        Write-Host "$s -> $status $($_.Exception.Message.Substring(0, [Math]::Min(80, $_.Exception.Message.Length)))"
    }
}
