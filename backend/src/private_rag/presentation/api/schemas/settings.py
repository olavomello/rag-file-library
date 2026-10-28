"""Response schema exposing a safe subset of effective settings.

Internal filesystem paths are intentionally excluded (AGENTS.md §20).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from private_rag.settings import Settings


class SettingsResponse(BaseModel):
    app_name: str
    app_env: str
    generation_model: str
    embedding_model: str
    temperature: float
    max_output_tokens: int
    context_window: int
    chunk_size: int
    chunk_overlap: int
    search_top_k: int
    rag_max_context_chunks: int
    rag_max_context_chars: int
    max_upload_size_mb: int
    indexing_concurrency: int
    generation_concurrency: int
    ocr_enabled: bool

    @classmethod
    def from_settings(cls, settings: Settings) -> SettingsResponse:
        return cls(
            app_name=settings.app_name,
            app_env=settings.app_env,
            generation_model=settings.ollama_generation_model,
            embedding_model=settings.ollama_embedding_model,
            temperature=settings.ollama_temperature,
            max_output_tokens=settings.ollama_max_output_tokens,
            context_window=settings.ollama_context_window,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            search_top_k=settings.search_top_k,
            rag_max_context_chunks=settings.rag_max_context_chunks,
            rag_max_context_chars=settings.rag_max_context_chars,
            max_upload_size_mb=settings.max_upload_size_mb,
            indexing_concurrency=settings.indexing_concurrency,
            generation_concurrency=settings.generation_concurrency,
            ocr_enabled=settings.ocr_enabled,
        )


class SettingsUpdateRequest(BaseModel):
    """Partial settings update. Any field left unset is unchanged."""

    generation_model: str | None = Field(default=None, min_length=1)
    embedding_model: str | None = Field(default=None, min_length=1)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: int | None = Field(default=None, ge=1)
    context_window: int | None = Field(default=None, ge=256)
    chunk_size: int | None = Field(default=None, ge=1)
    chunk_overlap: int | None = Field(default=None, ge=0)
    search_top_k: int | None = Field(default=None, ge=1)
    rag_max_context_chunks: int | None = Field(default=None, ge=1)
    rag_max_context_chars: int | None = Field(default=None, ge=500)
    max_upload_size_mb: int | None = Field(default=None, ge=1)
    indexing_concurrency: int | None = Field(default=None, ge=1)
    generation_concurrency: int | None = Field(default=None, ge=1)
    ocr_enabled: bool | None = None


class SettingsUpdateResponse(BaseModel):
    settings: SettingsResponse
    requires_restart: bool
    requires_reindex: bool
    message: str
