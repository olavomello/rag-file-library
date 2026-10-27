"""DTOs for document use cases."""

from __future__ import annotations

from dataclasses import dataclass

from private_rag.domain.entities.document import Document


@dataclass(frozen=True, slots=True)
class UploadResult:
    """Outcome of an upload: the stored document and whether it already existed."""

    document: Document
    is_duplicate: bool
