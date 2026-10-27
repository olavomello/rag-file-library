"""Integration tests for the document management endpoints."""

from __future__ import annotations

import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from private_rag.container.container import Container
from private_rag.main import create_app
from private_rag.settings import Settings

BASE = "/api/v1/documents"


class _FakeEmbeddings:
    """Deterministic embeddings so background indexing succeeds without Ollama."""

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
    )
    container = Container(settings)
    container.__dict__["embedding_provider"] = _FakeEmbeddings()
    with TestClient(create_app(settings=settings, container=container)) as test_client:
        yield test_client


def _wait_for_status(
    client: TestClient, document_id: str, targets: set[str], timeout: float = 15.0
) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = client.get(f"{BASE}/{document_id}").json()["status"]
        if status in targets:
            return status
        time.sleep(0.05)
    raise AssertionError(f"Document {document_id} did not reach {targets}")


def _upload(client: TestClient, name: str, data: bytes, content_type: str = "text/plain"):
    return client.post(f"{BASE}/upload", files={"file": (name, data, content_type)})


def test_upload_list_get_download_delete_flow(client: TestClient) -> None:
    payload = b"The vacation policy grants 20 days per year."
    response = _upload(client, "policy.txt", payload)
    assert response.status_code == 201
    body = response.json()
    assert body["is_duplicate"] is False
    document_id = body["document"]["id"]
    assert body["document"]["status"] == "uploaded"
    # Internal path/stored name must not leak.
    assert "stored_name" not in body["document"]

    listing = client.get(BASE)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == document_id

    fetched = client.get(f"{BASE}/{document_id}")
    assert fetched.status_code == 200
    assert fetched.json()["original_name"] == "policy.txt"

    download = client.get(f"{BASE}/{document_id}/download")
    assert download.status_code == 200
    assert download.content == payload
    assert "policy.txt" in download.headers.get("content-disposition", "")

    deleted = client.delete(f"{BASE}/{document_id}")
    assert deleted.status_code == 204
    assert client.get(f"{BASE}/{document_id}").status_code == 404
    assert client.get(BASE).json()["total"] == 0


def test_duplicate_upload_is_flagged_and_not_restored(client: TestClient) -> None:
    data = b"identical content"
    first = _upload(client, "a.txt", data)
    second = _upload(client, "renamed.txt", data)

    assert first.json()["is_duplicate"] is False
    assert second.status_code == 201
    assert second.json()["is_duplicate"] is True
    assert second.json()["document"]["id"] == first.json()["document"]["id"]
    assert client.get(BASE).json()["total"] == 1


def test_unsupported_type_returns_415(client: TestClient) -> None:
    response = _upload(client, "malware.exe", b"MZ\x90\x00", "application/octet-stream")
    assert response.status_code == 415


def test_invalid_pdf_returns_400(client: TestClient) -> None:
    response = _upload(client, "fake.pdf", b"this is not a pdf", "application/pdf")
    assert response.status_code == 400


def test_valid_pdf_signature_is_accepted(client: TestClient) -> None:
    response = _upload(client, "real.pdf", b"%PDF-1.7\nbinary...", "application/pdf")
    assert response.status_code == 201
    assert response.json()["document"]["mime_type"] == "application/pdf"


def test_get_missing_returns_404(client: TestClient) -> None:
    assert client.get(f"{BASE}/does-not-exist").status_code == 404


def test_list_filters_by_status(client: TestClient) -> None:
    response = _upload(client, "a.txt", b"content a")
    document_id = response.json()["document"]["id"]
    # The document is queued and indexed in the background (fake embeddings).
    _wait_for_status(client, document_id, {"indexed"})

    assert client.get(f"{BASE}?status=indexed").json()["total"] == 1
    assert client.get(f"{BASE}?status=uploaded").json()["total"] == 0
    # Invalid status value is rejected by validation.
    assert client.get(f"{BASE}?status=bogus").status_code == 422
