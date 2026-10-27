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
import { streamChat } from '../services/chat';
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
  isStreaming: boolean;
  newConversation: () => void;
  selectConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  send: (question: string) => void;
}

const STORAGE_KEY = 'privaterag.chats';
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
  const [streamingId, setStreamingId] = useState<string | null>(null);

  const activeIdRef = useRef(activeId);
  const streamingRef = useRef(false);
  useEffect(() => {
    activeIdRef.current = activeId;
  }, [activeId]);

  // Persist conversations (per-viewer) so chats survive reloads and navigation.
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch {
      /* ignore unavailable storage */
    }
  }, [conversations]);

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
      if (!text || streamingRef.current) return;

      let targetId = activeIdRef.current;
      if (!targetId) {
        targetId = uid();
        activeIdRef.current = targetId;
        setActiveId(targetId);
      }
      const conversationId = targetId;

      setConversations((prev) => {
        const exists = prev.some((c) => c.id === conversationId);
        const base = exists
          ? prev
          : [{ id: conversationId, title: text.slice(0, 60), createdAt: Date.now(), messages: [] }, ...prev];
        return base.map((conversation) =>
          conversation.id === conversationId
            ? {
                ...conversation,
                title: conversation.messages.length === 0 ? text.slice(0, 60) : conversation.title,
                messages: [
                  ...conversation.messages,
                  { role: 'user', content: text },
                  { role: 'assistant', content: '' },
                ],
              }
            : conversation
        );
      });

      streamingRef.current = true;
      setStreamingId(conversationId);

      // The stream runs here, in the app-level provider, so it keeps going even
      // when the Chat page is unmounted (e.g. the user navigates elsewhere).
      void (async () => {
        try {
          for await (const event of streamChat(text)) {
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
          streamingRef.current = false;
          setStreamingId(null);
        }
      })();
    },
    [updateLast]
  );

  const newConversation = useCallback(() => setActiveId(null), []);
  const selectConversation = useCallback((id: string) => setActiveId(id), []);
  const deleteConversation = useCallback((id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    setActiveId((current) => (current === id ? null : current));
  }, []);

  const value = useMemo<ChatContextValue>(
    () => ({
      conversations,
      activeId,
      activeConversation: conversations.find((c) => c.id === activeId) ?? null,
      isStreaming: streamingId !== null,
      newConversation,
      selectConversation,
      deleteConversation,
      send,
    }),
    [conversations, activeId, streamingId, newConversation, selectConversation, deleteConversation, send]
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat(): ChatContextValue {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within ChatProvider');
  return context;
}
