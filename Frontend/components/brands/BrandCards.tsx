'use client'

import { useEffect, useState, useRef } from 'react'
import Image from 'next/image'
import { X, ChevronLeft, ChevronRight } from 'lucide-react'
import { api } from '@/lib/api'

interface BrandCount {
  brand: string
  count: number
}

interface BrandCardsProps {
  selectedBrand?: string
  onBrandSelect: (brand: string | undefined) => void
}

const BG_COLORS = [
  'bg-blue-500', 'bg-emerald-500', 'bg-violet-500', 'bg-amber-500',
  'bg-rose-500', 'bg-cyan-500', 'bg-orange-500', 'bg-teal-500',
  'bg-pink-500', 'bg-indigo-500', 'bg-lime-500', 'bg-red-500',
]

function getColor(brand: string): string {
  let hash = 0
  for (let i = 0; i < brand.length; i++) {
    hash = brand.charCodeAt(i) + ((hash << 5) - hash)
  }
  return BG_COLORS[Math.abs(hash) % BG_COLORS.length]
}

function brandToLogoPath(brand: string): string {
  return `/brand_logos/${brand.replace(/\s+/g, '_')}.png`
}

export function BrandCards({ selectedBrand, onBrandSelect }: BrandCardsProps) {
  const [brands, setBrands] = useState<BrandCount[]>([])
  const [loading, setLoading] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.get<{ brands: BrandCount[] }>('/ads/brand-counts')
      .then((data) => setBrands(data.brands || []))
      .catch(() => setBrands([]))
      .finally(() => setLoading(false))
  }, [])

  function scroll(dir: 'left' | 'right') {
    if (!scrollRef.current) return
    const amount = 280
    scrollRef.current.scrollBy({ left: dir === 'left' ? -amount : amount, behavior: 'smooth' })
  }

  if (loading) {
    return (
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <h2 className="text-2xl font-bold text-text-primary mb-6">Browse by Brand</h2>
        <div className="flex gap-3 overflow-hidden">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-xl bg-surface-secondary min-w-[130px] h-28 shrink-0" />
          ))}
        </div>
      </section>
    )
  }

  if (brands.length === 0) return null

  const totalCars = brands.reduce((s, b) => s + b.count, 0)

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-text-primary">Browse by Brand</h2>
          <p className="text-text-secondary text-sm mt-1">
            {brands.length} brands &middot; {totalCars} cars
          </p>
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
        className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-surface-border hover:scrollbar-thumb-text-secondary"
        style={{ scrollSnapType: 'x mandatory' }}
      >
        {brands.map((b) => {
          const isActive = selectedBrand === b.brand
          return (
            <button
              key={b.brand}
              onClick={() => onBrandSelect(isActive ? undefined : b.brand)}
              className={`group flex flex-col items-center gap-2 min-w-[130px] p-4 rounded-xl transition-all border shrink-0 ${
                isActive
                  ? 'bg-primary-50 border-primary-400 shadow-md ring-1 ring-primary-400'
                  : 'bg-surface-secondary hover:bg-surface-border border-surface-border hover:border-primary-300 hover:shadow-md'
              }`}
              style={{ scrollSnapAlign: 'start' }}
            >
              <div className={`relative w-14 h-14 rounded-full overflow-hidden flex items-center justify-center ring-2 transition-all ${
                isActive ? 'ring-primary-400' : 'ring-surface-border group-hover:ring-primary-300'
              }`}>
                <Image
                  src={brandToLogoPath(b.brand)}
                  alt={b.brand}
                  width={48}
                  height={48}
                  className="object-contain p-1 group-hover:scale-110 transition-transform"
                />
              </div>
              <span className={`text-xs font-semibold text-center leading-tight ${
                isActive ? 'text-primary-600' : 'text-text-primary'
              }`}>
                {b.brand}
              </span>
              <span className="text-[10px] text-text-secondary font-medium -mt-0.5">
                {b.count} ad{b.count !== 1 ? 's' : ''}
              </span>
            </button>
          )
        })}
      </div>

      {selectedBrand && (
        <div className="flex items-center gap-2 mt-4 text-sm">
          <span className="text-text-secondary">
            Showing ads for <strong className="text-text-primary">{selectedBrand}</strong>
          </span>
          <button
            onClick={() => onBrandSelect(undefined)}
            className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-primary-50 text-primary-600 hover:bg-primary-100 transition-colors text-xs font-medium"
          >
            <X className="w-3 h-3" />
            Clear filter
          </button>
        </div>
      )}
    </section>
  )
}
