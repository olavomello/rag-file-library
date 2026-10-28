export type HealthStatusValue = 'ok' | 'unavailable' | 'error';

export interface LivenessResponse {
  status: string;
  app_name: string;
  app_env: string;
  version: string;
}

export interface ComponentHealthResponse {
  component: string;
  status: HealthStatusValue;
  detail: string | null;
  metadata: Record<string, string>;
}

export type DocumentStatus =
  | 'uploaded'
  | 'pending'
  | 'processing'
  | 'indexed'
  | 'failed'
  | 'deleting';

export interface DocumentView {
  id: string;
  original_name: string;
  mime_type: string;
  extension: string;
  size_bytes: number;
  checksum_sha256: string;
  status: DocumentStatus;
  chunk_count: number;
  created_at: string;
  updated_at: string;
  indexed_at: string | null;
  error_message: string | null;
}

export interface DocumentListResponse {
  items: DocumentView[];
  total: number;
}

export interface UploadResponse {
  document: DocumentView;
  is_duplicate: boolean;
}

export interface DocumentContentResponse {
  document_id: string;
  content: string;
  char_count: number;
}

export interface IndexingJobView {
  id: string;
  document_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  retry_count: number;
}

export interface SearchResultItem {
  document_id: string;
  document_name: string;
  chunk_id: string;
  excerpt: string;
  distance: number;
  page_number: number | null;
  metadata: Record<string, string>;
}

export interface SemanticSearchResponse {
  query: string;
  count: number;
  results: SearchResultItem[];
}

export interface ChatSource {
  document_id: string;
  document_name: string;
  chunk_id: string;
  page_number: number | null;
}

export interface ChatResponse {
  answer: string;
  grounded: boolean;
  sources: ChatSource[];
}

export type ChatStreamEvent =
  | { type: 'sources'; grounded: boolean; sources: ChatSource[] }
  | { type: 'token'; text: string }
  | { type: 'error'; detail: string }
  | { type: 'done' };

export interface DashboardStats {
  total_documents: number;
  uploaded: number;
  pending: number;
  processing: number;
  indexed: number;
  failed: number;
  deleting: number;
  total_chunks: number;
  active_jobs: number;
  generation_model: string;
  embedding_model: string;
}

export interface SettingsView {
  app_name: string;
  app_env: string;
  generation_model: string;
  embedding_model: string;
  temperature: number;
  max_output_tokens: number;
  context_window: number;
  chunk_size: number;
  chunk_overlap: number;
  search_top_k: number;
  rag_max_context_chunks: number;
  rag_max_context_chars: number;
  max_upload_size_mb: number;
  indexing_concurrency: number;
  generation_concurrency: number;
  ocr_enabled: boolean;
}

export type SettingsUpdate = Partial<
  Pick<
    SettingsView,
    | 'generation_model'
    | 'embedding_model'
    | 'temperature'
    | 'max_output_tokens'
    | 'context_window'
    | 'chunk_size'
    | 'chunk_overlap'
    | 'search_top_k'
    | 'rag_max_context_chunks'
    | 'rag_max_context_chars'
    | 'max_upload_size_mb'
    | 'indexing_concurrency'
    | 'generation_concurrency'
    | 'ocr_enabled'
  >
>;

export interface SettingsUpdateResponse {
  settings: SettingsView;
  requires_restart: boolean;
  requires_reindex: boolean;
  message: string;
}

export interface ModelsStatus {
  generation_model: string;
  embedding_model: string;
  ollama_available: boolean;
  generation_available: boolean;
  embedding_available: boolean;
}
