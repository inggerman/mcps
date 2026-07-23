$ErrorActionPreference = "Continue"

$MCPS = @(
    "mcp-prompt-engineer",
    "mcp-docker",
    "mcp-kafka",
    "mcp-llm-router",
    "mcp-git",
    "mcp-code-quality",
    "mcp-architecture",
    "mcp-event-driven",
    "mcp-orchestrator",
    "mcp-best-practices",
    "mcp-ci-cd",
    "mcp-design-patterns",
    "mcp-security-champion",
    "mcp-object-storage",
    "mcp-openapi",
    "mcp-documents",
    "mcp-kubernetes",
    "mcp-observability",
    "mcp-terraform",
    "mcp-snyk",
    "mcp-sonar",
    "mcp-java-build",
    "mcp-agent-runner",
    "mcp-personal-vault"
)

$HARBOR = "harbor.mrrobot.fs/ghl"
$TOTAL = $MCPS.Count
$CURRENT = 0
$FAILED = @()

foreach ($mcp in $MCPS) {
    $CURRENT++
    Write-Host "[$CURRENT/$TOTAL] Building $mcp..." -ForegroundColor Cyan

    & docker compose build $mcp 2>&1 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  BUILD FAILED for $mcp" -ForegroundColor Red
        $FAILED += $mcp
        continue
    }

    Write-Host "  Tagging as $HARBOR/$mcp`:latest..." -ForegroundColor Yellow
    & docker tag "${mcp}:latest" "$HARBOR/$mcp`:latest" 2>&1 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }

    Write-Host "  Pushing to Harbor..." -ForegroundColor Yellow
    & docker push "$HARBOR/$mcp`:latest" 2>&1 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  PUSH FAILED for $mcp" -ForegroundColor Red
        $FAILED += $mcp
    } else {
        Write-Host "  DONE $mcp" -ForegroundColor Green
    }
}

Write-Host "`n=== Complete: $($TOTAL - $FAILED.Count)/$TOTAL succeeded ===" -ForegroundColor Green
if ($FAILED.Count -gt 0) {
    Write-Host "FAILED: $($FAILED -join ', ')" -ForegroundColor Red
}
