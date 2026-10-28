import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import { ApiError } from '../services/apiClient';
import { streamChat, type ChatHistoryMessage } from '../services/chat';
import type { ChatSource } from '../types';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  grounded?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: number;
  messages: ChatMessage[];
}

interface ChatContextValue {
  conversations: Conversation[];
  activeId: string | null;
  activeConversation: Conversation | null;
  /** True if the given conversation is streaming; defaults to the active one. */
  isStreaming: (id?: string | null) => boolean;
  /** Whether any conversation is currently streaming. */
  anyStreaming: boolean;
  newConversation: () => void;
  selectConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  send: (question: string) => void;
}

const STORAGE_KEY = 'privaterag.chats';
// How many prior messages to send as context for a follow-up question.
const HISTORY_LIMIT = 6;
const ChatContext = createContext<ChatContextValue | null>(null);

function uid(): string {
  try {
    return crypto.randomUUID();
  } catch {
    return `c-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }
}

function loadConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw);
    return Array.isArray(data) ? (data as Conversation[]) : [];
  } catch {
    return [];
  }
}

function replaceLastAssistant(
  messages: ChatMessage[],
  update: (message: ChatMessage) => ChatMessage
): ChatMessage[] {
  if (messages.length === 0) return messages;
  const last = messages[messages.length - 1];
  if (!last || last.role !== 'assistant') return messages;
  return [...messages.slice(0, -1), update(last)];
}

export function ChatProvider({ children }: { children: React.ReactNode }): JSX.Element {
  const [conversations, setConversations] = useState<Conversation[]>(loadConversations);
  const [activeId, setActiveId] = useState<string | null>(
    () => loadConversations()[0]?.id ?? null
  );
  // Each conversation streams independently so several can run at once.
  const [streamingIds, setStreamingIds] = useState<Set<string>>(() => new Set());

  const activeIdRef = useRef(activeId);
  const conversationsRef = useRef(conversations);
  const streamingIdsRef = useRef(streamingIds);
  useEffect(() => {
    activeIdRef.current = activeId;
  }, [activeId]);
  useEffect(() => {
    conversationsRef.current = conversations;
  }, [conversations]);

  // Persist conversations (per-viewer) so chats survive reloads and navigation.
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch {
      /* ignore unavailable storage */
    }
  }, [conversations]);

  // Update the streaming set through the ref so `send` can guard synchronously.
  const setStreaming = useCallback((id: string, on: boolean) => {
    const next = new Set(streamingIdsRef.current);
    if (on) next.add(id);
    else next.delete(id);
    streamingIdsRef.current = next;
    setStreamingIds(next);
  }, []);

  const updateLast = useCallback(
    (conversationId: string, update: (message: ChatMessage) => ChatMessage) => {
      setConversations((prev) =>
        prev.map((conversation) =>
          conversation.id === conversationId
            ? {
                ...conversation,
                messages: replaceLastAssistant(conversation.messages, update),
              }
            : conversation
        )
      );
    },
    []
  );

  const send = useCallback(
    (question: string) => {
      const text = question.trim();
      if (!text) return;

      let targetId = activeIdRef.current;
      if (!targetId) {
        targetId = uid();
        activeIdRef.current = targetId;
        setActiveId(targetId);
      }
      const conversationId = targetId;

      // Only one in-flight request per conversation; other chats stay free.
      if (streamingIdsRef.current.has(conversationId)) return;

      // Prior turns of THIS conversation, so a short follow-up stays on-subject.
      const existing = conversationsRef.current.find((c) => c.id === conversationId);
      const history: ChatHistoryMessage[] = (existing?.messages ?? [])
        .filter((m) => m.content.trim().length > 0)
        .slice(-HISTORY_LIMIT)
        .map((m) => ({ role: m.role, content: m.content }));

      setConversations((prev) => {
        const exists = prev.some((c) => c.id === conversationId);
        const base = exists
          ? prev
          : [
              { id: conversationId, title: text.slice(0, 60), createdAt: Date.now(), messages: [] },
              ...prev,
            ];
        return base.map((conversation) =>
          conversation.id === conversationId
            ? {
                ...conversation,
                title:
                  conversation.messages.length === 0 ? text.slice(0, 60) : conversation.title,
                messages: [
                  ...conversation.messages,
                  { role: 'user', content: text },
                  { role: 'assistant', content: '' },
                ],
              }
            : conversation
        );
      });

      setStreaming(conversationId, true);

      // The stream runs here, in the app-level provider, so it keeps going even
      // when the Chat page is unmounted (e.g. the user navigates elsewhere) and
      // independently of any other conversation that is streaming at the same time.
      void (async () => {
        try {
          for await (const event of streamChat(text, history)) {
            if (event.type === 'sources') {
              updateLast(conversationId, (m) => ({
                ...m,
                sources: event.sources,
                grounded: event.grounded,
              }));
            } else if (event.type === 'token') {
              updateLast(conversationId, (m) => ({ ...m, content: m.content + event.text }));
            } else if (event.type === 'error') {
              updateLast(conversationId, (m) => ({
                ...m,
                content: `${m.content}\n\n[error: ${event.detail}]`,
              }));
            }
          }
        } catch (error) {
          const detail =
            error instanceof ApiError ? error.detail ?? error.message : 'Chat request failed.';
          updateLast(conversationId, (m) => ({
            ...m,
            content: m.content || `[error: ${detail}]`,
          }));
        } finally {
          setStreaming(conversationId, false);
        }
      })();
    },
    [setStreaming, updateLast]
  );

  const newConversation = useCallback(() => setActiveId(null), []);
  const selectConversation = useCallback((id: string) => setActiveId(id), []);
  const deleteConversation = useCallback((id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    setActiveId((current) => (current === id ? null : current));
  }, []);

  const isStreaming = useCallback(
    (id?: string | null) => {
      const target = id === undefined ? activeIdRef.current : id;
      return target != null && streamingIds.has(target);
    },
    [streamingIds]
  );

  const value = useMemo<ChatContextValue>(
    () => ({
      conversations,
      activeId,
      activeConversation: conversations.find((c) => c.id === activeId) ?? null,
      isStreaming,
      anyStreaming: streamingIds.size > 0,
      newConversation,
      selectConversation,
      deleteConversation,
      send,
    }),
    [
      conversations,
      activeId,
      streamingIds,
      isStreaming,
      newConversation,
      selectConversation,
      deleteConversation,
      send,
    ]
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat(): ChatContextValue {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within ChatProvider');
  return context;
}
