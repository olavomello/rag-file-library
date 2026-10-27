"""End-to-end ingestion tests: upload -> background index -> status/content/jobs.

The embedding model is faked (Ollama is not required) while the parser, chunker,
ChromaDB storage, and background worker all run for real.
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
JOBS = "/api/v1/indexing/jobs"


class FakeEmbeddings:
    model = "fake-embed"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t) % 5), 1.0, 0.0, 0.5] for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text) % 5), 1.0, 0.0, 0.5]


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        _env_file=None,
        upload_dir=str(tmp_path / "uploads"),
        jobs_dir=str(tmp_path / "jobs"),
        chroma_path=str(tmp_path / "chroma"),
        temp_dir=str(tmp_path / "temp"),
        config_dir=str(tmp_path / "config"),
        chunk_size=20,
        chunk_overlap=5,
    )
    container = Container(settings)
    container.__dict__["embedding_provider"] = FakeEmbeddings()
    with TestClient(create_app(settings=settings, container=container)) as test_client:
        yield test_client


def _wait_for_status(
    client: TestClient, document_id: str, targets: set[str], timeout: float = 15.0
) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = client.get(f"{DOCS}/{document_id}").json()["status"]
        if status in targets:
            return status
        time.sleep(0.05)
    raise AssertionError(f"Document {document_id} did not reach {targets} in time")


def _upload(client: TestClient, name: str, text: str) -> str:
    response = client.post(f"{DOCS}/upload", files={"file": (name, text.encode(), "text/plain")})
    assert response.status_code == 201
    return response.json()["document"]["id"]


SAMPLE = " ".join(f"The vacation policy sentence number {i} here." for i in range(15))


def test_upload_triggers_background_indexing(client: TestClient) -> None:
    document_id = _upload(client, "policy.txt", SAMPLE)

    status = _wait_for_status(client, document_id, {"indexed", "failed"})
    assert status == "indexed"

    document = client.get(f"{DOCS}/{document_id}").json()
    assert document["chunk_count"] > 0
    assert document["indexed_at"] is not None

    # A completed job exists for the document.
    jobs = client.get(JOBS).json()["items"]
    doc_jobs = [j for j in jobs if j["document_id"] == document_id]
    assert len(doc_jobs) == 1
    assert doc_jobs[0]["status"] == "completed"
    assert doc_jobs[0]["progress"] == 1.0


def test_content_endpoint_returns_extracted_text(client: TestClient) -> None:
    document_id = _upload(client, "notes.txt", "First line.\n\nSecond paragraph here.")
    body = client.get(f"{DOCS}/{document_id}/content").json()
    assert "First line." in body["content"]
    assert body["char_count"] == len(body["content"])


def test_reindex_requeues_and_completes(client: TestClient) -> None:
    document_id = _upload(client, "policy.txt", SAMPLE)
    _wait_for_status(client, document_id, {"indexed", "failed"})

    response = client.post(f"{DOCS}/{document_id}/reindex")
    assert response.status_code == 202
    assert response.json()["document_id"] == document_id

    status = _wait_for_status(client, document_id, {"indexed", "failed"})
    assert status == "indexed"


def test_job_endpoints_list_get_and_retry(client: TestClient) -> None:
    document_id = _upload(client, "policy.txt", SAMPLE)
    _wait_for_status(client, document_id, {"indexed", "failed"})

    jobs = client.get(JOBS).json()["items"]
    job_id = next(j["id"] for j in jobs if j["document_id"] == document_id)

    fetched = client.get(f"{JOBS}/{job_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == job_id

    retried = client.post(f"{JOBS}/{job_id}/retry")
    assert retried.status_code == 202
    assert retried.json()["retry_count"] >= 1

    status = _wait_for_status(client, document_id, {"indexed", "failed"})
    assert status == "indexed"


def test_get_missing_job_returns_404(client: TestClient) -> None:
    assert client.get(f"{JOBS}/nope").status_code == 404


def test_reindex_missing_document_returns_404(client: TestClient) -> None:
    assert client.post(f"{DOCS}/ghost/reindex").status_code == 404
