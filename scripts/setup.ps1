# Private RAG - Setup script (Windows PowerShell)
# Verifies tooling, installs dependencies, and prepares local data directories.

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot

function Write-Section($text) { Write-Host "`n=== $text ===" -ForegroundColor Cyan }
function Test-Command($name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }

Write-Section 'Checking prerequisites'

if (-not (Test-Command 'uv')) {
    Write-Host "uv is not installed. Install it from https://docs.astral.sh/uv/ (it manages Python 3.12)." -ForegroundColor Red
    exit 1
}
Write-Host "uv: $(uv --version)" -ForegroundColor Green

if (-not (Test-Command 'node')) {
    Write-Host 'Node.js is not installed. Install Node.js 20+ from https://nodejs.org/.' -ForegroundColor Red
    exit 1
}
Write-Host "node: $(node --version)" -ForegroundColor Green
Write-Host "npm:  $(npm --version)" -ForegroundColor Green

Write-Section 'Preparing data directories'
foreach ($dir in @('uploads', 'chroma', 'jobs', 'temp', 'config')) {
    $path = Join-Path $Root "data/$dir"
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}
Write-Host 'Data directories ready.' -ForegroundColor Green

Write-Section 'Installing backend dependencies (uv)'
Push-Location (Join-Path $Root 'backend')
uv sync --extra dev
Pop-Location

Write-Section 'Installing frontend dependencies (npm)'
Push-Location (Join-Path $Root 'frontend')
npm install
Pop-Location

Write-Section 'Environment file'
$envPath = Join-Path $Root '.env'
if (-not (Test-Path $envPath)) {
    Copy-Item (Join-Path $Root '.env.example') $envPath
    Write-Host 'Created .env from .env.example.' -ForegroundColor Green
} else {
    Write-Host '.env already exists; leaving it untouched.' -ForegroundColor Yellow
}

Write-Section 'Ollama (local AI models)'
if (Test-Command 'ollama') {
    Write-Host "ollama: $(ollama --version)" -ForegroundColor Green
    Write-Host 'Download the required models with:' -ForegroundColor Yellow
} else {
    Write-Host 'Ollama is NOT installed. AI features (embeddings, chat) require it.' -ForegroundColor Yellow
    Write-Host 'Install from https://ollama.com/, then run:' -ForegroundColor Yellow
}
Write-Host '    ollama pull qwen3:0.6b' -ForegroundColor White
Write-Host '    ollama pull embeddinggemma' -ForegroundColor White

Write-Host "`nSetup complete. Start the app with: scripts\start.ps1" -ForegroundColor Cyan
