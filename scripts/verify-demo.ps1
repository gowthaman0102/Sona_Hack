$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$historyPath = Join-Path $repoRoot "backend\data\learning_history.json"

$historyExisted = Test-Path $historyPath
$historyBytes = $null

if ($historyExisted) {
    $historyBytes = [System.IO.File]::ReadAllBytes($historyPath)
}

try {
    Write-Host "=== AURA DEMO VERIFICATION ===" -ForegroundColor Cyan

    Write-Host "`n[1] Checking Ollama..." -ForegroundColor Yellow

    $ollama = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 10

    $installedModels = @(
        $ollama.models | ForEach-Object { $_.name }
    )

    $requiredModels = @(
        "qwen3:1.7b",
        "qwen3:4b",
        "qwen3:8b"
    )

    foreach ($model in $requiredModels) {
        if ($model -notin $installedModels) {
            throw "Required Ollama model is missing: $model"
        }
    }

    Write-Host "OLLAMA + REQUIRED MODELS: PASS" -ForegroundColor Green

    Write-Host "`n[2] Checking backend health..." -ForegroundColor Yellow

    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 10

    if ($health.status -ne "healthy") {
        throw "Backend health check failed."
    }

    Write-Host "BACKEND HEALTH: PASS" -ForegroundColor Green

    Write-Host "`n[3] Checking API metadata..." -ForegroundColor Yellow

    $metadata = Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -Method Get -TimeoutSec 10

    if ($metadata.version -ne "1.0.0") {
        throw "Unexpected API version: $($metadata.version)"
    }

    Write-Host "API VERSION 1.0.0: PASS" -ForegroundColor Green

    Write-Host "`n[4] Checking frontend..." -ForegroundColor Yellow

    $frontend = Invoke-WebRequest -Uri "http://localhost:5173/" -UseBasicParsing -TimeoutSec 10

    if ($frontend.StatusCode -ne 200) {
        throw "Frontend did not return HTTP 200."
    }

    Write-Host "FRONTEND AVAILABILITY: PASS" -ForegroundColor Green

    Write-Host "`n[5] Running real AURA route..." -ForegroundColor Yellow

    $body = @{
        prompt = "2+2"
    } | ConvertTo-Json

    $route = Invoke-RestMethod `
        -Uri "http://127.0.0.1:8000/route" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 180

    if ($route.response -ne "4") {
        throw "Live route returned unexpected answer: $($route.response)"
    }

    if ($route.routing.selected_model -notin $requiredModels) {
        throw "Live route used an unexpected model."
    }

    if ($route.confidence.should_escalate) {
        throw "Final response still requests escalation."
    }

    if ($route.analytics.attempt_count -lt 1) {
        throw "Route analytics did not record an attempt."
    }

    Write-Host "LIVE ROUTE RESPONSE: PASS" -ForegroundColor Green
    Write-Host "FINAL TIER  :" $route.routing.selected_tier
    Write-Host "FINAL MODEL :" $route.routing.selected_model
    Write-Host "RESPONSE    :" $route.response
    Write-Host "CONFIDENCE  :" $route.confidence.score
    Write-Host "ESCALATED   :" $route.escalation.escalated
    Write-Host "ATTEMPTS    :" $route.analytics.attempt_count

    Write-Host "`n=== AURA DEMO VERIFICATION: PASS ===" -ForegroundColor Green
}
finally {
    if ($historyExisted) {
        [System.IO.File]::WriteAllBytes($historyPath, $historyBytes)
    }
    elseif (Test-Path $historyPath) {
        Remove-Item $historyPath -Force
    }

    Write-Host "LEARNING HISTORY RESTORED: PASS" -ForegroundColor Green
}
