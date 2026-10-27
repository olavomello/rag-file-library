# ADR 0004: Semantic search (Phase 5)

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

Phase 5 adds semantic document search: find the most relevant passages for a
natural-language query. Per `AGENTS.md` §14 this must work independently of the
LLM and return enough information to locate and open the original documents.

## Decisions

1. **LLM-free retrieval.** `SemanticSearchUseCase` embeds the query with the
   embedding model and runs a vector query against the chunk store. No text
   generation is involved, so search works whenever the embedding model is
   available, even if the generation model is not.

2. **Results restricted to `INDEXED` documents.** The use case reads the set of
   indexed document ids from the registry and scopes the vector query to them. A
   document that is uploaded, pending, processing, or failed never contributes
   results, which upholds the "no partial exposure" guarantee from ADR-0003
   (reindex deletes-then-adds while the document is `processing`, hence excluded).

3. **Configurable limit and optional document filter.** `top_k` defaults to
   `SEARCH_TOP_K` and can be overridden per request (1–50). An optional
   `document_ids` filter is intersected with the indexed set; it is the seam for
   future knowledge-base scoping without an API change.

4. **Raw distance is returned, not a probability.** Each result carries the vector
   distance from ChromaDB as-is; the API and UI must not present it as a confidence
   or probability. Source resolution (document id, original name, page number,
   excerpt) comes from chunk metadata recorded at indexing time, so the client can
   link to `GET /documents/{id}/content` and `/download`.

5. **Empty queries rejected.** The request schema enforces a non-empty query (422);
   a whitespace-only query is rejected by the use case as `InvalidSearchQueryError`
   (400).

## Consequences

- New endpoint: `POST /api/v1/search/semantic`.
- Search is proven end-to-end with a deterministic keyword-based fake embedding
  model; real ranking quality with `embeddinggemma` is unverified until Ollama is
  available, but the retrieval path and scoping are covered by tests.
