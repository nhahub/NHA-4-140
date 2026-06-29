'use client'

import { useTranslations } from 'next-intl'
import { useAds } from '@/hooks/useAds'
import { AdFilters } from '@/components/ads/AdFilters'
import { AdGrid } from '@/components/ads/AdGrid'
import type { Ad } from '@/types/ad'

interface AdGridClientProps {
  initialAds: Ad[]
}

export function AdGridClient({ initialAds }: AdGridClientProps) {
  const t = useTranslations('home')
  const { ads, filters, isLoading, hasMore, loadMore, updateFilters, resetFilters } = useAds({
    autoFetch: true,
  })

  const displayAds = ads.length > 0 ? ads : initialAds

  return (
    <div className="flex gap-8">
      <aside className="w-72 shrink-0 hidden lg:block">
        <AdFilters
          filters={filters}
          onFilterChange={updateFilters}
          onReset={resetFilters}
        />
      </aside>
      <div className="flex-1 min-w-0">
        <h2 className="text-2xl font-bold text-text-primary mb-6">
          {t('latest_listings')}
        </h2>
        <AdGrid
          ads={displayAds}
          isLoading={isLoading}
          hasMore={hasMore}
          loadMore={loadMore}
        />
      </div>
    </div>
  )
}
