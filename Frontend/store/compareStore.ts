import { create } from 'zustand'
import type { Ad } from '@/types/ad'

interface CompareState {
  ads: Ad[]
  addAd: (ad: Ad) => boolean
  removeAd: (adId: string) => void
  clearAll: () => void
  isSelected: (adId: string) => boolean
}

function getInitialAds(): Ad[] {
  if (typeof window === 'undefined') return []
  try {
    const stored = sessionStorage.getItem('compare_ads')
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

function persistAds(ads: Ad[]) {
  if (typeof window !== 'undefined') {
    sessionStorage.setItem('compare_ads', JSON.stringify(ads))
  }
}

export const useCompareStore = create<CompareState>((set, get) => ({
  ads: getInitialAds(),

  addAd: (ad) => {
    const { ads } = get()
    if (ads.length >= 3) return false
    if (ads.some((a) => a.id === ad.id)) return false
    const updated = [...ads, ad]
    persistAds(updated)
    set({ ads: updated })
    return true
  },

  removeAd: (adId) => {
    const updated = get().ads.filter((a) => a.id !== adId)
    persistAds(updated)
    set({ ads: updated })
  },

  clearAll: () => {
    persistAds([])
    set({ ads: [] })
  },

  isSelected: (adId) => get().ads.some((a) => a.id === adId),
}))
