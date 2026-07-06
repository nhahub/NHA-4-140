'use client'

import { useState, useRef, useEffect, useCallback, type KeyboardEvent } from 'react'
import { Send, Sparkles, Square, Mic, MicOff, Loader2 } from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { useTranslations } from 'next-intl'
import { useVoice } from '@/hooks/useVoice'
import { useAudioLevel } from '@/hooks/useAudioLevel'
import { LiveWaveform } from './LiveWaveform'

interface ChatInputProps {
  onSend: (text: string, language?: string) => void
  isStreaming: boolean
  onStop: () => void
}

export function ChatInput({ onSend, isStreaming, onStop }: ChatInputProps) {
  const t = useTranslations('chat')
  const [value, setValue] = useState('')
  const [recordingTime, setRecordingTime] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const {
    state: voiceState,
    isSupported: voiceSupported,
    stream,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useVoice()
  const amplitude = useAudioLevel(stream)

  const isRecording = voiceState === 'recording'
  const isProcessing = voiceState === 'processing'

  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
    }
  }, [value])

  useEffect(() => {
    if (isRecording) {
      setRecordingTime(0)
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1)
      }, 1000)
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [isRecording])

  const formatTime = (seconds: number): string => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }

  const handleSend = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || isStreaming) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, isStreaming, onSend])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!isRecording) handleSend()
    }
  }

  const handleMicToggle = useCallback(async () => {
    if (isRecording) {
      try {
        const result = await stopRecording()
        if (result.text.trim()) {
          onSend(result.text, result.language)
        }
      } catch {
        // Error handled by useVoice state
      }
    } else {
      try {
        await startRecording()
      } catch {
        // Error handled by useVoice state
      }
    }
  }, [isRecording, startRecording, stopRecording, onSend])

  const isDisabled = isStreaming || isProcessing

  return (
    <div className="flex items-end gap-2 p-4 bg-background-primary">
      <AnimatePresence mode="wait">
        {isRecording ? (
          <motion.div
            key="recording"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.2 }}
            className="flex items-center gap-3 flex-1 h-10 px-3 rounded-xl bg-danger/5 border border-danger/20"
          >
            <div className="flex items-center gap-2 shrink-0">
              <span className="w-2 h-2 rounded-full bg-danger animate-pulse" />
              <span className="text-sm tabular-nums text-text-primary font-medium min-w-[44px]">
                {formatTime(recordingTime)}
              </span>
            </div>

            <div className="flex-1 flex items-center justify-center overflow-hidden">
              <LiveWaveform amplitude={amplitude} />
            </div>

            <button
              onClick={handleMicToggle}
              className="flex items-center justify-center w-8 h-8 rounded-lg bg-danger text-white hover:bg-danger/90 transition-colors shrink-0"
              aria-label={t('stop_recording') || 'Stop recording'}
            >
              <Square className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        ) : (
          <motion.div
            key="idle"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="flex items-end gap-2 flex-1"
          >
            {voiceSupported && (
              <button
                onClick={handleMicToggle}
                disabled={isDisabled}
                className={cn(
                  'flex items-center justify-center w-10 h-10 rounded-xl shrink-0 transition-all',
                  isProcessing
                    ? 'bg-surface-secondary text-text-secondary cursor-not-allowed'
                    : 'bg-surface-secondary text-text-primary hover:bg-surface-border'
                )}
                aria-label={
                  isRecording
                    ? (t('stop_recording') || 'Stop recording')
                    : (t('start_recording') || 'Start recording')
                }
              >
                {isProcessing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Mic className="w-4 h-4" />
                )}
              </button>
            )}

            <div className="flex-1 relative">
              <div className="absolute left-3 bottom-3 text-surface-border pointer-events-none">
                <Sparkles className="w-4 h-4" />
              </div>
              <textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  isRecording
                    ? (t('recording') || 'Recording... speak now')
                    : (t('input_placeholder') || 'message the chatbot...')
                }
                rows={1}
                disabled={isDisabled || isRecording}
                className={cn(
                  'w-full resize-none rounded-xl border border-surface-border',
                  'bg-surface-secondary text-text-primary placeholder:text-text-secondary',
                  'pl-10 pr-4 py-3 text-sm',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'transition-colors'
                )}
                style={{ maxHeight: '120px' }}
              />
            </div>

            {isStreaming ? (
              <button
                onClick={onStop}
                className="flex items-center justify-center w-10 h-10 rounded-xl bg-danger text-white hover:opacity-90 transition-opacity shrink-0"
                aria-label={t('stop') || 'Stop'}
              >
                <Square className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!value.trim() || isRecording}
                className={cn(
                  'flex items-center justify-center w-10 h-10 rounded-xl shrink-0 transition-colors',
                  value.trim() && !isRecording
                    ? 'bg-primary-500 text-white hover:bg-primary-600'
                    : 'bg-surface-secondary text-text-secondary cursor-not-allowed'
                )}
                aria-label={t('send') || 'Send'}
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
