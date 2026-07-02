'use client'

import { useRef, useCallback, useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

type TTSState = 'idle' | 'loading' | 'playing' | 'error'

export function useTTS() {
  const [state, setState] = useState<TTSState>('idle')
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const blobUrlRef = useRef<string | null>(null)

  const isSupported = typeof window !== 'undefined' && typeof Audio !== 'undefined'

  const speak = useCallback(async (text: string, language: string = 'en') => {
    if (!text.trim()) return

    // Stop any current playback
    stop()

    setState('loading')

    try {
      const res = await fetch(`${API_URL}/chat/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim(), language }),
      })

      if (!res.ok) {
        throw new Error(`TTS failed: ${res.status}`)
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      blobUrlRef.current = url

      const audio = new Audio(url)
      audioRef.current = audio

      return new Promise<void>((resolve, reject) => {
        audio.onplay = () => setState('playing')
        audio.onended = () => {
          setState('idle')
          cleanup()
          resolve()
        }
        audio.onerror = (e) => {
          setState('error')
          cleanup()
          reject(new Error('Audio playback failed'))
        }

        audio.play().catch((err) => {
          setState('error')
          cleanup()
          reject(err)
        })
      })
    } catch (err: any) {
      setState('error')
      throw err
    }
  }, [])

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      audioRef.current = null
    }
    cleanup()
    setState('idle')
  }, [])

  const cleanup = useCallback(() => {
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current)
      blobUrlRef.current = null
    }
  }, [])

  return {
    state,
    isSupported,
    speak,
    stop,
  }
}
