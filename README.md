# Private RAG

**Local AI Knowledge Management & Intelligent Document Search.**

Private RAG is a fully local document-intelligence application. Upload documents,
index their contents, run semantic searches, locate original files, and ask natural
language questions answered by a locally executed LLM — with **no cloud services, no
paid APIs, and no external document transmission**.

The application provides two independent capabilities:

- **Document Search** — locate relevant documents and passages without the LLM.
- **RAG Chat** — generate grounded answers with source citations using retrieved content.

## Tech stack

| Layer          | Technology                                             |
| -------------- | ------------------------------------------------------ |
| Frontend       | React, TypeScript, Vite, Tailwind CSS, TanStack Query  |
| Backend        | Python 3.12, FastAPI, Pydantic v2, Uvicorn             |
| Vector store   | ChromaDB (embedded persistent client)                  |
| Local AI       | Ollama (`qwen3:0.6b` generation, `embeddinggemma` embeddings) |
| Doc parsing    | PyMuPDF (PDF), python-docx (DOCX), stdlib (TXT/MD)      |

Architecture follows **Clean Architecture** (domain → application → infrastructure →
presentation) with Test-Driven Development.

## Prerequisites

- **Python 3.12+** via [`uv`](https://docs.astral.sh/uv/)
- **Node.js 20+** and npm
- **Ollama** (optional, required only for embeddings + chat) — https://ollama.com/

## Quick start (Windows)

```powershell
# 1. Install dependencies and prepare data directories
scripts\setup.ps1

# 2. (optional) pull the local models
ollama pull qwen3:0.6b
ollama pull embeddinggemma

# 3. Start backend + frontend
scripts\start.ps1

# 4. Run the full test / lint / type-check suite
scripts\test.ps1

# 5. Stop the dev servers
scripts\stop.ps1
```

- Frontend: http://127.0.0.1:5173
- Backend API: http://127.0.0.1:8000
- API docs (Swagger): http://127.0.0.1:8000/docs

## Manual commands

Backend:

```bash
cd backend
uv sync --extra dev
uv run uvicorn private_rag.main:app --host 127.0.0.1 --port 8000 --reload
uv run pytest
```

Frontend:

```bash
cd frontend
npm install
npm run dev
npm test
```

## API spec (Insomnia / Postman)

The full OpenAPI spec is committed at [`backend/openapi.json`](backend/openapi.json) —
import it into Insomnia, Postman, or any OpenAPI reader. It is also served live at
http://127.0.0.1:8000/openapi.json, with Swagger UI at http://127.0.0.1:8000/docs.

Regenerate the committed spec after changing any endpoint (a contract test fails if it
is stale):

```bash
cd backend
uv run python scripts/export_openapi.py
```

## Project layout

```
rag-file-library/
├── backend/     # FastAPI + Clean Architecture (domain/application/infrastructure/presentation)
├── frontend/    # React + Vite + Tailwind SPA
├── data/        # Local persistence: uploads, chroma, jobs, temp, config (git-ignored contents)
├── docs/        # Architecture, API, testing, ADRs, deployment
└── scripts/     # Windows PowerShell setup/start/stop/test
```

## Privacy & security

- Binds to `127.0.0.1` by default — not exposed to the local network.
- No telemetry, analytics, or external inference. Documents never leave the machine.
- Uploaded documents are treated as untrusted data; no macros or embedded code are executed.
- The absence of authentication is intentional and safe **only** for trusted local use.

## Status

Under active, phased implementation. See [docs/adr](docs/adr/) for
architecture decision records and the implementation report (added on completion) for
the verified vs. unverified feature matrix.
