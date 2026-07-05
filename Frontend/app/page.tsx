import { getTranslations } from 'next-intl/server'
import { HomeClient } from './HomeClient'
import { HeroSection } from '@/components/home/HeroSection'
import type { Ad } from '@/types/ad'

const API_URL = process.env.API_URL || 'http://backend:8000/api/v1'

async function getInitialAds(): Promise<Ad[]> {
  try {
    const res = await fetch(`${API_URL}/ads?page=1&limit=12`, {
      cache: 'no-store',
    })
    if (!res.ok) return []
    const data = await res.json()
    return data.ads ?? []
  } catch {
    return []
  }
}

export default async function HomePage() {
  const initialAds = await getInitialAds()

  return (
    <div>
      <HeroSection />
      <HomeClient initialAds={initialAds} />
    </div>
  )
}
