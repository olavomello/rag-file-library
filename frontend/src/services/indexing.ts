import { apiGet } from './apiClient';
import type { IndexingJobView } from '../types';

export function listIndexingJobs(signal?: AbortSignal): Promise<{ items: IndexingJobView[] }> {
  return apiGet<{ items: IndexingJobView[] }>('/indexing/jobs', signal);
}
