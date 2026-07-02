'use client'

import { useEffect } from 'react'
import { addRecentlyViewed } from '@/components/ads/RecentlyViewed'
import type { Ad } from '@/types/ad'

interface AdViewTrackerProps {
  ad: Ad
}

export function AdViewTracker({ ad }: AdViewTrackerProps) {
  useEffect(() => {
    addRecentlyViewed(ad)
  }, [ad])

  return null
}
