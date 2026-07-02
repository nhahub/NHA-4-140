'use client'

import { useRef } from 'react'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { ChevronLeft, ChevronRight, Star, Gauge, Fuel, Settings } from 'lucide-react'
import { formatPrice, formatKm, getConditionBadge, BLUR_PLACEHOLDER } from '@/lib/utils'
import type { Ad } from '@/types/ad'

interface FeaturedCarsProps {
  ads: Ad[]
}

export function FeaturedCars({ ads }: FeaturedCarsProps) {
  const router = useRouter()
  const scrollRef = useRef<HTMLDivElement>(null)

  if (ads.length === 0) return null

  const featured = ads.slice(0, 6)

  function scroll(dir: 'left' | 'right') {
    if (!scrollRef.current) return
    const cardWidth = 320
    scrollRef.current.scrollBy({ left: dir === 'left' ? -cardWidth : cardWidth, behavior: 'smooth' })
  }

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-amber-100">
            <Star className="w-5 h-5 text-amber-600 fill-amber-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-text-primary">Featured Listings</h2>
            <p className="text-text-secondary text-sm mt-0.5">Hand-picked cars you might love</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => scroll('left')}
            className="p-2 rounded-xl bg-surface-secondary hover:bg-surface-border text-text-secondary hover:text-text-primary transition-colors border border-surface-border"
            aria-label="Scroll left"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={() => scroll('right')}
            className="p-2 rounded-xl bg-surface-secondary hover:bg-surface-border text-text-secondary hover:text-text-primary transition-colors border border-surface-border"
            aria-label="Scroll right"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-surface-border hover:scrollbar-thumb-text-secondary"
        style={{ scrollSnapType: 'x mandatory' }}
      >
        {featured.map((ad, idx) => {
          const badge = getConditionBadge(ad.condition)
          return (
            <div
              key={ad.id}
              onClick={() => router.push(`/ads/${ad.id}`)}
              className="group bg-surface rounded-xl border border-surface-border overflow-hidden cursor-pointer transition-all hover:shadow-lg hover:border-primary-300 shrink-0 w-[300px]"
              style={{ scrollSnapAlign: 'start' }}
            >
              <div className="relative aspect-[16/10] bg-surface-secondary">
                <Image
                  src={ad.cover_image_url || '/placeholder.svg'}
                  alt={`${ad.brand} ${ad.model} ${ad.year}`}
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-300"
                  sizes="300px"
                  placeholder="blur"
                  blurDataURL={BLUR_PLACEHOLDER}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
                <div className="absolute top-2 left-2 flex gap-1">
                  <span
                    className="px-2 py-1 rounded-md text-xs font-medium shadow-sm"
                    style={{ backgroundColor: badge.bg, color: badge.text }}
                  >
                    {badge.label}
                  </span>
                  {idx === 0 && (
                    <span className="px-2 py-1 rounded-md text-xs font-medium bg-amber-500 text-white shadow-sm">
                      Sponsored
                    </span>
                  )}
                </div>
                <div className="absolute bottom-3 left-3 right-3">
                  <h3 className="text-white font-bold text-base drop-shadow-sm">
                    {ad.brand} {ad.model} {ad.year}
                  </h3>
                  <p className="text-white text-lg font-bold drop-shadow-sm">
                    {formatPrice(ad.price)} <span className="text-sm font-normal">EGP</span>
                  </p>
                </div>
              </div>
              <div className="p-3">
                <div className="flex items-center gap-3 text-xs text-text-muted">
                  <span className="flex items-center gap-1">
                    <Gauge className="w-3.5 h-3.5" />
                    {formatKm(ad.km_driven)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Fuel className="w-3.5 h-3.5" />
                    {ad.fuel_type}
                  </span>
                  <span className="flex items-center gap-1">
                    <Settings className="w-3.5 h-3.5" />
                    {ad.transmission}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
