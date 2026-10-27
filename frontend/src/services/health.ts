import { apiGet, ApiError } from './apiClient';
import type { ComponentHealthResponse, LivenessResponse } from '../types';

export function fetchLiveness(signal?: AbortSignal): Promise<LivenessResponse> {
  return apiGet<LivenessResponse>('/health', signal);
}

/**
 * Component probes legitimately return HTTP 503 when a dependency is down.
 * We still want the parsed status body in that case, so 503 is treated as a
 * valid, non-throwing response.
 */
async function fetchComponentHealth(
  path: string,
  signal?: AbortSignal
): Promise<ComponentHealthResponse> {
  const response = await fetch(`/api/v1${path}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
    signal,
  });

  if (!response.ok && response.status !== 503) {
    throw new ApiError(`GET ${path} failed`, response.status);
  }

  return (await response.json()) as ComponentHealthResponse;
}

export function fetchOllamaHealth(signal?: AbortSignal): Promise<ComponentHealthResponse> {
  return fetchComponentHealth('/health/ollama', signal);
}

export function fetchChromaHealth(signal?: AbortSignal): Promise<ComponentHealthResponse> {
  return fetchComponentHealth('/health/chroma', signal);
}
