'use client'

import { useState } from 'react'
import { Plus, Check, BarChart3 } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useCompareStore } from '@/store/compareStore'
import type { Ad } from '@/types/ad'

interface CompareButtonProps {
  ad: Ad
}

export default function CompareButton({ ad }: CompareButtonProps) {
  const t = useTranslations('Compare')
  const { addAd: addCar, removeAd: removeCar, isSelected: isInCompare } = useCompareStore()
  const selected = isInCompare(ad.id)
  const [showToast, setShowToast] = useState(false)

  function handleToggle() {
    if (selected) {
      removeCar(ad.id)
      return
    }

    const added = addCar(ad)
    if (!added) {
      setShowToast(true)
      setTimeout(() => setShowToast(false), 3000)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={handleToggle}
        className={`
          group relative flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold
          transition-all duration-300 border overflow-hidden
          ${
            selected
              ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white border-primary-500 shadow-md shadow-primary-500/20'
              : 'bg-gradient-to-r from-primary-50 to-primary-100/80 text-primary-700 border-primary-200 hover:border-primary-300 hover:shadow-md hover:shadow-primary-500/10 dark:from-primary-950/20 dark:to-primary-900/10 dark:text-primary-400 dark:border-primary-800 dark:hover:border-primary-700'
          }
        `}
        title={selected ? t('addedToCompare') || 'Added to Compare' : t('addToCompare') || 'Add to Compare'}
      >
        <span className={`
          flex items-center justify-center w-5 h-5 rounded-full transition-all duration-300
          ${selected ? 'bg-white/20' : 'bg-primary-500/10 group-hover:bg-primary-500/20'}
        `}>
          {selected ? (
            <Check className="w-3 h-3 transition-transform duration-300 scale-100" />
          ) : (
            <Plus className="w-3 h-3 transition-transform duration-300 group-hover:rotate-90" />
          )}
        </span>
        <span className="truncate">
          {selected ? t('addedToCompare') || 'Added' : t('addToCompare') || 'Compare'}
        </span>
        <BarChart3 className="w-3.5 h-3.5 opacity-60 hidden sm:block" />
      </button>

      {showToast && (
        <div className="absolute -top-10 left-1/2 z-50 -translate-x-1/2 whitespace-nowrap rounded-lg bg-gradient-to-r from-danger to-red-600 px-3 py-1.5 text-sm text-white shadow-lg animate-in fade-in slide-in-from-top-2">
          {t('maxThreeCars') || 'Max 3 cars for comparison'}
        </div>
      )}
    </div>
  )
}
