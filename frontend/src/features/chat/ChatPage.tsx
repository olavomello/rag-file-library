import { useEffect, useRef, useState } from 'react';

import { useChat } from '../../app/chatStore';

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

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, activeId]);

  function onSubmit(event: React.FormEvent): void {
    event.preventDefault();
    const question = input.trim();
    if (!question || isStreaming) return;
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
          {conversations.map((conversation) => (
            <li key={conversation.id}>
              <div
                className={`group flex items-center justify-between rounded-md px-3 py-2 text-sm ${
                  conversation.id === activeId
                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-600/20 dark:text-brand-100'
                    : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
                }`}
              >
                <button className="flex-1 truncate text-left" onClick={() => selectConversation(conversation.id)}>
                  {conversation.title || 'Untitled'}
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
          ))}
        </ul>
      </aside>

      {/* Chat area */}
      <div className="flex min-h-0 flex-1 flex-col">
        <header className="mb-3">
          <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">AI Chat</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Grounded answers from your documents, with sources. Conversations are saved and keep
            streaming if you switch screens.
          </p>
        </header>

        <div className="flex-1 space-y-4 overflow-y-auto rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          {messages.length === 0 && (
            <p className="py-10 text-center text-sm text-slate-400 dark:text-slate-500">
              Ask a question about your indexed documents.
            </p>
          )}
          {messages.map((message, index) => (
            <div key={index} className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                  message.role === 'user'
                    ? 'bg-brand-600 text-white'
                    : 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100'
                }`}
              >
                <p className="whitespace-pre-wrap">
                  {message.content || (isStreaming ? '…' : '')}
                </p>
                {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                  <div className="mt-2 border-t border-slate-200 pt-2 dark:border-slate-700">
                    <p className="mb-1 text-[11px] font-semibold uppercase text-slate-400 dark:text-slate-500">Sources</p>
                    <ul className="space-y-0.5">
                      {message.sources.map((source, i) => (
                        <li key={source.chunk_id} className="text-xs text-slate-500 dark:text-slate-400">
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
                    <p className="mt-1 text-[11px] italic text-slate-400 dark:text-slate-500">
                      Not grounded in any document.
                    </p>
                  )}
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>

        <form onSubmit={onSubmit} className="mt-3 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            disabled={isStreaming}
            className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none disabled:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:disabled:bg-slate-800"
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {isStreaming ? 'Thinking…' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
}
