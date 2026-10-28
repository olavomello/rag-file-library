"""Apply and validate user settings overrides on top of base settings.

Overrides are stored under stable *public* keys (the same ones the API exposes)
and mapped here to the concrete :class:`Settings` field names. Applying produces a
fresh, fully validated ``Settings`` — so invalid combinations (e.g. overlap >= size)
are rejected by the same rules that validate configuration at startup.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from private_rag.settings import Settings

# Public override key -> Settings field name.
OVERRIDABLE_FIELDS: dict[str, str] = {
    "generation_model": "ollama_generation_model",
    "embedding_model": "ollama_embedding_model",
    "temperature": "ollama_temperature",
    "max_output_tokens": "ollama_max_output_tokens",
    "context_window": "ollama_context_window",
    "chunk_size": "chunk_size",
    "chunk_overlap": "chunk_overlap",
    "search_top_k": "search_top_k",
    "rag_max_context_chunks": "rag_max_context_chunks",
    "rag_max_context_chars": "rag_max_context_chars",
    "max_upload_size_mb": "max_upload_size_mb",
    "indexing_concurrency": "indexing_concurrency",
    "generation_concurrency": "generation_concurrency",
    "ocr_enabled": "ocr_enabled",
}


def filter_overridable(overrides: Mapping[str, Any]) -> dict[str, Any]:
    """Keep only recognised, non-null override keys."""
    return {
        key: value
        for key, value in overrides.items()
        if key in OVERRIDABLE_FIELDS and value is not None
    }


def apply_overrides(base: Settings, overrides: Mapping[str, Any]) -> Settings:
    """Return a new validated ``Settings`` = ``base`` with ``overrides`` applied.

    Raises ``pydantic.ValidationError`` if the result is invalid.
    """
    data: dict[str, Any] = base.model_dump()
    for public_key, value in filter_overridable(overrides).items():
        data[OVERRIDABLE_FIELDS[public_key]] = value
    # _env_file is a valid pydantic-settings init kwarg (disables .env re-read);
    # it is not part of the model's generated __init__ signature that mypy sees.
    return Settings(_env_file=None, **data)  # type: ignore[call-arg]
