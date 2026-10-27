# Private RAG - Stop script (Windows PowerShell)
# Stops only the processes started by start.ps1 (tracked by PID file).

$ErrorActionPreference = 'SilentlyContinue'
$Root = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $Root 'data/config/.pids.json'

if (-not (Test-Path $PidFile)) {
    Write-Host 'No PID file found; nothing to stop.' -ForegroundColor Yellow
    return
}

$pids = Get-Content $PidFile | ConvertFrom-Json
foreach ($entry in @('backend', 'frontend')) {
    $procId = $pids.$entry
    if ($procId) {
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($proc) {
            # Stop the process tree (dev servers spawn children).
            Stop-Process -Id $procId -Force
            Write-Host "Stopped $entry (PID $procId)." -ForegroundColor Green
        } else {
            Write-Host "$entry (PID $procId) is not running." -ForegroundColor Yellow
        }
    }
}

Remove-Item $PidFile -ErrorAction SilentlyContinue
Write-Host 'Done.' -ForegroundColor Cyan
