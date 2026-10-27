import { useState } from 'react';

import { streamChat } from '../../services/chat';
import { ApiError } from '../../services/apiClient';
import type { ChatSource } from '../../types';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  grounded?: boolean;
}

export function ChatPage(): JSX.Element {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);

  function updateLast(update: (m: Message) => Message): void {
    setMessages((prev) => {
      if (prev.length === 0) return prev;
      const next = [...prev];
      const last = next[next.length - 1];
      if (!last) return prev;
      next[next.length - 1] = update(last);
      return next;
    });
  }

  async function onSubmit(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    const question = input.trim();
    if (!question || busy) return;

    setInput('');
    setBusy(true);
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: question },
      { role: 'assistant', content: '' },
    ]);

    try {
      for await (const event_ of streamChat(question)) {
        if (event_.type === 'sources') {
          updateLast((m) => ({ ...m, sources: event_.sources, grounded: event_.grounded }));
        } else if (event_.type === 'token') {
          updateLast((m) => ({ ...m, content: m.content + event_.text }));
        } else if (event_.type === 'error') {
          updateLast((m) => ({ ...m, content: m.content + `\n\n[error: ${event_.detail}]` }));
        }
      }
    } catch (error) {
      const detail = error instanceof ApiError ? error.detail ?? error.message : 'Chat failed.';
      updateLast((m) => ({ ...m, content: m.content || `[error: ${detail}]` }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">AI Chat</h2>
          <p className="text-sm text-slate-500">Grounded answers from your documents, with sources.</p>
        </div>
        {messages.length > 0 && (
          <button
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
            onClick={() => setMessages([])}
          >
            New conversation
          </button>
        )}
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        {messages.length === 0 && (
          <p className="py-10 text-center text-sm text-slate-400">
            Ask a question about your indexed documents.
          </p>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                message.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : 'bg-slate-100 text-slate-800'
              }`}
            >
              <p className="whitespace-pre-wrap">
                {message.content || (busy ? '…' : '')}
              </p>
              {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                <div className="mt-2 border-t border-slate-200 pt-2">
                  <p className="mb-1 text-[11px] font-semibold uppercase text-slate-400">Sources</p>
                  <ul className="space-y-0.5">
                    {message.sources.map((source, i) => (
                      <li key={source.chunk_id} className="text-xs text-slate-500">
                        [{i + 1}] {source.document_name}
                        {source.page_number != null && ` · p.${source.page_number}`}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {message.role === 'assistant' &&
                message.grounded === false &&
                (!message.sources || message.sources.length === 0) && (
                  <p className="mt-1 text-[11px] italic text-slate-400">
                    Not grounded in any document.
                  </p>
                )}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={onSubmit} className="mt-4 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          disabled={busy}
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none disabled:bg-slate-50"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {busy ? 'Thinking…' : 'Send'}
        </button>
      </form>
    </div>
  );
}
