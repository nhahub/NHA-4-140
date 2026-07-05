'use client'

import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import { useChatStore } from '@/store/chatStore'
import { api } from '@/lib/api'
import type { User } from '@/types/auth'

export function useAuth() {
  const { user, isLoading, setUser, setLoading, clear } = useAuthStore()

  useEffect(() => {
    if (isLoading) {
      api.get<User>('/users/me')
        .then(setUser)
        .catch(() => clear())
    }
  }, [])

  const clearChatSession = () => {
    localStorage.removeItem('chat_session_token')
    useChatStore.getState().clearMessages()
    useChatStore.getState().setSessionToken(null)
  }

  const login = async (email: string, password: string) => {
    clearChatSession()
    const res = await api.post<{ user: User }>('/auth/login', { email, password })
    setUser(res.user)
    return res.user
  }

  const register = async (data: { name: string; email: string; phone: string; password: string }) => {
    clearChatSession()
    const res = await api.post<{ user: User }>('/auth/register', data)
    setUser(res.user)
    return res.user
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } catch {}
    clearChatSession()
    clear()
  }

  return { user, isLoading, login, register, logout, isAuthenticated: !!user }
}
