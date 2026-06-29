'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Search, MessageCircle } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { AdCard } from '@/components/ads/AdCard'
import { AskAiBanner } from '@/components/ads/AskAiBanner'
import type { Ad } from '@/types/ad'

export default function SearchPage() {
  const t = useTranslations('search')
  const searchParams = useSearchParams()
  const query = searchParams.get('q') || ''
  const [ads, setAds] = useState<Ad[]>([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (!query) {
      setAds([])
      return
    }
    setIsLoading(true)
    api.get<{ ads: Ad[] }>('/search', { q: query })
      .then((data) => setAds(data.ads))
      .catch(() => setAds([]))
      .finally(() => setIsLoading(false))
  }, [query])

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <Search className="w-6 h-6" />
          {query ? (
            <>
              {t('resultsFor', { query }) || `Results for "${query}"`}
              <span className="text-sm font-normal text-text-muted">
                ({ads.length} {t('found') || 'found'})
              </span>
            </>
          ) : (
            t('title') || 'Search Cars'
          )}
        </h1>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="bg-surface rounded-xl border border-surface-border overflow-hidden animate-pulse">
              <div className="aspect-[16/9] bg-surface-secondary" />
              <div className="p-4 space-y-3">
                <div className="h-4 bg-surface-secondary rounded w-3/4" />
                <div className="h-5 bg-surface-secondary rounded w-1/2" />
                <div className="h-3 bg-surface-secondary rounded w-full" />
              </div>
            </div>
          ))}
        </div>
      ) : ads.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {ads.map((ad) => (
            <AdCard key={ad.id} ad={ad} />
          ))}
        </div>
      ) : (
        <div className="text-center py-20">
          <Search className="w-16 h-16 mx-auto text-text-muted mb-4" />
          <h2 className="text-xl font-semibold text-text-primary mb-2">
            {query ? t('noResults', { query }) || `No results for "${query}"` : t('emptyTitle') || 'Search for cars'}
          </h2>
          <p className="text-text-muted mb-6">
            {t('emptySubtitle') || 'Try a different search or ask the AI assistant for help.'}
          </p>
          <AskAiBanner />
        </div>
      )}
    </div>
  )
}
