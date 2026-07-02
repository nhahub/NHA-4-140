import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { MapPin, Phone, Eye } from 'lucide-react'
import { api } from '@/lib/api'
import { formatPrice, getConditionBadge } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { AdImageGallery } from '@/components/ads/AdImageGallery'
import { AdSpecsTable } from '@/components/ads/AdSpecsTable'
import CompareButton from '@/components/compare/CompareButton'
import { AskAiButton } from '@/components/ads/AskAiButton'
import { AiPriceWidget } from '@/components/ads/AiPriceWidget'
import { ShareButtons } from '@/components/ads/ShareButtons'
import { RecentlyViewed } from '@/components/ads/RecentlyViewed'
import { AdViewTracker } from './AdViewTracker'
import type { Ad } from '@/types/ad'

interface PageProps {
  params: Promise<{ id: string }>
}

async function fetchAd(id: string): Promise<Ad | null> {
  try {
    return await api.get<Ad>(`/ads/${id}`)
  } catch (err: any) {
    if (err?.status === 404) return null
    throw err
  }
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params
  const ad = await fetchAd(id)
  if (!ad) return {}
  return {
    title: `${ad.brand} ${ad.model} ${ad.year} - ${formatPrice(ad.price)} EGP`,
    description: ad.description?.slice(0, 160) || `${ad.brand} ${ad.model} ${ad.year} for sale`,
  }
}

export default async function AdDetailPage({ params }: PageProps) {
  const { id } = await params
  const ad = await fetchAd(id)
  if (!ad) notFound()

  const badge = getConditionBadge(ad.condition)

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="lg:flex lg:gap-8">
        <div className="lg:w-2/3 space-y-6">
          <AdImageGallery images={ad.images} coverImageUrl={ad.cover_image_url} />

          <section className="bg-surface rounded-xl border border-surface-border p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-4">Specifications</h2>
            <AdSpecsTable ad={ad} />
          </section>

          <section className="bg-surface rounded-xl border border-surface-border p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-3">Description</h2>
            <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-line">
              {ad.description}
            </p>
          </section>

          {ad.special_conditions && (
            <section className="bg-surface rounded-xl border border-surface-border p-6">
              <h2 className="text-lg font-semibold text-text-primary mb-3">Special Conditions</h2>
              <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-line">
                {ad.special_conditions}
              </p>
            </section>
          )}

          <div className="flex items-center gap-3">
            <CompareButton ad={ad} />
          </div>
        </div>

        <aside className="lg:w-1/3 mt-6 lg:mt-0">
          <div className="lg:sticky lg:top-24 space-y-4">
            <div className="bg-surface rounded-xl border border-surface-border p-6 space-y-4">
              <div>
                <p className="text-3xl font-bold text-text-primary">
                  {formatPrice(ad.price)} <span className="text-lg font-medium text-text-muted">EGP</span>
                </p>
                <span
                  className="inline-block mt-2 px-3 py-1 rounded-md text-xs font-medium"
                  style={{ backgroundColor: badge.bg, color: badge.text }}
                >
                  {badge.label}
                </span>
              </div>

              <div className="flex items-center gap-2 text-sm text-text-muted">
                <Eye className="w-4 h-4" />
                <span>{ad.views_count} views</span>
              </div>

              <div className="flex items-center gap-3 p-4 bg-surface-secondary rounded-xl">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-500 font-bold text-lg">
                  {ad.brand[0]}
                </div>
                <div>
                  <p className="text-sm font-medium text-text-primary">{ad.brand} {ad.model}</p>
                  <div className="flex items-center gap-1 text-xs text-text-muted mt-0.5">
                    <MapPin className="w-3 h-3" />
                    <span>{ad.city}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-primary-500" />
                <span className="text-sm font-medium text-text-primary">0100 000 0000</span>
              </div>

              <AiPriceWidget price={ad.price} brand={ad.brand} model={ad.model} year={ad.year} />

              <AskAiButton adId={ad.id} />

              <ShareButtons ad={ad} />
            </div>
          </div>
        </aside>
      </div>

      <RecentlyViewed />
      <AdViewTracker ad={ad} />
    </div>
  )
}
