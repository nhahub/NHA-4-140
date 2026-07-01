'use client'

import { X, Bot } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useChatStore } from '@/store/chatStore'
import { ChatMessages } from './ChatMessages'
import { ChatInput } from './ChatInput'
import { useChat } from '@/hooks/useChat'

export function ChatDrawer() {
  const { isOpen, close } = useChatStore()
  const { messages, isStreaming, sendMessage, stop } = useChat()

  if (!isOpen) return null

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
        onClick={close}
      />
      <div
        className={cn(
          'fixed z-50 top-0 bottom-0',
          'ltr:right-0 rtl:left-0',
          'w-full sm:w-[420px]',
          'bg-background-primary border-l border-surface-border',
          'flex flex-col shadow-2xl',
          'animate-in slide-in-from-right',
          'rtl:animate-in rtl:slide-in-from-left'
        )}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary-500" />
            <span className="font-semibold text-text-primary">AI Assistant</span>
          </div>
          <button
            onClick={close}
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors"
            aria-label="Close chat"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-hidden flex flex-col">
          <ChatMessages messages={messages} isStreaming={isStreaming} />
        </div>

        <div className="border-t border-surface-border">
          <ChatInput onSend={sendMessage} isStreaming={isStreaming} onStop={stop} />
        </div>
      </div>
    </>
  )
}
