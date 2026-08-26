try {
    $r = Invoke-WebRequest -Uri 'http://mcp-agent-runner.mrrobot.fs/' -Method GET -TimeoutSec 10
    Write-Host "Status: $($r.StatusCode)"
} catch {
    Write-Host "Error: $($_.Exception.Message)"
}

# Test mcp-documentation too
try {
    $r2 = Invoke-WebRequest -Uri 'http://mcp-documentation.mrrobot.fs/' -Method GET -TimeoutSec 10
    Write-Host "Doc Status: $($r2.StatusCode)"
} catch {
    Write-Host "Doc Error: $($_.Exception.Message)"
}

# Test with /mcp endpoint
try {
    $r3 = Invoke-WebRequest -Uri 'http://mcp-agent-runner.mrrobot.fs/mcp' -Method POST -Body '{}' -ContentType 'application/json' -Headers @{'Accept'='application/json, text/event-stream'} -TimeoutSec 10
    Write-Host "MCP Status: $($r3.StatusCode)"
} catch {
    Write-Host "MCP Error: $($_.Exception.Message)"
}
