import { apiPost } from './apiClient';
import type { SemanticSearchResponse } from '../types';

export function semanticSearch(
  query: string,
  topK?: number,
  signal?: AbortSignal
): Promise<SemanticSearchResponse> {
  return apiPost<SemanticSearchResponse>(
    '/search/semantic',
    { query, top_k: topK ?? null },
    signal
  );
}
