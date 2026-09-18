$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $repoRoot "backend"
$venvActivate = Join-Path $backendPath ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $backendPath)) {
    throw "Backend directory not found: $backendPath"
}

if (-not (Test-Path $venvActivate)) {
    throw "Backend virtual environment not found: $venvActivate"
}

Set-Location $backendPath

. $venvActivate

Write-Host "Starting AURA backend on http://127.0.0.1:8000" -ForegroundColor Cyan

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
