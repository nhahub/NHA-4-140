'use client'

import { useEffect, useRef } from 'react'
import { Bot, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ChatCarCard } from './ChatCarCard'
import { useTranslations } from 'next-intl'
import type { ChatMessage } from '@/types/chat'

interface ChatMessagesProps {
  messages: ChatMessage[]
  isStreaming: boolean
}

function PriceAnalysisCard({ data }: { data: any }) {
  const t = useTranslations('chat')
  return (
    <div className="flex gap-3 p-3 rounded-lg bg-surface-secondary min-w-[200px]">
      {data.min != null && (
        <div className="flex-1 text-center">
          <p className="text-xs text-text-secondary">{t('min_price') || 'Min'}</p>
          <p className="text-sm font-semibold text-text-primary">{data.min.toLocaleString()} EGP</p>
        </div>
      )}
      {data.max != null && (
        <div className="flex-1 text-center">
          <p className="text-xs text-text-secondary">{t('max_price') || 'Max'}</p>
          <p className="text-sm font-semibold text-text-primary">{data.max.toLocaleString()} EGP</p>
        </div>
      )}
      {data.recommended != null && (
        <div className="flex-1 text-center">
          <p className="text-xs text-text-secondary">{t('recommended_price') || 'Recommended'}</p>
          <p className="text-sm font-semibold text-primary-500">{data.recommended.toLocaleString()} EGP</p>
        </div>
      )}
    </div>
  )
}

export function ChatMessages({ messages, isStreaming }: ChatMessagesProps) {
  const t = useTranslations('chat')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <Bot className="w-12 h-12 text-surface-border mx-auto mb-3" />
          <p className="text-text-secondary text-sm">{t('start_message') || 'How can I help you find a car today?'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-surface-border hover:scrollbar-thumb-text-secondary">
      {messages.map((msg) => {
        if (msg.role === 'system' || msg.role === 'user' || msg.role === 'assistant') {
          const isUser = msg.role === 'user'
          return (
            <div
              key={msg.id}
              className={cn(
                'flex gap-2',
                isUser ? 'justify-end' : msg.type === 'status' || msg.type === 'error' ? 'justify-center' : 'justify-start'
              )}
            >
              {!isUser && msg.type !== 'status' && msg.type !== 'error' && (
                <div className="w-7 h-7 rounded-full bg-surface-secondary flex items-center justify-center shrink-0 mt-1">
                  <Bot className="w-4 h-4 text-text-secondary" />
                </div>
              )}

              <div
                className={cn(
                  'max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                  isUser
                    ? 'bg-primary-500 text-white rounded-br-md'
                    : msg.type === 'status'
                      ? 'text-text-secondary italic text-xs text-center bg-transparent px-2 py-1'
                      : msg.type === 'error'
                        ? 'bg-danger/10 text-danger text-xs text-center px-3 py-1.5'
                        : 'bg-surface-secondary text-text-primary rounded-bl-md'
                )}
              >
                {msg.content}
              </div>

              {isUser && (
                <div className="w-7 h-7 rounded-full bg-primary-500 flex items-center justify-center shrink-0 mt-1">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          )
        }

        if (msg.type === 'cars' && msg.cars) {
          return (
            <div key={msg.id} className="space-y-2">
              <p className="text-sm text-text-secondary px-1">{t('found_cars') || 'Here are some cars that match:'}</p>
              <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
                {msg.cars.map((car: any) => (
                  <ChatCarCard key={car.id} car={car} />
                ))}
              </div>
            </div>
          )
        }

        if (msg.type === 'similar_cars' && msg.similar_cars) {
          return (
            <div key={msg.id} className="space-y-2">
              <p className="text-sm text-text-secondary px-1">{t('similar_cars') || 'Similar cars:'}</p>
              <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
                {msg.similar_cars.map((car: any) => (
                  <ChatCarCard key={car.id} car={car} />
                ))}
              </div>
            </div>
          )
        }

        if (msg.type === 'price_analysis' && msg.price_analysis) {
          return (
            <div key={msg.id} className="space-y-2">
              <p className="text-sm text-text-secondary px-1">{t('price_analysis') || 'Price Analysis'}</p>
              <PriceAnalysisCard data={msg.price_analysis} />
            </div>
          )
        }

        if (msg.type === 'new_match' && msg.cars) {
          return (
            <div key={msg.id} className="space-y-2 p-3 rounded-lg bg-primary-500/10 border border-primary-500/20">
              <p className="text-sm font-semibold text-primary-500">{t('new_match') || 'New listings found!'}</p>
              <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
                {msg.cars.map((car: any) => (
                  <ChatCarCard key={car.id} car={car} />
                ))}
              </div>
            </div>
          )
        }

        return null
      })}

      {isStreaming && (
        <div className="flex items-center gap-2 text-text-secondary px-1">
          <div className="flex gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-text-secondary animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-text-secondary animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-text-secondary animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span className="text-xs">{t('thinking') || 'Thinking...'}</span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
