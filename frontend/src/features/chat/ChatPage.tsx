import { useEffect, useRef, useState } from 'react';

import { useChat, type ChatMessage } from '../../app/chatStore';
import type { ChatSource } from '../../types';

export function ChatPage(): JSX.Element {
  const {
    conversations,
    activeId,
    activeConversation,
    isStreaming,
    newConversation,
    selectConversation,
    deleteConversation,
    send,
  } = useChat();
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  const messages = activeConversation?.messages ?? [];
  // Only the active conversation's own streaming state blocks its input — other
  // chats (and new ones) remain usable while this one is working.
  const activeStreaming = isStreaming(activeId);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, activeId]);

  function onSubmit(event: React.FormEvent): void {
    event.preventDefault();
    const question = input.trim();
    if (!question || activeStreaming) return;
    send(question);
    setInput('');
  }

  return (
    <div className="flex h-[calc(100vh-9rem)] flex-col gap-3 md:flex-row">
      {/* Conversation list */}
      <aside className="shrink-0 md:w-60">
        <button
          onClick={newConversation}
          className="mb-2 w-full rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          + New chat
        </button>
        <ul className="max-h-40 space-y-1 overflow-y-auto md:max-h-full">
          {conversations.length === 0 && (
            <li className="px-1 py-2 text-xs text-slate-400 dark:text-slate-500">No conversations yet.</li>
          )}
          {conversations.map((conversation) => {
            const streaming = isStreaming(conversation.id);
            return (
              <li key={conversation.id}>
                <div
                  className={`group flex items-center justify-between rounded-md px-3 py-2 text-sm ${
                    conversation.id === activeId
                      ? 'bg-brand-50 text-brand-700 dark:bg-brand-600/20 dark:text-brand-100'
                      : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
                  }`}
                >
                  <button
                    className="flex min-w-0 flex-1 items-center gap-2 text-left"
                    onClick={() => selectConversation(conversation.id)}
                  >
                    {streaming && (
                      <span
                        aria-label="Working"
                        title="Working…"
                        className="h-2 w-2 shrink-0 animate-pulse rounded-full bg-brand-500"
                      />
                    )}
                    <span className="truncate">{conversation.title || 'Untitled'}</span>
                  </button>
                  <button
                    aria-label="Delete conversation"
                    className="ml-2 text-slate-400 opacity-0 hover:text-rose-500 group-hover:opacity-100"
                    onClick={() => deleteConversation(conversation.id)}
                  >
                    ✕
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      </aside>

      {/* Chat area */}
      <div className="flex min-h-0 flex-1 flex-col">
        <header className="mb-3">
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">AI Chat</h2>
            {activeStreaming && <TypingDots />}
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Grounded answers from your documents. Conversations are saved, keep streaming if you
            switch screens, and several can run at the same time.
          </p>
        </header>

        <div className="flex-1 space-y-4 overflow-y-auto rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          {messages.length === 0 && (
            <p className="py-10 text-center text-sm text-slate-400 dark:text-slate-500">
              Ask a question about your indexed documents.
            </p>
          )}
          {messages.map((message, index) => {
            const isLast = index === messages.length - 1;
            return (
              <div key={index} className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                    message.role === 'user'
                      ? 'bg-brand-600 text-white'
                      : 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100'
                  }`}
                >
                  {message.role === 'assistant' && !message.content && activeStreaming && isLast ? (
                    <TypingDots />
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                  {message.role === 'assistant' && <AssistantMessageExtras message={message} />}
                </div>
              </div>
            );
          })}
          <div ref={endRef} />
        </div>

        <form onSubmit={onSubmit} className="mt-3 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            disabled={activeStreaming}
            className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none disabled:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:disabled:bg-slate-800"
          />
          <button
            type="submit"
            disabled={activeStreaming || !input.trim()}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {activeStreaming ? 'Thinking…' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
}

/** Minimalist animated typing indicator shown while an answer is streaming. */
function TypingDots(): JSX.Element {
  return (
    <span className="inline-flex items-center gap-1 py-1" aria-label="Working">
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s] dark:bg-slate-500" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s] dark:bg-slate-500" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 dark:bg-slate-500" />
    </span>
  );
}

/** The "not grounded" note plus a collapsed, togglable Sources list. */
function AssistantMessageExtras({ message }: { message: ChatMessage }): JSX.Element | null {
  const hasSources = !!message.sources && message.sources.length > 0;
  if (hasSources) return <CollapsibleSources sources={message.sources!} />;
  if (message.grounded === false) {
    return (
      <p className="mt-1 text-[11px] italic text-slate-400 dark:text-slate-500">
        Not grounded in any document.
      </p>
    );
  }
  return null;
}

function CollapsibleSources({ sources }: { sources: ChatSource[] }): JSX.Element {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="inline-flex items-center gap-1 rounded-full border border-slate-300 px-2 py-0.5 text-[11px] font-medium text-slate-500 transition-colors hover:border-brand-400 hover:text-brand-600 dark:border-slate-600 dark:text-slate-400 dark:hover:text-brand-300"
      >
        <span className="text-[13px] leading-none">⌕</span>
        {open ? 'Hide sources' : `Sources (${sources.length})`}
      </button>
      {open && (
        <ul className="mt-2 space-y-0.5 border-t border-slate-200 pt-2 dark:border-slate-700">
          {sources.map((source, i) => (
            <li key={source.chunk_id} className="text-xs text-slate-500 dark:text-slate-400">
              [{i + 1}] {source.document_name}
              {source.page_number != null && ` · p.${source.page_number}`}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
