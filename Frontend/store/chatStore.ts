import { create } from 'zustand'
import type { ChatMessage } from '@/types/chat'

function generateId(): string {
  return Math.random().toString(36).substring(2, 11)
}

interface ChatState {
  isOpen: boolean
  sessionToken: string | null
  contextAdId: string | null
  messages: ChatMessage[]
  isStreaming: boolean
  pendingAssistantMessage: string

  open: (contextAdId?: string) => void
  close: () => void
  addMessage: (msg: Omit<ChatMessage, 'id'>) => void
  appendToken: (token: string) => void
  setStreaming: (val: boolean) => void
  setSessionToken: (token: string) => void
  setContextAdId: (id: string | null) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  isOpen: false,
  sessionToken: null,
  contextAdId: null,
  messages: [],
  isStreaming: false,
  pendingAssistantMessage: '',

  open: (contextAdId) => {
    const state = get()
    if (contextAdId) {
      set({ contextAdId })
    }
    set({ isOpen: true })
  },

  close: () => set({ isOpen: false }),

  addMessage: (msg) => {
    const newMsg: ChatMessage = { id: generateId(), ...msg }
    if (msg.role === 'assistant' && msg.content) {
      set((state) => ({
        messages: [...state.messages, newMsg],
        pendingAssistantMessage: '',
      }))
    } else {
      set((state) => ({
        messages: [...state.messages, newMsg],
      }))
    }
  },

  appendToken: (token) => {
    set((state) => {
      const newPending = state.pendingAssistantMessage + token
      const messages = [...state.messages]
      const lastMsg = messages[messages.length - 1]
      if (lastMsg && lastMsg.role === 'assistant' && lastMsg.type === 'text') {
        messages[messages.length - 1] = { ...lastMsg, content: lastMsg.content + token }
        return { messages, pendingAssistantMessage: newPending }
      }
      const newMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: token,
        type: 'text',
      }
      return { messages: [...messages, newMsg], pendingAssistantMessage: newPending }
    })
  },

  setStreaming: (isStreaming) => set({ isStreaming }),

  setSessionToken: (sessionToken) => set({ sessionToken }),

  setContextAdId: (contextAdId) => set({ contextAdId }),

  clearMessages: () => set({ messages: [], pendingAssistantMessage: '' }),
}))
