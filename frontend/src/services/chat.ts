import { apiPost, apiPostStream } from './apiClient';
import type { ChatResponse, ChatStreamEvent } from '../types';

export function askChat(
  question: string,
  topK?: number,
  signal?: AbortSignal
): Promise<ChatResponse> {
  return apiPost<ChatResponse>('/chat', { question, top_k: topK ?? null }, signal);
}

export function streamChat(
  question: string,
  topK?: number,
  signal?: AbortSignal
): AsyncGenerator<ChatStreamEvent> {
  return apiPostStream<ChatStreamEvent>(
    '/chat/stream',
    { question, top_k: topK ?? null },
    signal
  );
}
