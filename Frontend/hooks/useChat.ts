'use client'

import { useCallback, useEffect, useRef } from 'react'
import { useChatStore } from '@/store/chatStore'
import { useSSE } from './useSSE'
import { useTTS } from './useTTS'
import { api } from '@/lib/api'
import type { ChatMessage, ChatHistory } from '@/types/chat'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export function useChat() {
  const {
    messages, isStreaming, sessionToken, contextAdId,
    addMessage, appendToken, setStreaming, setSessionToken, clearMessages,
  } = useChatStore()

  const { start, stop } = useSSE()
  const { speak: speakTTS, stop: stopTTS } = useTTS()
  const responseTextRef = useRef('')
  const responseLangRef = useRef<string>('en')

  // Restore session from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('chat_session_token')
    if (savedToken) {
      setSessionToken(savedToken)
      api.get<ChatHistory>(`/chat/history/${savedToken}`)
        .then((history) => {
          if (history.messages.length > 0) {
            clearMessages()
            for (const m of history.messages) {
              addMessage({
                role: m.role as 'user' | 'assistant' | 'system',
                content: m.content,
                type: 'text',
                created_at: m.created_at,
              })
            }
          }
        })
        .catch(() => {
          localStorage.removeItem('chat_session_token')
          setSessionToken(null)
        })
    }
  }, [])

  // Persist session token to localStorage whenever it changes
  useEffect(() => {
    if (sessionToken) {
      localStorage.setItem('chat_session_token', sessionToken)
    }
  }, [sessionToken])

  const ensureSession = useCallback(async (token?: string): Promise<string> => {
    const res = await api.post<{ session_token: string; is_new: boolean }>(
      '/chat/session',
      { context_ad_id: contextAdId }
    )
    const t = res.session_token
    setSessionToken(t)
    localStorage.setItem('chat_session_token', t)
    return t
  }, [contextAdId, setSessionToken])

  const sendMessage = useCallback(async (text: string, language?: string) => {
    if (!text.trim() || isStreaming) return

    stopTTS()
    responseTextRef.current = ''
    responseLangRef.current = language || 'en'

    const token = sessionToken
      ? sessionToken
      : await ensureSession()

    const userMsg: Omit<ChatMessage, 'id'> = {
      role: 'user',
      content: text,
      type: 'text',
    }
    addMessage(userMsg)
    setStreaming(true)

    await start(
      `${API_URL}/chat/message`,
      {
        session_token: token,
        message: text,
        context_ad_id: contextAdId,
      },
      {
        onEvent: (event) => {
          switch (event.type) {
            case 'token':
              appendToken(event.content)
              responseTextRef.current += event.content
              break
            case 'cars':
              addMessage({
                role: 'assistant',
                content: '',
                type: 'cars',
                cars: event.content,
              })
              break
            case 'similar_cars':
              addMessage({
                role: 'assistant',
                content: '',
                type: 'similar_cars',
                similar_cars: event.content,
              })
              break
            case 'price_analysis':
              addMessage({
                role: 'assistant',
                content: '',
                type: 'price_analysis',
                price_analysis: event.content,
              })
              break
            case 'new_match':
              addMessage({
                role: 'assistant',
                content: 'New listings matching your preferences!',
                type: 'new_match',
                cars: event.content,
              })
              break
            case 'status':
              addMessage({
                role: 'system',
                content: event.content,
                type: 'status',
              })
              break
            case 'error':
              addMessage({
                role: 'system',
                content: event.content,
                type: 'error',
              })
              break
          }
        },
        onDone: () => {
          setStreaming(false)
          // Speak the accumulated response
          const responseText = responseTextRef.current.trim()
          if (responseText) {
            speakTTS(responseText, responseLangRef.current).catch(() => {})
          }
        },
        onError: (err) => {
          addMessage({
            role: 'system',
            content: err,
            type: 'error',
          })
          setStreaming(false)
        },
      }
    )
  }, [sessionToken, contextAdId, isStreaming, speakTTS, stopTTS])

  return { messages, isStreaming, sendMessage, stop }
}
