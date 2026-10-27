# Architecture overview

Private RAG is a local-first document-intelligence app. The backend follows Clean
Architecture; the frontend is a feature-based React SPA. Everything runs on the user's
machine — no cloud services, no paid APIs.

## Layers (backend)

```
presentation  →  application  →  domain
      ↑                ↑
      └──── infrastructure ────┘   (implements application/domain ports)
```

Dependencies point inward. The rule is enforced by a test
(`tests/contract/test_architecture.py`): the **domain** imports no framework, I/O
library, or outer layer; the **application** imports no infrastructure or presentation.

- **domain/** — entities (`Document`, `DocumentChunk`, `KnowledgeBase`, `IndexingJob`,
  `SearchResult`, `ChatMessage`), value objects (status enums, `SourceReference`),
  repository contracts (`Protocol`s), pure services (hashing), and exceptions. No I/O.
- **application/** — use cases (documents, indexing, search, chat, dashboard), DTOs,
  ports (`Clock`, `FileStore`, `EmbeddingProvider`, `GenerationProvider`,
  `DocumentParserRegistry`, `TokenCounter`, `HealthProbe`), and pure services
  (validation, chunking, context/prompt building, naming, token counting).
- **infrastructure/** — ChromaDB client + repositories, filesystem storage + atomic
  JSON job store, parsers (PyMuPDF/python-docx/stdlib), Ollama adapters (embeddings,
  generation, model catalog, health), and the background indexing worker.
- **presentation/** — FastAPI routes, Pydantic schemas, DI providers, exception
  handlers. Business logic lives in use cases, not route handlers.
- **container/** — the composition root wiring concrete implementations to ports via
  explicit DI; owns the single embedded ChromaDB client.

## Key flows

**Ingestion (upload → searchable):** `POST /documents/upload` validates and stores the
file and registers metadata → the document is queued on the in-process async worker →
the worker parses → chunks (overlap, page numbers) → embeds (Ollama) → stores vectors
in ChromaDB → marks the document `indexed`. All-or-nothing: on failure, partial chunks
are removed and the document is marked `failed`. Job state persists to JSON and is
recovered on restart.

**Search (no LLM):** `POST /search/semantic` embeds the query and runs a ChromaDB
vector search scoped to `indexed` documents only.

**RAG chat:** `POST /chat` (and `/chat/stream`) retrieves chunks, builds a bounded,
numbered context and a grounded prompt, generates with Ollama, and returns the answer
with real source citations. If retrieval is empty, it says so without calling the LLM.

## Technology

React/Vite/TypeScript/Tailwind/TanStack Query · FastAPI/Pydantic v2/Uvicorn ·
ChromaDB (embedded) · Ollama (`qwen3:0.6b`, `embeddinggemma`) · PyMuPDF/python-docx.
Tooling: `uv`, ruff, mypy (strict), pytest; ESLint, Prettier, Vitest.
