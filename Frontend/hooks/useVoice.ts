'use client'

import { useState, useRef, useCallback } from 'react'
import { api } from '@/lib/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

type VoiceState = 'idle' | 'recording' | 'processing' | 'error'

interface VoiceResult {
  text: string
  language: string
}

export function useVoice() {
  const [state, setState] = useState<VoiceState>('idle')
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)

  const isSupported = typeof window !== 'undefined' &&
    typeof navigator.mediaDevices?.getUserMedia === 'function' &&
    typeof MediaRecorder !== 'undefined'

  const startRecording = useCallback(async (): Promise<void> => {
    setError(null)
    setState('recording')
    chunksRef.current = []

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4'

      const recorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.start()
    } catch (err: any) {
      setState('error')
      setError(err.message || 'Microphone access denied')
      throw err
    }
  }, [])

  const stopRecording = useCallback(async (): Promise<VoiceResult> => {
    const recorder = mediaRecorderRef.current
    const stream = streamRef.current

    if (!recorder || recorder.state === 'inactive') {
      setState('error')
      setError('No active recording')
      throw new Error('No active recording')
    }

    setState('processing')

    return new Promise((resolve, reject) => {
      recorder.onstop = async () => {
        // Stop all tracks
        if (stream) {
          stream.getTracks().forEach((t) => t.stop())
          streamRef.current = null
        }

        const blob = new Blob(chunksRef.current, { type: recorder.mimeType })
        chunksRef.current = []

        try {
          const formData = new FormData()
          formData.append('audio', blob, 'recording.webm')

          const result = await fetch(`${API_URL}/chat/stt`, {
            method: 'POST',
            body: formData,
          })

          if (!result.ok) {
            const errText = await result.text().catch(() => 'STT failed')
            throw new Error(errText)
          }

          const data = await result.json()
          setState('idle')
          resolve({ text: data.text, language: data.language })
        } catch (err: any) {
          setState('error')
          setError(err.message || 'Transcription failed')
          reject(err)
        }
      }

      recorder.stop()
    })
  }, [])

  const cancelRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current
    const stream = streamRef.current

    if (recorder && recorder.state !== 'inactive') {
      recorder.ondataavailable = null
      recorder.onstop = null
      recorder.stop()
    }

    if (stream) {
      stream.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }

    chunksRef.current = []
    mediaRecorderRef.current = null
    setState('idle')
    setError(null)
  }, [])

  return {
    state,
    error,
    isSupported,
    startRecording,
    stopRecording,
    cancelRecording,
  }
}
