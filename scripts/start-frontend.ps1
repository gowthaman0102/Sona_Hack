$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendPath = Join-Path $repoRoot "frontend"
$packageJson = Join-Path $frontendPath "package.json"

if (-not (Test-Path $frontendPath)) {
    throw "Frontend directory not found: $frontendPath"
}

if (-not (Test-Path $packageJson)) {
    throw "Frontend package.json not found: $packageJson"
}

Set-Location $frontendPath

Write-Host "Starting AURA frontend on http://localhost:5173" -ForegroundColor Cyan

npm run dev
