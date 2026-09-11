$ErrorActionPreference = "Continue"

$HARBOR = "harbor.mrrobot.fs/ghl"
$BASE_DIR = "c:\Users\germa\Documents\engineering\mcps"
$TOTAL = 0
$CURRENT = 0
$FAILED = @()
$SUCCEEDED = @()

# Get all MCP directories
$mcps = Get-ChildItem -Path $BASE_DIR -Directory -Filter "mcp-*" | Sort-Object Name
$TOTAL = $mcps.Count

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Building $TOTAL MCP images" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

foreach ($mcp in $mcps) {
    $CURRENT++
    $name = $mcp.Name
    $dockerfile = Join-Path $mcp.FullName "Dockerfile"
    
    if (-not (Test-Path $dockerfile)) {
        Write-Host "  [$CURRENT/$TOTAL] SKIP $name (no Dockerfile)" -ForegroundColor DarkGray
        continue
    }
    
    Write-Host "  [$CURRENT/$TOTAL] Building $name..." -ForegroundColor Cyan -NoNewline
    
    $buildResult = docker build -t "${HARBOR}/${name}:latest" -f $dockerfile $BASE_DIR 2>&1
    $buildExit = $LASTEXITCODE
    
    if ($buildExit -ne 0) {
        Write-Host " BUILD FAILED" -ForegroundColor Red
        $FAILED += $name
        continue
    }
    
    Write-Host " pushing..." -ForegroundColor Yellow -NoNewline
    $pushResult = docker push "${HARBOR}/${name}:latest" 2>&1
    $pushExit = $LASTEXITCODE
    
    if ($pushExit -ne 0) {
        Write-Host " PUSH FAILED" -ForegroundColor Red
        $FAILED += $name
    } else {
        Write-Host " OK" -ForegroundColor Green
        $SUCCEEDED += $name
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Results: $($SUCCEEDED.Count)/$TOTAL succeeded" -ForegroundColor Green
if ($FAILED.Count -gt 0) {
    Write-Host "  FAILED: $($FAILED -join ', ')" -ForegroundColor Red
}
Write-Host "============================================" -ForegroundColor Cyan

# Save results for next step
$succeeded | ConvertTo-Json | Out-File "C:\Users\germa\mcp-build-results.json"
