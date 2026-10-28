"""ChromaDB implementation of the chunk vector repository."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from private_rag.domain.entities.document_chunk import DocumentChunk
from private_rag.domain.entities.search_result import SearchResult
from private_rag.infrastructure.chroma.client import ChromaClientProvider

_COLLECTION = "document_chunks"


def _page_number(raw: object) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        value = int(str(raw))
    except (TypeError, ValueError):
        return None
    return value if value >= 1 else None


class ChromaChunkRepository:
    """Stores chunk embeddings in a dedicated ChromaDB collection."""

    def __init__(self, provider: ChromaClientProvider) -> None:
        self._provider = provider

    def _collection(self) -> Any:
        return self._provider.get_or_create_collection(_COLLECTION, space="cosine")

    def add_chunks(
        self,
        chunks: Sequence[DocumentChunk],
        embeddings: Sequence[Sequence[float]],
        *,
        embedding_model: str,
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if not chunks:
            return

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, str | int]] = []
        for chunk in chunks:
            ids.append(chunk.id)
            documents.append(chunk.content)
            metadata: dict[str, str | int] = {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "embedding_model": embedding_model,
            }
            metadata.update({key: str(value) for key, value in chunk.metadata.items()})
            metadatas.append(metadata)

        self._collection().add(
            ids=ids,
            embeddings=[list(vector) for vector in embeddings],
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        embedding: Sequence[float],
        *,
        top_k: int,
        document_ids: Sequence[str] | None = None,
        contains: Sequence[str] | None = None,
    ) -> list[SearchResult]:
        where = None
        if document_ids:
            where = {"document_id": {"$in": list(document_ids)}}

        where_document = self._where_document(contains)

        result = self._collection().query(
            query_embeddings=[list(embedding)],
            n_results=top_k,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"],
        )
        return self._map_results(result)

    @staticmethod
    def _where_document(contains: Sequence[str] | None) -> dict[str, Any] | None:
        terms = [term for term in (contains or []) if term]
        if not terms:
            return None
        if len(terms) == 1:
            return {"$contains": terms[0]}
        return {"$or": [{"$contains": term} for term in terms]}

    def delete_by_document(self, document_id: str) -> None:
        self._collection().delete(where={"document_id": document_id})

    def count(self, *, document_id: str | None = None) -> int:
        if document_id is None:
            return int(self._collection().count())
        got = self._collection().get(where={"document_id": document_id}, include=[])
        return len(got["ids"])

    @staticmethod
    def _map_results(result: Any) -> list[SearchResult]:
        ids = result["ids"][0]
        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]

        results: list[SearchResult] = []
        for chunk_id, content, meta, distance in zip(
            ids, documents, metadatas, distances, strict=True
        ):
            meta = meta or {}
            results.append(
                SearchResult(
                    document_id=str(meta.get("document_id", "")),
                    document_name=str(meta.get("document_name", "")),
                    chunk_id=str(chunk_id),
                    content=str(content),
                    distance=max(0.0, float(distance)),
                    page_number=_page_number(meta.get("page_number")),
                    metadata={key: str(value) for key, value in meta.items()},
                )
            )
        return results
