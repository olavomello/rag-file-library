# Repo map

Directories, entry points, and key modules. Refresh only the areas that change.
Keep under ~150 lines.

```
rag-file-library/
├── backend/                         # FastAPI service (uv, Python 3.12, Clean Architecture)
│   ├── pyproject.toml               # deps, ruff, mypy (strict), pytest config
│   └── src/private_rag/
│       ├── main.py                  # create_app() factory + lifespan (prepare storage, start worker)
│       ├── settings.py              # Pydantic Settings (validated config)
│       ├── domain/                  # entities, value_objects, repositories (ports), services, exceptions — no I/O
│       ├── application/
│       │   ├── dto/                 # UploadResult, ParsedDocument, ComponentHealth, ...
│       │   ├── ports/               # Clock, FileStore, EmbeddingProvider, DocumentParser(Registry), TokenCounter, HealthProbe
│       │   ├── services/            # file_validation, text_normalization, chunking, token_counter
│       │   └── use_cases/           # documents/ (upload,list,get,content,delete), indexing/ (index_document), search/ (semantic_search)
│       ├── infrastructure/
│       │   ├── chroma/              # client provider, chunk_repository, document_registry, health_probe
│       │   ├── filesystem/          # file_storage, atomic, naming, json_indexing_job_repository
│       │   ├── parsers/             # pdf (PyMuPDF), docx, text, registry
│       │   ├── ollama/              # embedding_provider, health_probe
│       │   ├── indexing/            # worker (async background queue)
│       │   └── clock.py
│       ├── presentation/            # FastAPI: api/routes, api/schemas, api/dependencies, exception_handlers
│       └── container/               # composition root (explicit DI)
│   └── tests/                       # unit/, integration/, e2e/, contract/, fixtures/
│
├── frontend/                        # React + Vite + TS + Tailwind + TanStack Query
│   └── src/                         # app/, components/, features/{dashboard,documents,search,chat,settings}, services/, types/
│
├── data/                            # local persistence (git-ignored contents): uploads/, chroma/, jobs/, temp/, config/
├── docs/
│   ├── adr/                         # Architecture Decision Records (0001–0005) + template + index
│   ├── guides/                      # delegation, efficiency, security
│   ├── decisions.md                 # append-only decision log
│   ├── tasks.md                     # task taxonomy
│   └── repo-map.md                  # this file
├── scripts/                         # Windows PowerShell: setup, start, stop, test
├── .github/workflows/ci.yml         # CI: backend (ruff, mypy, pytest) + frontend (typecheck, lint, vitest)
├── AGENTS.md                        # project master prompt (RAG spec)
├── AGENT_TEAM.md                    # agent spawn/merge policy
├── ROADMAP.md                       # phase status
├── CHANGELOG.md / VERSION           # SemVer release tracking
└── README.md
```

## Entry points

- Backend API: `uv run uvicorn private_rag.main:app` → `http://127.0.0.1:8000` (docs at `/docs`).
- Frontend: `npm run dev` → `http://127.0.0.1:5173` (proxies `/api` to the backend).
- Tests: `scripts/test.ps1`, or `uv run pytest` (backend) / `npm test` (frontend).
