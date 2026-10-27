"""End-to-end semantic search tests.

Documents are indexed through the real pipeline using a deterministic
keyword-based fake embedding model, so search ranking is predictable without
Ollama. The LLM is not involved in search.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from private_rag.container.container import Container
from private_rag.main import create_app
from private_rag.settings import Settings

DOCS = "/api/v1/documents"
SEARCH = "/api/v1/search/semantic"

_VOCAB = ("vacation", "invoice", "python")


class KeywordEmbeddings:
    """Embeds text as keyword-occurrence counts plus a constant baseline dim."""

    model = "keyword-fake"

    def _vector(self, text: str) -> list[float]:
        low = text.lower()
        return [float(low.count(word)) for word in _VOCAB] + [1.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        _env_file=None,
        upload_dir=str(tmp_path / "uploads"),
        jobs_dir=str(tmp_path / "jobs"),
        chroma_path=str(tmp_path / "chroma"),
        temp_dir=str(tmp_path / "temp"),
        config_dir=str(tmp_path / "config"),
    )
    container = Container(settings)
    container.__dict__["embedding_provider"] = KeywordEmbeddings()
    with TestClient(create_app(settings=settings, container=container)) as test_client:
        yield test_client


def _upload_and_index(client: TestClient, name: str, text: str) -> str:
    response = client.post(f"{DOCS}/upload", files={"file": (name, text.encode(), "text/plain")})
    document_id = response.json()["document"]["id"]
    deadline = time.time() + 15.0
    while time.time() < deadline:
        if client.get(f"{DOCS}/{document_id}").json()["status"] == "indexed":
            return document_id
        time.sleep(0.05)
    raise AssertionError(f"{name} was not indexed in time")


def test_search_ranks_relevant_document_first(client: TestClient) -> None:
    vacation_id = _upload_and_index(
        client,
        "vacation.txt",
        "Our vacation policy grants twenty vacation days each year to every employee.",
    )
    _upload_and_index(
        client,
        "invoice.txt",
        "This invoice shows the invoice total and the invoice due date for the order.",
    )

    response = client.post(SEARCH, json={"query": "How many vacation days do we get?"})
    assert response.status_code == 200
    body = response.json()

    assert body["count"] >= 1
    top = body["results"][0]
    assert top["document_id"] == vacation_id
    assert top["document_name"] == "vacation.txt"
    assert "vacation" in top["excerpt"].lower()
    assert top["distance"] >= 0.0


def test_top_k_limits_results(client: TestClient) -> None:
    _upload_and_index(client, "a.txt", "vacation vacation vacation policy details here.")
    _upload_and_index(client, "b.txt", "invoice invoice invoice billing details here.")

    response = client.post(SEARCH, json={"query": "vacation", "top_k": 1})
    assert response.status_code == 200
    assert len(response.json()["results"]) <= 1


def test_search_with_no_indexed_documents_returns_empty(client: TestClient) -> None:
    response = client.post(SEARCH, json={"query": "anything"})
    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["results"] == []


def test_empty_query_is_rejected(client: TestClient) -> None:
    assert client.post(SEARCH, json={"query": ""}).status_code == 422
    assert client.post(SEARCH, json={"query": "   "}).status_code == 400
