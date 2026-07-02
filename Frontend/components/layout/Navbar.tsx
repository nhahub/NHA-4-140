'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { PlusCircle, MessageCircle, User, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { LanguageToggle } from '@/components/ui/LanguageToggle'
import { useAuthStore } from '@/store/authStore'
import { useChatStore } from '@/store/chatStore'

export function Navbar() {
  const t = useTranslations('nav')
  const { user } = useAuthStore()
  const { open: openChat } = useChatStore()

  return (
    <nav className="sticky top-0 z-40 bg-surface border-b border-surface-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <Image src="/logo.svg" alt="CarsMarket" width={32} height={32} className="shrink-0" />
              <span className="text-lg font-bold text-text-primary">CarsMarket</span>
            </Link>

            <div className="hidden md:flex items-center gap-1">
              <Link href="/" className="px-3 py-2 text-sm text-text-secondary hover:text-text-primary rounded-lg hover:bg-surface-secondary transition-colors">
                {t('browse')}
              </Link>
              <Link href="/ads/new" className="px-3 py-2 text-sm text-text-secondary hover:text-text-primary rounded-lg hover:bg-surface-secondary transition-colors">
                {t('sell')}
              </Link>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => openChat()}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-text-secondary hover:text-text-primary rounded-lg hover:bg-surface-secondary transition-colors"
            >
              <MessageCircle className="w-4 h-4" />
              <span className="hidden sm:inline">{t('chat')}</span>
            </button>

            <LanguageToggle />

            {user ? (
              <div className="flex items-center gap-2">
                <Link
                  href="/profile"
                  className="flex items-center gap-1.5 px-3 py-2 text-sm text-text-secondary hover:text-text-primary rounded-lg hover:bg-surface-secondary transition-colors"
                >
                  <User className="w-4 h-4" />
                  <span className="hidden sm:inline">{user.name}</span>
                </Link>
                <Link href="/ads/new">
                  <Button size="sm">
                    <PlusCircle className="w-4 h-4" />
                    <span className="hidden sm:inline">{t('post_ad')}</span>
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link href="/login">
                  <Button variant="ghost" size="sm">{t('login')}</Button>
                </Link>
                <Link href="/register">
                  <Button size="sm">{t('register')}</Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
