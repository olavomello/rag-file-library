"""Unit tests for application configuration (Pydantic Settings)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from private_rag.settings import Settings


def _base_kwargs(**overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "chunk_size": 500,
        "chunk_overlap": 75,
        "max_upload_size_mb": 25,
        "search_top_k": 5,
        "indexing_concurrency": 1,
        "generation_concurrency": 1,
        "api_port": 8000,
    }
    kwargs.update(overrides)
    return kwargs


def test_defaults_match_specification() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "Private RAG"
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8000
    assert settings.ollama_generation_model == "qwen3:0.6b"
    assert settings.ollama_embedding_model == "embeddinggemma"
    assert settings.chunk_size == 500
    assert settings.chunk_overlap == 75
    assert settings.search_top_k == 5
    assert settings.indexing_concurrency == 1
    assert settings.generation_concurrency == 1
    assert settings.max_upload_size_mb == 25


def test_max_upload_size_bytes_is_derived() -> None:
    settings = Settings(_env_file=None, **_base_kwargs(max_upload_size_mb=10))
    assert settings.max_upload_size_bytes == 10 * 1024 * 1024


def test_chunk_overlap_must_be_smaller_than_chunk_size() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **_base_kwargs(chunk_size=100, chunk_overlap=100))


def test_chunk_overlap_cannot_be_negative() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **_base_kwargs(chunk_overlap=-1))


def test_api_port_must_be_in_valid_range() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **_base_kwargs(api_port=70000))


def test_concurrency_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **_base_kwargs(indexing_concurrency=0))


def test_cors_origins_parsed_from_csv_string() -> None:
    settings = Settings(_env_file=None, cors_origins="http://localhost:5173,http://127.0.0.1:5173")
    assert "http://localhost:5173" in settings.cors_origins
    assert "http://127.0.0.1:5173" in settings.cors_origins


def test_env_prefix_is_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_GENERATION_MODEL", "qwen3:1.7b")
    settings = Settings(_env_file=None)
    assert settings.ollama_generation_model == "qwen3:1.7b"
