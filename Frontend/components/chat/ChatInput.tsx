'use client'

import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import { Send, Sparkles, Square } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTranslations } from 'next-intl'

interface ChatInputProps {
  onSend: (text: string) => void
  isStreaming: boolean
  onStop: () => void
}

export function ChatInput({ onSend, isStreaming, onStop }: ChatInputProps) {
  const t = useTranslations('chat')
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
    }
  }, [value])

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || isStreaming) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex items-end gap-2 p-4 bg-background-primary">
      <div className="flex-1 relative">
        <div className="absolute left-3 bottom-3 text-surface-border pointer-events-none">
          <Sparkles className="w-4 h-4" />
        </div>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('input_placeholder') || 'message the chatbot...'}
          rows={1}
          disabled={isStreaming}
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
          disabled={!value.trim()}
          className={cn(
            'flex items-center justify-center w-10 h-10 rounded-xl shrink-0 transition-colors',
            value.trim()
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
