'use client'

import { useTranslations } from 'next-intl'
import { useEffect } from 'react'
import { X } from 'lucide-react'
import { useAds } from '@/hooks/useAds'
import { AdFilters } from '@/components/ads/AdFilters'
import { AdGrid } from '@/components/ads/AdGrid'
import type { Ad } from '@/types/ad'

interface AdGridClientProps {
  initialAds: Ad[]
  selectedBrand?: string
}

const FILTER_LABELS: Record<string, string> = {
  brand: 'Brand',
  condition: 'Condition',
  fuel_type: 'Fuel',
  transmission: 'Transmission',
  body_type: 'Body',
  city: 'City',
}

export function AdGridClient({ initialAds, selectedBrand }: AdGridClientProps) {
  const t = useTranslations('home')
  const { ads, filters, isLoading, hasMore, loadMore, updateFilters, resetFilters } = useAds({
    autoFetch: true,
  })

  useEffect(() => {
    if (selectedBrand) {
      updateFilters({ brand: selectedBrand })
    } else {
      updateFilters({ brand: undefined })
    }
  }, [selectedBrand, updateFilters])

  const displayAds = ads.length > 0 ? ads : (!selectedBrand ? initialAds : [])

  const activeFilters = Object.entries(filters).filter(
    ([key, val]) =>
      val !== undefined && val !== '' && !['page', 'limit', 'sort'].includes(key)
  ) as [string, string][]

  function removeFilter(key: string) {
    updateFilters({ [key]: undefined })
  }

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
          {selectedBrand ? `Cars by ${selectedBrand}` : t('latest_listings')}
        </h2>

        {activeFilters.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 mb-4">
            {activeFilters.map(([key, val]) => (
              <span
                key={key}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary-50 text-primary-600 text-xs font-medium border border-primary-200"
              >
                {FILTER_LABELS[key] || key}: {val}
                <button onClick={() => removeFilter(key)} className="hover:bg-primary-100 rounded-full p-0.5 transition-colors">
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
            <button
              onClick={resetFilters}
              className="text-xs text-text-muted hover:text-text-secondary underline transition-colors"
            >
              Clear all
            </button>
          </div>
        )}

        {selectedBrand && displayAds.length === 0 && !isLoading && (
          <p className="text-text-secondary text-sm">
            No ads found for {selectedBrand}.
          </p>
        )}
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
