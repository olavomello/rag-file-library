import { afterEach, describe, expect, it, vi } from 'vitest';

import { apiPostStream } from '../src/services/apiClient';
import type { ChatStreamEvent } from '../src/types';

function ndjsonResponse(lines: string[]): Response {
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(lines.join('\n') + '\n'));
      controller.close();
    },
  });
  return new Response(body, {
    status: 200,
    headers: { 'content-type': 'application/x-ndjson' },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe('apiPostStream', () => {
  it('yields each newline-delimited JSON event in order', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        ndjsonResponse([
          '{"type":"sources","grounded":true,"sources":[]}',
          '{"type":"token","text":"Hello "}',
          '{"type":"token","text":"world"}',
          '{"type":"done"}',
        ])
      )
    );

    const events: ChatStreamEvent[] = [];
    for await (const event of apiPostStream<ChatStreamEvent>('/chat/stream', { question: 'hi' })) {
      events.push(event);
    }

    expect(events.map((e) => e.type)).toEqual(['sources', 'token', 'token', 'done']);
    const text = events
      .filter((e): e is Extract<ChatStreamEvent, { type: 'token' }> => e.type === 'token')
      .map((e) => e.text)
      .join('');
    expect(text).toBe('Hello world');
  });
});
