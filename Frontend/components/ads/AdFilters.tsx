'use client'

import { useState } from 'react'
import { Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { CONDITIONS, FUEL_TYPES, TRANSMISSIONS, BODY_TYPES, BODY_TYPE_ICONS } from '@/lib/utils'
import { useTranslations } from 'next-intl'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import type { AdFilters as AdFiltersType } from '@/types/ad'

const BRANDS = [
  'Toyota', 'Hyundai', 'Nissan', 'BMW', 'Mercedes', 'Honda', 'Chevrolet', 'Kia',
  'Suzuki', 'Mitsubishi', 'Renault', 'Peugeot', 'Volkswagen', 'Ford', 'Jeep',
  'MG', 'Chery', 'BYD', 'Geely', 'Opel', 'Fiat', 'Audi', 'Lexus',
]

const CITIES = [
  'Cairo', 'Alexandria', 'Giza', 'Mansoura', 'Tanta', 'Port Said',
  'Suez', 'Luxor', 'Aswan', 'Hurghada', 'Sharm el-Sheikh',
  '6th of October', 'Sheikh Zayed', 'New Cairo', 'Madinaty',
]

interface AdFiltersProps {
  filters: AdFiltersType
  onFilterChange: (filters: AdFiltersType) => void
  onReset: () => void
}

export function AdFilters({ filters, onFilterChange, onReset }: AdFiltersProps) {
  const t = useTranslations('filters')
  const [brandSearch, setBrandSearch] = useState('')
  const [showBrandDropdown, setShowBrandDropdown] = useState(false)

  const filteredBrands = BRANDS.filter((b) =>
    b.toLowerCase().includes(brandSearch.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          {t('brand')}
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted z-10" />
          <input
            className={cn(
              'w-full h-10 pl-9 pr-8 rounded-lg border border-surface-border bg-surface text-text-primary text-sm',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors'
            )}
            placeholder={t('search_brand')}
            value={filters.brand || brandSearch}
            onChange={(e) => {
              setBrandSearch(e.target.value)
              onFilterChange({ ...filters, brand: e.target.value || undefined })
              setShowBrandDropdown(true)
            }}
            onFocus={() => setShowBrandDropdown(true)}
            onBlur={() => setTimeout(() => setShowBrandDropdown(false), 200)}
          />
          {filters.brand && (
            <button
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
              onClick={() => {
                onFilterChange({ ...filters, brand: undefined })
                setBrandSearch('')
              }}
            >
              <X className="w-4 h-4" />
            </button>
          )}
          {showBrandDropdown && filteredBrands.length > 0 && (
            <div className="absolute z-20 mt-1 w-full bg-surface border border-surface-border rounded-lg shadow-lg max-h-48 overflow-y-auto">
              {filteredBrands.map((b) => (
                <button
                  key={b}
                  type="button"
                  className={cn(
                    'w-full text-left px-3 py-2 text-sm hover:bg-surface-secondary transition-colors',
                    filters.brand === b && 'bg-primary-50 text-primary-500 font-medium'
                  )}
                  onClick={() => {
                    onFilterChange({ ...filters, brand: b })
                    setBrandSearch(b)
                    setShowBrandDropdown(false)
                  }}
                >
                  {b}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          {t('price_range')}
        </label>
        <div className="flex gap-2">
          <Input
            type="number"
            placeholder="Min"
            value={filters.price_min ?? ''}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                price_min: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          />
          <Input
            type="number"
            placeholder="Max"
            value={filters.price_max ?? ''}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                price_max: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          {t('year_range')}
        </label>
        <div className="flex gap-2">
          <Input
            type="number"
            placeholder="Min"
            value={filters.year_min ?? ''}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                year_min: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          />
          <Input
            type="number"
            placeholder="Max"
            value={filters.year_max ?? ''}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                year_max: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          {t('city')}
        </label>
        <select
          className={cn(
            'w-full h-10 px-3 rounded-lg border border-surface-border bg-surface text-text-primary text-sm',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors'
          )}
          value={filters.city || ''}
          onChange={(e) =>
            onFilterChange({ ...filters, city: e.target.value || undefined })
          }
        >
          <option value="">{t('all')}</option>
          {CITIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          {t('condition')}
        </label>
        <div className="space-y-2">
          {CONDITIONS.map((c) => {
            const checked = filters.condition === c
            return (
              <label
                key={c}
                className={cn(
                  'flex items-center gap-2 cursor-pointer px-3 py-2 rounded-lg border transition-colors',
                  checked
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-surface-border hover:border-text-muted'
                )}
              >
                <input
                  type="checkbox"
                  className="rounded border-surface-border text-primary-500 focus:ring-primary-500"
                  checked={checked}
                  onChange={() =>
                    onFilterChange({
                      ...filters,
                      condition: checked ? undefined : c,
                    })
                  }
                />
                <span className="text-sm text-text-primary capitalize">{c}</span>
              </label>
            )
          })}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          {t('fuel_type')}
        </label>
        <div className="space-y-2">
          {FUEL_TYPES.map((f) => {
            const checked = filters.fuel_type === f
            return (
              <label
                key={f}
                className={cn(
                  'flex items-center gap-2 cursor-pointer px-3 py-2 rounded-lg border transition-colors',
                  checked
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-surface-border hover:border-text-muted'
                )}
              >
                <input
                  type="checkbox"
                  className="rounded border-surface-border text-primary-500 focus:ring-primary-500"
                  checked={checked}
                  onChange={() =>
                    onFilterChange({
                      ...filters,
                      fuel_type: checked ? undefined : f,
                    })
                  }
                />
                <span className="text-sm text-text-primary capitalize">{f}</span>
              </label>
            )
          })}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          {t('transmission')}
        </label>
        <div className="flex gap-4">
          {TRANSMISSIONS.map((tr) => (
            <label
              key={tr}
              className={cn(
                'flex items-center gap-2 cursor-pointer px-4 py-2 rounded-lg border transition-colors flex-1 justify-center',
                filters.transmission === tr
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-surface-border hover:border-text-muted'
              )}
            >
              <input
                type="radio"
                name="transmission"
                className="border-surface-border text-primary-500 focus:ring-primary-500"
                checked={filters.transmission === tr}
                onChange={() =>
                  onFilterChange({
                    ...filters,
                    transmission: filters.transmission === tr ? undefined : tr,
                  })
                }
              />
              <span className="text-sm text-text-primary capitalize">{tr}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          {t('body_type')}
        </label>
        <div className="grid grid-cols-4 gap-2">
          {BODY_TYPES.map((b) => (
            <button
              key={b}
              type="button"
              className={cn(
                'flex flex-col items-center gap-1 p-2 rounded-lg border text-xs transition-colors',
                filters.body_type === b
                  ? 'border-primary-500 bg-primary-50 text-primary-500'
                  : 'border-surface-border text-text-muted hover:border-text-muted hover:text-text-primary'
              )}
              onClick={() =>
                onFilterChange({
                  ...filters,
                  body_type: filters.body_type === b ? undefined : b,
                })
              }
            >
              <span className="text-lg">{BODY_TYPE_ICONS[b]}</span>
              <span className="capitalize">{b}</span>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-text-primary mb-1.5">
          {t('sort')}
        </label>
        <select
          className={cn(
            'w-full h-10 px-3 rounded-lg border border-surface-border bg-surface text-text-primary text-sm',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors'
          )}
          value={filters.sort || 'newest'}
          onChange={(e) =>
            onFilterChange({ ...filters, sort: e.target.value })
          }
        >
          <option value="newest">{t('sort_newest')}</option>
          <option value="price_asc">{t('sort_price_asc')}</option>
          <option value="price_desc">{t('sort_price_desc')}</option>
          <option value="most_viewed">{t('sort_views')}</option>
        </select>
      </div>

      <div className="space-y-2 pt-2">
        <Button className="w-full" onClick={() => onFilterChange({ ...filters, page: 1 })}>
          {t('apply')}
        </Button>
        <Button variant="outline" className="w-full" onClick={onReset}>
          {t('reset')}
        </Button>
      </div>
    </div>
  )
}
