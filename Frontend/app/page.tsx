import { Search, Car } from 'lucide-react'
import { getTranslations } from 'next-intl/server'
import { HomeClient } from './HomeClient'
import type { Ad } from '@/types/ad'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

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
  const t = await getTranslations('home')
  const initialAds = await getInitialAds()

  return (
    <div>
      <section className="bg-gradient-to-br from-primary-500 via-primary-600 to-primary-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
          <div className="max-w-2xl">
            <div className="flex items-center gap-2 mb-4 text-primary-100">
              <Car className="w-5 h-5" />
              <span className="text-sm font-medium uppercase tracking-wider">
                AI-Powered Car Marketplace
              </span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4 leading-tight">
              {t('hero_title')}
            </h1>
            <p className="text-lg text-primary-100 mb-8">
              {t('hero_subtitle')}
            </p>
            <form
              action="/search"
              className="relative max-w-xl"
            >
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                name="q"
                placeholder={t('search_placeholder')}
                className="w-full h-14 pl-12 pr-4 rounded-xl bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-300 text-base shadow-lg"
              />
            </form>
          </div>
        </div>
      </section>

      <HomeClient initialAds={initialAds} />
    </div>
  )
}
