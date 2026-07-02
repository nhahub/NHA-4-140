import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPrice(price: number): string {
  return price.toLocaleString('en-EG')
}

export function formatKm(km: number): string {
  if (km >= 1000) {
    return (km / 1000).toFixed(km % 1000 === 0 ? 0 : 1) + 'k'
  }
  return km.toLocaleString()
}

export function formatViews(count: number): string {
  if (count >= 1000000) return (count / 1000000).toFixed(1) + 'M'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'k'
  return count.toString()
}

export function getConditionBadge(condition: string): { bg: string; text: string; label: string } {
  const map: Record<string, { bg: string; text: string; label: string }> = {
    new: { bg: '#dbeafe', text: '#1d4ed8', label: 'New' },
    used: { bg: '#fef9c3', text: '#854d0e', label: 'Used' },
  }
  return map[condition.toLowerCase()] || map.used
}

export const BLUR_PLACEHOLDER =
  'data:image/webp;base64,UklGRiQAAABXRUJQVlA4IBgAAAAwAQCdASoCAAEADMDOJaQAA3AA/vuEAAA='

export const BODY_TYPE_ICONS: Record<string, string> = {
  sedan: '🚗',
  suv: '🚙',
  hatchback: '🚘',
  pickup: '🛻',
  coupe: '🏎️',
  convertible: '🚗',
  van: '🚐',
  wagon: '🚗',
}

export const CONDITIONS = ['new', 'used'] as const
export const FUEL_TYPES = ['petrol', 'diesel', 'electric', 'hybrid'] as const
export const TRANSMISSIONS = ['automatic', 'manual'] as const
export const BODY_TYPES = ['sedan', 'suv', 'hatchback', 'pickup', 'coupe', 'van', 'wagon'] as const
