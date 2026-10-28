import { apiPost, apiPostStream } from './apiClient';
import type { ChatResponse, ChatStreamEvent } from '../types';

/** A prior turn sent so the backend can keep follow-up questions on-subject. */
export interface ChatHistoryMessage {
  role: 'user' | 'assistant';
  content: string;
}

export function askChat(
  question: string,
  history: ChatHistoryMessage[] = [],
  topK?: number,
  signal?: AbortSignal
): Promise<ChatResponse> {
  return apiPost<ChatResponse>(
    '/chat',
    { question, history, top_k: topK ?? null },
    signal
  );
}

export function streamChat(
  question: string,
  history: ChatHistoryMessage[] = [],
  topK?: number,
  signal?: AbortSignal
): AsyncGenerator<ChatStreamEvent> {
  return apiPostStream<ChatStreamEvent>(
    '/chat/stream',
    { question, history, top_k: topK ?? null },
    signal
  );
}
