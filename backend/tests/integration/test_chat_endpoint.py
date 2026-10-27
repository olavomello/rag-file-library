"""End-to-end RAG chat tests with fake embeddings and a fake LLM (no Ollama)."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from private_rag.container.container import Container
from private_rag.main import create_app
from private_rag.settings import Settings

DOCS = "/api/v1/documents"
CHAT = "/api/v1/chat"

_VOCAB = ("vacation", "invoice")


class KeywordEmbeddings:
    model = "keyword-fake"

    def _vector(self, text: str) -> list[float]:
        low = text.lower()
        return [float(low.count(w)) for w in _VOCAB] + [1.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class FakeGeneration:
    model = "fake-llm"

    def generate(self, prompt: str) -> str:
        assert "Context:" in prompt
        return "Based on the documents, employees get 20 vacation days. [Source 1]"

    def stream_generate(self, prompt: str) -> Iterator[str]:
        yield from ["Based ", "on ", "the ", "documents."]


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
    container.__dict__["generation_provider"] = FakeGeneration()
    with TestClient(create_app(settings=settings, container=container)) as test_client:
        yield test_client


def _index(client: TestClient, name: str, text: str) -> None:
    resp = client.post(f"{DOCS}/upload", files={"file": (name, text.encode(), "text/plain")})
    document_id = resp.json()["document"]["id"]
    deadline = time.time() + 15.0
    while time.time() < deadline:
        if client.get(f"{DOCS}/{document_id}").json()["status"] == "indexed":
            return
        time.sleep(0.05)
    raise AssertionError("document not indexed in time")


def test_chat_returns_grounded_answer_with_sources(client: TestClient) -> None:
    _index(client, "policy.txt", "Our vacation policy grants twenty vacation days per year.")

    response = client.post(CHAT, json={"question": "How many vacation days?"})
    assert response.status_code == 200
    body = response.json()

    assert body["grounded"] is True
    assert "20 vacation days" in body["answer"]
    assert len(body["sources"]) >= 1
    assert body["sources"][0]["document_name"] == "policy.txt"


def test_chat_without_indexed_documents_is_not_grounded(client: TestClient) -> None:
    response = client.post(CHAT, json={"question": "Anything here?"})
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["sources"] == []


def test_chat_stream_emits_sources_then_tokens_then_done(client: TestClient) -> None:
    _index(client, "policy.txt", "Our vacation policy grants twenty vacation days per year.")

    response = client.post(f"{CHAT}/stream", json={"question": "vacation days?"})
    assert response.status_code == 200

    events = [json.loads(line) for line in response.text.splitlines() if line.strip()]
    assert events[0]["type"] == "sources"
    assert events[0]["grounded"] is True
    assert len(events[0]["sources"]) >= 1

    tokens = [e["text"] for e in events if e["type"] == "token"]
    assert "".join(tokens) == "Based on the documents."
    assert events[-1]["type"] == "done"


def test_empty_question_rejected(client: TestClient) -> None:
    assert client.post(CHAT, json={"question": ""}).status_code == 422


def test_models_endpoint_reports_consistent_status(client: TestClient) -> None:
    body = client.get("/api/v1/models").json()
    assert body["generation_model"] == "qwen3:0.6b"
    assert body["embedding_model"] == "embeddinggemma"
    assert isinstance(body["ollama_available"], bool)
    # Availability flags must be consistent with reachability regardless of
    # whether Ollama happens to be running in this environment.
    if not body["ollama_available"]:
        assert body["generation_available"] is False
        assert body["embedding_available"] is False
        assert body["available_models"] == []
