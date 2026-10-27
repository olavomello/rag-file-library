# Windows deployment / local run

Private RAG is designed for trusted local use on Windows (it ships without
authentication and binds to `127.0.0.1`).

## Prerequisites

- **Python 3.12+** via [`uv`](https://docs.astral.sh/uv/)
- **Node.js 20+** and npm
- **Ollama** (for embeddings + chat) — https://ollama.com/

## Setup

```powershell
scripts\setup.ps1
```

Installs backend (`uv sync`) and frontend (`npm install`) dependencies, creates the
`data/` directories, and copies `.env.example` to `.env`.

Pull the local models (required for indexing, search, and chat):

```powershell
ollama pull qwen3:0.6b
ollama pull embeddinggemma
```

## Run

```powershell
scripts\start.ps1    # backend on :8000, frontend on :5173
scripts\stop.ps1     # stops only the processes start.ps1 launched
```

- App: http://127.0.0.1:5173
- API docs: http://127.0.0.1:8000/docs

## Test / quality gate

```powershell
scripts\test.ps1
```

Runs backend ruff + mypy + pytest and frontend typecheck + lint + vitest.

## Data & backup

All state lives under `data/` (git-ignored): `uploads/` (original files),
`chroma/` (vectors + document registry), `jobs/` (indexing job state), `config/`,
`temp/`. Back up the `data/` directory to preserve the knowledge base. Deleting it
resets the application.

## Offline

After setup and model pulls, the application runs fully offline. If Ollama is not
running, document management and already-indexed browsing still work; indexing,
search, and chat require the embedding model, and chat additionally requires the
generation model.
