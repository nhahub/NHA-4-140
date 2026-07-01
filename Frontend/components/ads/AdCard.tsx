'use client'

import { useState } from 'react'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { Heart, MapPin, Gauge, Fuel, Settings, Trash2, AlertTriangle } from 'lucide-react'
import { cn, formatPrice, formatKm, formatViews, getConditionBadge } from '@/lib/utils'
import { useCompareStore } from '@/store/compareStore'
import { api } from '@/lib/api'
import type { Ad } from '@/types/ad'

interface AdCardProps {
  ad: Ad
  editable?: boolean
  onDelete?: (adId: string) => void
}

export function AdCard({ ad, editable, onDelete }: AdCardProps) {
  const router = useRouter()
  const { addAd, removeAd, isSelected } = useCompareStore()
  const selected = isSelected(ad.id)
  const badge = getConditionBadge(ad.condition)
  const [isSaved, setIsSaved] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  async function handleDelete(e: React.MouseEvent) {
    e.stopPropagation()
    if (!confirmDelete) {
      setConfirmDelete(true)
      setTimeout(() => setConfirmDelete(false), 3000)
      return
    }
    setDeleting(true)
    try {
      await api.del(`/ads/${ad.id}`)
      onDelete?.(ad.id)
    } catch {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  return (
    <div
      className="group bg-surface rounded-xl border border-surface-border overflow-hidden cursor-pointer transition-all hover:shadow-lg"
      onClick={() => router.push(`/ads/${ad.id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') router.push(`/ads/${ad.id}`) }}
    >
      <div className="relative aspect-[16/9] bg-surface-secondary">
        <Image
          src={ad.cover_image_url || 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22800%22 height=%22600%22%3E%3Crect fill=%22%23e2e8f0%22 width=%22800%22 height=%22600%22/%3E%3Ctext fill=%22%2394a3b8%22 font-family=%22Arial%22 font-size=%2224%22 x=%22400%22 y=%22300%22 text-anchor=%22middle%22 dy=%22.3em%22%3ENo Image%3C/text%3E%3C/svg%3E'}
          alt={`${ad.brand} ${ad.model} ${ad.year}`}
          fill
          className="object-cover group-hover:scale-105 transition-transform duration-300"
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
        />
        <div className="absolute top-2 left-2 flex gap-1">
          <span
            className="px-2 py-1 rounded-md text-xs font-medium"
            style={{ backgroundColor: badge.bg, color: badge.text }}
          >
            {badge.label}
          </span>
        </div>
        {editable ? (
          <div className="absolute top-2 right-2 flex gap-1">
            {confirmDelete ? (
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="p-2 bg-danger text-white rounded-full shadow-lg hover:opacity-90 transition-all animate-pulse"
                title="Click again to confirm delete"
              >
                {deleting ? (
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <AlertTriangle className="w-4 h-4" />
                )}
              </button>
            ) : (
              <button
                onClick={handleDelete}
                className="p-2 bg-white/80 backdrop-blur-sm rounded-full hover:bg-danger hover:text-white transition-all"
                title="Delete ad"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        ) : (
          <button
            onClick={(e) => { e.stopPropagation(); setIsSaved(!isSaved) }}
            className="absolute top-2 right-2 p-2 bg-white/80 backdrop-blur-sm rounded-full hover:bg-white transition-colors"
            aria-label={isSaved ? 'Remove from saved' : 'Save'}
          >
            <Heart className={cn('w-4 h-4', isSaved ? 'fill-danger text-danger' : 'text-text-secondary')} />
          </button>
        )}
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-text-primary truncate">
          {ad.brand} {ad.model} {ad.year}
        </h3>
        <p className="text-lg font-bold text-primary-500 mt-1">
          {formatPrice(ad.price)} EGP
        </p>
        <div className="flex items-center gap-3 mt-2 text-xs text-text-muted">
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
          <span className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5" />
            {ad.city}
          </span>
        </div>
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-surface-border">
          <button
            onClick={(e) => {
              e.stopPropagation()
              selected ? removeAd(ad.id) : addAd(ad)
            }}
            className={cn(
              'text-xs font-medium transition-colors',
              selected ? 'text-primary-500' : 'text-text-muted hover:text-primary-500'
            )}
          >
            {selected ? 'Added to Compare' : 'Add to Compare'}
          </button>
          <span className="text-xs text-text-muted flex items-center gap-1">
            {formatViews(ad.views_count)} views
          </span>
        </div>
      </div>
    </div>
  )
}
