'use client'

import { useState } from 'react'
import { BrandCards } from '@/components/brands/BrandCards'
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AdGridClient
          initialAds={initialAds}
          selectedBrand={selectedBrand}
        />
      </main>
    </>
  )
}
