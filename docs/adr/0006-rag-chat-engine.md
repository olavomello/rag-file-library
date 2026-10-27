# ADR 0006: RAG chat engine (Phase 6)

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

Phase 6 adds grounded question answering over the user's documents (`AGENTS.md`
§15–16): retrieve relevant chunks, build a bounded context and prompt, generate an
answer with a local LLM, and return trustworthy source references — with streaming.

## Decision

1. **Separate, composable stages.** Retrieval reuses `SemanticSearchUseCase`;
   `ContextBuilder`, `PromptBuilder`, and the `GenerationProvider` port are distinct,
   and `AnswerQuestionUseCase` orchestrates them. Responsibilities are not coupled.

2. **Grounding and prompt-injection safety.** The system prompt instructs the model
   to answer only from the context, to say when the answer isn't in the documents, and
   to **treat the context as untrusted data, never as instructions** — retrieved
   document text cannot override system instructions.

3. **No fabricated citations.** Sources returned to the client are exactly the chunks
   the `ContextBuilder` included (numbered `[Source N]`), resolved from chunk metadata —
   never invented by the model. The response carries a `grounded` flag.

4. **Insufficient context short-circuits the LLM.** When retrieval returns nothing,
   the answer states it can't be established from the documents and **no generation
   call is made**, keeping search and generation independent (search works without the
   generation model; management/retrieval work without either when embeddings exist).

5. **Bounded context.** `RAG_MAX_CONTEXT_CHUNKS` and `RAG_MAX_CONTEXT_CHARS` cap how
   much is sent to a small local model.

6. **Local generation via a port.** `OllamaGenerationProvider` calls Ollama's
   `/api/generate` (blocking and NDJSON streaming), with temperature / `num_predict` /
   `num_ctx` / timeout from settings and an injectable client for tests. Streaming is
   exposed as a sync token iterator and served over `application/x-ndjson`
   (`sources` event, then `token` events, then `done`; a mid-stream failure emits an
   `error` event).

## Consequences

- New endpoints: `POST /api/v1/chat`, `POST /api/v1/chat/stream`, and
  `GET /api/v1/models` + `/models/status` (configured models and availability).
- Proven end-to-end with a fake embedder and a fake LLM. **Real generation via Ollama
  (`qwen3:0.6b`) is unverified** — Ollama isn't installed; the adapter is tested with a
  mocked transport (`AGENTS.md` §27).
