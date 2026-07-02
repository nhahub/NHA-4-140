'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { Home, Search, PlusCircle, MessageCircle, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useChatStore } from '@/store/chatStore'

const NAV_ITEMS = [
  { href: '/', label: 'home', icon: Home },
  { href: '/search', label: 'search', icon: Search },
  { href: '/ads/new', label: 'sell', icon: PlusCircle },
  { href: '/chat', label: 'chat', icon: MessageCircle },
  { href: '/profile', label: 'profile', icon: User },
]

export function MobileNav() {
  const pathname = usePathname()
  const t = useTranslations('nav')
  const { open: openChat } = useChatStore()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-surface border-t border-surface-border md:hidden safe-area-bottom">
      <div className="flex items-center justify-around h-14">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href ||
            (item.href === '/' && pathname === '/') ||
            (item.href !== '/' && pathname.startsWith(item.href))
          const Icon = item.icon

          if (item.href === '/chat') {
            return (
              <button
                key={item.href}
                onClick={() => openChat()}
                className={cn(
                  'flex flex-col items-center justify-center gap-0.5 px-3 py-1 rounded-lg transition-colors min-w-[64px]',
                  isActive
                    ? 'text-primary-500'
                    : 'text-text-muted hover:text-text-secondary'
                )}
              >
                <Icon className="w-5 h-5" />
                <span className="text-[10px] font-medium">{t(item.label as any) || item.label}</span>
              </button>
            )
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-col items-center justify-center gap-0.5 px-3 py-1 rounded-lg transition-colors min-w-[64px]',
                isActive
                  ? 'text-primary-500'
                  : 'text-text-muted hover:text-text-secondary'
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{t(item.label as any) || item.label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
