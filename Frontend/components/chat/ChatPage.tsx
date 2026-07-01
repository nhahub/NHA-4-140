'use client'

import { Bot, MessageSquare, Sliders, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useChat } from '@/hooks/useChat'
import { useChatStore } from '@/store/chatStore'
import { ChatMessages } from './ChatMessages'
import { ChatInput } from './ChatInput'
import { useTranslations } from 'next-intl'

const conversationStarters = [
  'Find me a sedan under 500k EGP',
  'Show me cars in Cairo',
  'I want a car with low mileage',
  'Compare BMW and Mercedes',
  'What is the average price of a 2020 Toyota?',
]

export function ChatPage() {
  const t = useTranslations('chat')
  const { messages, isStreaming, sendMessage, stop } = useChat()
  const { sessionToken, clearMessages } = useChatStore()

  return (
    <div className="flex h-[calc(100vh-4rem)] max-w-7xl mx-auto">
      <aside className="hidden lg:flex flex-col w-80 border-r border-surface-border p-6 gap-6 overflow-y-auto">
        <div className="flex items-center gap-2">
          <Bot className="w-6 h-6 text-primary-500" />
          <h1 className="text-xl font-bold text-text-primary">{t('title') || 'AI Assistant'}</h1>
        </div>

        <p className="text-sm text-text-secondary leading-relaxed">
          {t('description') || 'Ask me anything about cars on the marketplace. I can help you find the perfect vehicle, compare options, and analyze prices.'}
        </p>

        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-1.5">
            <MessageSquare className="w-4 h-4" />
            {t('starters') || 'Try asking'}
          </h3>
          <div className="flex flex-wrap gap-2">
            {conversationStarters.map((starter) => (
              <button
                key={starter}
                onClick={() => sendMessage(starter)}
                disabled={isStreaming}
                className="text-xs px-3 py-1.5 rounded-full bg-surface-secondary text-text-secondary hover:bg-surface-border hover:text-text-primary transition-colors disabled:opacity-50"
              >
                {starter}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-auto pt-4 border-t border-surface-border">
          <h3 className="text-sm font-semibold text-text-primary mb-2 flex items-center gap-1.5">
            <Sliders className="w-4 h-4" />
            {t('preferences') || 'Your Preferences'}
          </h3>
          <p className="text-xs text-text-secondary">
            {t('preferences_hint') || 'Set your preferences to get better recommendations.'}
          </p>
        </div>
      </aside>

      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border lg:hidden">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary-500" />
            <span className="font-semibold text-text-primary">{t('title') || 'AI Assistant'}</span>
          </div>
          {messages.length > 0 && (
            <button
              onClick={clearMessages}
              className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors"
              aria-label={t('clear') || 'Clear chat'}
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="flex-1 overflow-hidden flex flex-col">
          <ChatMessages messages={messages} isStreaming={isStreaming} />
        </div>

        <div className="border-t border-surface-border">
          <ChatInput onSend={sendMessage} isStreaming={isStreaming} onStop={stop} />
        </div>
      </div>
    </div>
  )
}
