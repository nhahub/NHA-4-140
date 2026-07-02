'use client'

import { useState } from 'react'
import { BrandCards } from '@/components/brands/BrandCards'
import { FeaturedCars } from '@/components/ads/FeaturedCars'
import { RecentlyViewed } from '@/components/ads/RecentlyViewed'
import { AdGridClient } from './AdGridClient'
import type { Ad } from '@/types/ad'

interface HomeClientProps {
  initialAds: Ad[]
}

export function HomeClient({ initialAds }: HomeClientProps) {
  const [selectedBrand, setSelectedBrand] = useState<string | undefined>()

  return (
    <>
      <BrandCards
        selectedBrand={selectedBrand}
        onBrandSelect={setSelectedBrand}
      />
      <FeaturedCars ads={initialAds} />
      <RecentlyViewed />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
        <AdGridClient
          initialAds={initialAds}
          selectedBrand={selectedBrand}
        />
      </main>
    </>
  )
}
