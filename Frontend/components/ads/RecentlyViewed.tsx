'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { Clock, ChevronRight } from 'lucide-react'
import { formatPrice, BLUR_PLACEHOLDER } from '@/lib/utils'
import type { Ad } from '@/types/ad'

const STORAGE_KEY = 'recently_viewed_ads'
const MAX_ITEMS = 8

function getRecentlyViewed(): Ad[] {
  if (typeof window === 'undefined') return []
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

export function addRecentlyViewed(ad: Ad) {
  try {
    const current = getRecentlyViewed()
    const filtered = current.filter((a) => a.id !== ad.id)
    const updated = [ad, ...filtered].slice(0, MAX_ITEMS)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  } catch {
    // ignore
  }
}

export function RecentlyViewed() {
  const [ads, setAds] = useState<Ad[]>([])
  const router = useRouter()

  useEffect(() => {
    setAds(getRecentlyViewed())
  }, [])

  if (ads.length === 0) return null

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center gap-2 mb-5">
        <Clock className="w-5 h-5 text-text-muted" />
        <h2 className="text-xl font-bold text-text-primary">Recently Viewed</h2>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-surface-border">
        {ads.slice(0, 6).map((ad) => (
          <button
            key={ad.id}
            onClick={() => router.push(`/ads/${ad.id}`)}
            className="group flex items-center gap-3 bg-surface rounded-xl border border-surface-border p-2 shrink-0 hover:border-primary-300 hover:shadow-md transition-all text-left"
          >
            <div className="relative w-16 h-16 rounded-lg overflow-hidden bg-surface-secondary shrink-0">
              <Image
                src={ad.cover_image_url || '/placeholder.svg'}
                alt={ad.model}
                fill
                className="object-cover group-hover:scale-105 transition-transform duration-300"
                sizes="64px"
                placeholder="blur"
                blurDataURL={BLUR_PLACEHOLDER}
              />
            </div>
            <div className="min-w-0 max-w-[160px]">
              <p className="text-sm font-medium text-text-primary truncate">
                {ad.brand} {ad.model} {ad.year}
              </p>
              <p className="text-xs text-primary-500 font-semibold mt-0.5">
                {formatPrice(ad.price)} EGP
              </p>
            </div>
            <ChevronRight className="w-4 h-4 text-text-muted shrink-0" />
          </button>
        ))}
      </div>
    </section>
  )
}
