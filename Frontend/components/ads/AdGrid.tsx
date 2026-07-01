'use client'

import { useEffect, useRef } from 'react'
import type { Ad } from '@/types/ad'
import { AdCard } from './AdCard'
import { AdCardSkeleton } from '@/components/ui/Skeleton'

interface AdGridProps {
  ads: Ad[]
  isLoading?: boolean
  hasMore?: boolean
  loadMore?: () => void
  editable?: boolean
  onDelete?: (adId: string) => void
}

export function AdGrid({ ads, isLoading, hasMore, loadMore, editable, onDelete }: AdGridProps) {
  const observerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!observerRef.current || !hasMore || !loadMore) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadMore()
      },
      { threshold: 0.1 }
    )
    observer.observe(observerRef.current)
    return () => observer.disconnect()
  }, [hasMore, loadMore])

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {ads.map((ad) => (
          <AdCard key={ad.id} ad={ad} editable={editable} onDelete={onDelete} />
        ))}
        {isLoading &&
          Array.from({ length: 6 }).map((_, i) => <AdCardSkeleton key={`skeleton-${i}`} />)
        }
      </div>
      {hasMore && <div ref={observerRef} className="h-10" />}
    </div>
  )
}
