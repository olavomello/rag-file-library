"""Document management endpoints: upload, list, get, download, delete."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse

from private_rag.container.container import Container
from private_rag.domain.value_objects.document_status import DocumentStatus
from private_rag.presentation.api.dependencies.providers import get_container
from private_rag.presentation.api.schemas.documents import (
    DocumentContentResponse,
    DocumentListResponse,
    DocumentResponse,
    UploadResponse,
)
from private_rag.presentation.api.schemas.indexing import JobResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    container: Container = Depends(get_container),
) -> UploadResponse:
    data = await file.read()
    use_case = container.upload_document_use_case
    result = await asyncio.to_thread(
        use_case.execute, filename=file.filename or "upload", data=data
    )
    # Newly stored documents are queued for background indexing.
    if not result.is_duplicate:
        await container.indexing_worker.enqueue(result.document.id)
    return UploadResponse(
        document=DocumentResponse.from_entity(result.document),
        is_duplicate=result.is_duplicate,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    status_filter: DocumentStatus | None = Query(default=None, alias="status"),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    container: Container = Depends(get_container),
) -> DocumentListResponse:
    documents = await asyncio.to_thread(
        container.list_documents_use_case.execute,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    total = await asyncio.to_thread(
        container.document_repository.count, status=status_filter
    )
    return DocumentListResponse(
        items=[DocumentResponse.from_entity(doc) for doc in documents],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    container: Container = Depends(get_container),
) -> DocumentResponse:
    document = await asyncio.to_thread(
        container.get_document_use_case.execute, document_id
    )
    return DocumentResponse.from_entity(document)


@router.get("/{document_id}/content", response_model=DocumentContentResponse)
async def get_document_content(
    document_id: str,
    container: Container = Depends(get_container),
) -> DocumentContentResponse:
    content = await asyncio.to_thread(
        container.get_document_content_use_case.execute, document_id
    )
    return DocumentContentResponse(
        document_id=document_id, content=content, char_count=len(content)
    )


@router.post(
    "/{document_id}/reindex",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def reindex_document(
    document_id: str,
    container: Container = Depends(get_container),
) -> JobResponse:
    # Confirm the document exists (404 otherwise), then queue it for indexing.
    await asyncio.to_thread(container.get_document_use_case.execute, document_id)
    job = await container.indexing_worker.enqueue(document_id)
    return JobResponse.from_entity(job)


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    container: Container = Depends(get_container),
) -> FileResponse:
    document = await asyncio.to_thread(
        container.get_document_use_case.execute, document_id
    )
    path = container.file_storage.path_for(document.stored_name)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Original file is missing"
        )
    return FileResponse(
        path=path, media_type=document.mime_type, filename=document.original_name
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    container: Container = Depends(get_container),
) -> Response:
    await asyncio.to_thread(container.delete_document_use_case.execute, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
