'use client'

import { useRouter, usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { X, ArrowRight } from 'lucide-react'
import Image from 'next/image'
import { Button } from '@/components/ui/Button'
import { useCompareStore } from '@/store/compareStore'

export function CompareTray() {
  const t = useTranslations('Compare')
  const router = useRouter()
  const pathname = usePathname()
  const { ads, removeAd, clearAll } = useCompareStore()

  if (ads.length === 0 || pathname === '/compare') return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 bg-surface border-t border-surface-border shadow-lg animate-slide-up">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-4">
        <div className="flex items-center gap-3 flex-1 overflow-x-auto">
          {ads.map((ad) => (
            <div key={ad.id} className="flex items-center gap-2 bg-surface-secondary rounded-lg px-3 py-2 shrink-0">
              {ad.cover_image_url && (
                <Image src={ad.cover_image_url} alt="" width={40} height={30} className="rounded object-cover" />
              )}
              <div className="text-sm">
                <p className="font-medium text-text-primary truncate max-w-[120px]">
                  {ad.brand} {ad.model} {ad.year}
                </p>
                <p className="text-text-muted">{ad.price.toLocaleString()} EGP</p>
              </div>
              <button onClick={() => removeAd(ad.id)} className="p-1 hover:bg-surface-border rounded transition-colors">
                <X className="w-4 h-4 text-text-muted" />
              </button>
            </div>
          ))}

          {ads.length < 3 && (
            <p className="text-sm text-text-muted shrink-0">{t('add_more')}</p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="sm" onClick={clearAll}>
            {t('startOver')}
          </Button>
          <Button
            size="sm"
            disabled={ads.length < 2}
            onClick={() => router.push('/compare')}
          >
            {t('compare_now')}
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
