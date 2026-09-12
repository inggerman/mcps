# Test streamable-http endpoint
try {
    $headers = @{
        'Accept' = 'application/json, text/event-stream'
        'Content-Type' = 'application/json'
    }
    $body = '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
    $r = Invoke-WebRequest -Uri 'http://mcp-agent-runner.mrrobot.fs/mcp' -Method POST -Body $body -Headers $headers -TimeoutSec 10
    Write-Host "Status: $($r.StatusCode)"
    Write-Host "Content-Type: $($r.Headers['Content-Type'])"
    Write-Host "Body: $($r.Content.Substring(0, [Math]::Min(200, $r.Content.Length)))"
} catch {
    Write-Host "Error: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        Write-Host "Status: $([int]$_.Exception.Response.StatusCode)"
    }
}
