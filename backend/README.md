# Private RAG — Backend

Local, privacy-first Retrieval-Augmented Generation API built with **FastAPI**,
**ChromaDB** (embedded), and **Ollama** (local models). Implemented with Clean
Architecture and Test-Driven Development.

## Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- (Optional, for AI features) [Ollama](https://ollama.com/) running locally

## Setup

```bash
uv sync --extra dev
```

## Run

```bash
uv run uvicorn private_rag.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs: http://127.0.0.1:8000/docs

## Test / lint / type-check

```bash
uv run pytest
uv run ruff check .
uv run mypy
```

## Architecture

```
src/private_rag/
├── domain/          # Entities, value objects, domain services, exceptions (no I/O)
├── application/     # Use cases, DTOs, ports (interfaces)
├── infrastructure/  # ChromaDB, Ollama, filesystem, parsers, chunking, indexing
├── presentation/    # FastAPI routes, schemas, dependencies, middleware
├── container/        # Composition root (explicit dependency injection)
├── settings.py      # Pydantic Settings (validated configuration)
└── main.py          # Application factory + ASGI entrypoint
```

Dependencies point inward: `presentation → application → domain`, with
`infrastructure` implementing `application` ports. The domain layer has no
framework or I/O imports.
