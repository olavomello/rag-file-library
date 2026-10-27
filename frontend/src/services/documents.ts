import { API_BASE_URL, apiDelete, apiGet, apiPost, apiUpload } from './apiClient';
import type {
  DocumentContentResponse,
  DocumentListResponse,
  DocumentStatus,
  DocumentView,
  IndexingJobView,
  UploadResponse,
} from '../types';

export function listDocuments(
  status?: DocumentStatus,
  signal?: AbortSignal
): Promise<DocumentListResponse> {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return apiGet<DocumentListResponse>(`/documents${query}`, signal);
}

export function getDocument(id: string, signal?: AbortSignal): Promise<DocumentView> {
  return apiGet<DocumentView>(`/documents/${id}`, signal);
}

export function getDocumentContent(
  id: string,
  signal?: AbortSignal
): Promise<DocumentContentResponse> {
  return apiGet<DocumentContentResponse>(`/documents/${id}/content`, signal);
}

export function uploadDocument(file: File): Promise<UploadResponse> {
  return apiUpload<UploadResponse>('/documents/upload', file);
}

export function deleteDocument(id: string): Promise<void> {
  return apiDelete(`/documents/${id}`);
}

export function reindexDocument(id: string): Promise<IndexingJobView> {
  return apiPost<IndexingJobView>(`/documents/${id}/reindex`, {});
}

export function documentDownloadUrl(id: string): string {
  return `${API_BASE_URL}/documents/${id}/download`;
}
