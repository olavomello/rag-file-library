# Private RAG - Start script (Windows PowerShell)
# Launches the backend (FastAPI/uvicorn) and frontend (Vite) dev servers.

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $Root 'data/config/.pids.json'

$backend = Start-Process -PassThru -WorkingDirectory (Join-Path $Root 'backend') `
    -FilePath 'uv' `
    -ArgumentList @('run', 'uvicorn', 'private_rag.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload')

$frontend = Start-Process -PassThru -WorkingDirectory (Join-Path $Root 'frontend') `
    -FilePath 'npm' `
    -ArgumentList @('run', 'dev')

@{ backend = $backend.Id; frontend = $frontend.Id } | ConvertTo-Json | Set-Content -Encoding utf8 $PidFile

Write-Host 'Private RAG is starting:' -ForegroundColor Cyan
Write-Host '  Backend  API : http://127.0.0.1:8000' -ForegroundColor Green
Write-Host '  API docs     : http://127.0.0.1:8000/docs' -ForegroundColor Green
Write-Host '  Frontend app : http://127.0.0.1:5173' -ForegroundColor Green
Write-Host "`nStop both with: scripts\stop.ps1" -ForegroundColor Yellow
