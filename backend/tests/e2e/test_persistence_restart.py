"""End-to-end: indexed data survives an application restart (AGENTS.md scenario 5).

A document is uploaded and indexed through one app instance; a second instance is
then built on the same data directories (simulating a process restart) and must see
the document as indexed and still searchable.
"""

from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from private_rag.container.container import Container
from private_rag.main import create_app
from private_rag.settings import Settings

DOCS = "/api/v1/documents"
SEARCH = "/api/v1/search/semantic"

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


def _clear_chroma_cache() -> None:
    try:
        from chromadb.api.shared_system_client import SharedSystemClient

        SharedSystemClient.clear_system_cache()
    except Exception:  # pragma: no cover
        pass


def _app(settings: Settings) -> TestClient:
    container = Container(settings)
    container.__dict__["embedding_provider"] = KeywordEmbeddings()
    return TestClient(create_app(settings=settings, container=container))


def test_indexed_data_survives_restart(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        upload_dir=str(tmp_path / "uploads"),
        jobs_dir=str(tmp_path / "jobs"),
        chroma_path=str(tmp_path / "chroma"),
        temp_dir=str(tmp_path / "temp"),
        config_dir=str(tmp_path / "config"),
    )

    payload = b"Our vacation policy grants twenty vacation days."

    # --- First "process": upload and index a document. ---
    with _app(settings) as client:
        upload = client.post(
            f"{DOCS}/upload",
            files={"file": ("policy.txt", payload, "text/plain")},
        )
        document_id = upload.json()["document"]["id"]
        deadline = time.time() + 15.0
        while time.time() < deadline:
            if client.get(f"{DOCS}/{document_id}").json()["status"] == "indexed":
                break
            time.sleep(0.05)
        assert client.get(f"{DOCS}/{document_id}").json()["status"] == "indexed"
        first_chunks = client.get(f"{DOCS}/{document_id}").json()["chunk_count"]
        assert first_chunks > 0

    # Simulate the process exiting.
    _clear_chroma_cache()

    # --- Second "process": same data dirs, fresh app. ---
    with _app(settings) as client:
        fetched = client.get(f"{DOCS}/{document_id}").json()
        assert fetched["status"] == "indexed"
        assert fetched["chunk_count"] == first_chunks

        results = client.post(SEARCH, json={"query": "vacation days"}).json()
        assert results["count"] >= 1
        assert results["results"][0]["document_id"] == document_id

        content = client.get(f"{DOCS}/{document_id}/content").json()
        assert "vacation" in content["content"].lower()
