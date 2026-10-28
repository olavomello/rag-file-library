import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { ChatStreamEvent } from '../src/types';

const streamCalls = vi.hoisted(
  () => [] as { question: string; history: { role: string; content: string }[] }[]
);

vi.mock('../src/services/chat', () => ({
  streamChat: (
    question: string,
    history: { role: string; content: string }[] = []
  ): AsyncGenerator<ChatStreamEvent> => {
    streamCalls.push({ question, history });
    async function* gen(): AsyncGenerator<ChatStreamEvent> {
      yield { type: 'sources', grounded: true, sources: [] };
      yield { type: 'token', text: 'Hello ' };
      yield { type: 'token', text: 'world' };
      yield { type: 'done' };
    }
    return gen();
  },
}));

import { ChatProvider, useChat } from '../src/app/chatStore';

const wrapper = ({ children }: { children: React.ReactNode }): JSX.Element => (
  <ChatProvider>{children}</ChatProvider>
);

beforeEach(() => {
  localStorage.clear();
  streamCalls.length = 0;
});
afterEach(() => vi.clearAllMocks());

describe('chat store', () => {
  it('creates a conversation, streams the answer, and persists it', async () => {
    const { result } = renderHook(() => useChat(), { wrapper });

    act(() => result.current.send('How many vacation days?'));

    await waitFor(() => expect(result.current.isStreaming()).toBe(false));

    const conversation = result.current.activeConversation;
    expect(conversation).not.toBeNull();
    expect(conversation?.messages[0]?.content).toBe('How many vacation days?');
    expect(conversation?.messages[1]?.content).toBe('Hello world');
    expect(conversation?.title).toContain('vacation');

    // Persisted to localStorage for future sessions.
    const stored = JSON.parse(localStorage.getItem('privaterag.chats') ?? '[]');
    expect(stored).toHaveLength(1);
    expect(stored[0].messages[1].content).toBe('Hello world');
  });

  it('keeps multiple conversations and can delete one', async () => {
    const { result } = renderHook(() => useChat(), { wrapper });

    act(() => result.current.send('first question'));
    await waitFor(() => expect(result.current.isStreaming()).toBe(false));
    act(() => result.current.newConversation());
    act(() => result.current.send('second question'));
    await waitFor(() => expect(result.current.isStreaming()).toBe(false));

    expect(result.current.conversations).toHaveLength(2);

    const toDelete = result.current.conversations[0]!.id;
    act(() => result.current.deleteConversation(toDelete));
    expect(result.current.conversations).toHaveLength(1);
  });

  it('sends prior turns as history on a follow-up question', async () => {
    const { result } = renderHook(() => useChat(), { wrapper });

    act(() => result.current.send('Who is Olavo?'));
    await waitFor(() => expect(result.current.isStreaming()).toBe(false));
    act(() => result.current.send('Date of birth?'));
    await waitFor(() => expect(result.current.isStreaming()).toBe(false));

    // First call has no prior context; the follow-up carries the earlier turns.
    expect(streamCalls[0]?.history).toEqual([]);
    expect(streamCalls[1]?.question).toBe('Date of birth?');
    expect(streamCalls[1]?.history).toEqual([
      { role: 'user', content: 'Who is Olavo?' },
      { role: 'assistant', content: 'Hello world' },
    ]);
  });
});
