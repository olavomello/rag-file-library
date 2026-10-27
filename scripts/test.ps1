# Private RAG - Test script (Windows PowerShell)
# Runs backend and frontend tests, type checks, and linting.

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$failed = $false

function Invoke-Step($name, $scriptBlock) {
    Write-Host "`n=== $name ===" -ForegroundColor Cyan
    try {
        & $scriptBlock
        if ($LASTEXITCODE -ne 0) { throw "exit code $LASTEXITCODE" }
        Write-Host "PASS: $name" -ForegroundColor Green
    } catch {
        Write-Host "FAIL: $name ($_)" -ForegroundColor Red
        $script:failed = $true
    }
}

Push-Location (Join-Path $Root 'backend')
Invoke-Step 'Backend: ruff'   { uv run ruff check . }
Invoke-Step 'Backend: mypy'   { uv run mypy }
Invoke-Step 'Backend: pytest' { uv run pytest }
Pop-Location

Push-Location (Join-Path $Root 'frontend')
Invoke-Step 'Frontend: typecheck' { npm run typecheck }
Invoke-Step 'Frontend: lint'      { npm run lint }
Invoke-Step 'Frontend: vitest'    { npm test }
Pop-Location

if ($failed) {
    Write-Host "`nSome checks failed." -ForegroundColor Red
    exit 1
}
Write-Host "`nAll checks passed." -ForegroundColor Green
