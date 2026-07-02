'use client'

import { useState, useRef, useEffect, useCallback, type KeyboardEvent } from 'react'
import { Send, Sparkles, Square, Mic, MicOff, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTranslations } from 'next-intl'
import { useVoice } from '@/hooks/useVoice'

interface ChatInputProps {
  onSend: (text: string, language?: string) => void
  isStreaming: boolean
  onStop: () => void
}

export function ChatInput({ onSend, isStreaming, onStop }: ChatInputProps) {
  const t = useTranslations('chat')
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const {
    state: voiceState,
    isSupported: voiceSupported,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useVoice()

  const isRecording = voiceState === 'recording'
  const isProcessing = voiceState === 'processing'

  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
    }
  }, [value])

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
      {voiceSupported && (
        <button
          onClick={handleMicToggle}
          disabled={isDisabled}
          className={cn(
            'flex items-center justify-center w-10 h-10 rounded-xl shrink-0 transition-all',
            isRecording
              ? 'bg-danger text-white shadow-lg shadow-danger/50 scale-110 animate-pulse'
              : isDisabled
                ? 'bg-surface-secondary text-text-secondary cursor-not-allowed'
                : 'bg-surface-secondary text-text-primary hover:bg-surface-border'
          )}
          aria-label={isRecording ? (t('stop_recording') || 'Stop recording') : (t('start_recording') || 'Start recording')}
        >
          {isProcessing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : isRecording ? (
            <MicOff className="w-4 h-4" />
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
          placeholder={isRecording ? (t('recording') || 'Recording... speak now') : (t('input_placeholder') || 'message the chatbot...')}
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
    </div>
  )
}
