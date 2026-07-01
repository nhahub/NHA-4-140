'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'
import { AdGrid } from '@/components/ads/AdGrid'
import { api } from '@/lib/api'
import type { Ad } from '@/types/ad'

export default function ProfilePage() {
  const t = useTranslations('profile')
  const { user, logout } = useAuth()
  const [tab, setTab] = useState<'ads' | 'favorites'>('ads')
  const [myAds, setMyAds] = useState<Ad[]>([])
  const [favorites, setFavorites] = useState<Ad[]>([])

  useEffect(() => {
    if (!user) return
    api.get<{ ads: Ad[] }>(`/users/${user.id}/ads`).then((data) => {
      setMyAds(data.ads ?? [])
    }).catch(() => {})
    api.get<{ ads: Ad[] }>('/favorites').then((data) => {
      setFavorites(data.ads ?? [])
    }).catch(() => {})
  }, [user])

  function handleDelete(adId: string) {
    setMyAds((prev) => prev.filter((a) => a.id !== adId))
  }

  if (!user) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <p className="text-text-secondary">Please sign in to view your profile.</p>
        <Link href="/login"><Button className="mt-4">Sign In</Button></Link>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-text-primary">{t('title')}</h1>
        <Button variant="ghost" onClick={logout}>{t('settings').replace('Settings', 'Sign Out')}</Button>
      </div>

      <div className="flex gap-4 mb-6 border-b border-surface-border">
        {(['ads', 'favorites'] as const).map((tKey) => (
          <button
            key={tKey}
            onClick={() => setTab(tKey)}
            className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
              tab === tKey ? 'border-primary-500 text-primary-500' : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            {t(tKey === 'ads' ? 'my_ads' : 'favorites')}
          </button>
        ))}
      </div>

      {tab === 'ads' && (
        <div>
          {myAds.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-text-secondary mb-4">{t('no_ads')}</p>
              <Link href="/ads/new"><Button>{t('post_ad_cta')}</Button></Link>
            </div>
          ) : (
            <AdGrid ads={myAds} editable onDelete={handleDelete} />
          )}
        </div>
      )}

      {tab === 'favorites' && (
        <div>
          {favorites.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-text-secondary mb-4">{t('no_favorites')}</p>
              <Link href="/"><Button>{t('browse_cta')}</Button></Link>
            </div>
          ) : (
            <AdGrid ads={favorites} />
          )}
        </div>
      )}
    </div>
  )
}
