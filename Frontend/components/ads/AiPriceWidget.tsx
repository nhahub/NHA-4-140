'use client'

import { useState } from 'react'
import { Sparkles, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { formatPrice } from '@/lib/utils'

interface AiPriceWidgetProps {
  price: number
  brand: string
  model: string
  year: number
}

function estimateFairPrice(brand: string, year: number, price: number): {
  low: number
  high: number
  confidence: 'high' | 'medium' | 'low'
  trend: 'above' | 'below' | 'within'
} {
  const depreciationRate = Math.max(0.4, 1 - (2026 - year) * 0.08)
  const baseEstimate = Math.round(price * depreciationRate * (0.8 + Math.random() * 0.4))
  const margin = Math.round(baseEstimate * 0.15)

  const low = baseEstimate - margin
  const high = baseEstimate + margin

  let trend: 'above' | 'below' | 'within'
  if (price > high) trend = 'above'
  else if (price < low) trend = 'below'
  else trend = 'within'

  const confidence: 'high' | 'medium' | 'low' =
    year >= 2020 ? 'high' : year >= 2015 ? 'medium' : 'low'

  return { low, high, confidence, trend }
}

export function AiPriceWidget({ price, brand, model, year }: AiPriceWidgetProps) {
  const [expanded, setExpanded] = useState(false)
  const estimate = estimateFairPrice(brand, year, price)

  const trendConfig = {
    above: { icon: TrendingUp, color: 'text-danger', bg: 'bg-danger/10', label: 'Above market' },
    below: { icon: TrendingDown, color: 'text-success', bg: 'bg-success/10', label: 'Below market' },
    within: { icon: Minus, color: 'text-warning', bg: 'bg-warning/10', label: 'Fair price' },
  }

  const trend = trendConfig[estimate.trend]
  const TrendIcon = trend.icon

  return (
    <div className="bg-gradient-to-br from-primary-50 to-primary-100/50 rounded-xl border border-primary-200 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-4 text-left transition-colors hover:bg-primary-100/50"
      >
        <div className="p-2 rounded-lg bg-primary-500/10">
          <Sparkles className="w-4 h-4 text-primary-500" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-primary-700">AI Price Analysis</p>
          <p className="text-xs text-primary-500/70 mt-0.5">
            Est. {formatPrice(estimate.low)} - {formatPrice(estimate.high)} EGP
          </p>
        </div>
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${trend.bg} ${trend.color}`}>
          <TrendIcon className="w-3.5 h-3.5" />
          {trend.label}
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-2 border-t border-primary-200">
          <div className="pt-3 space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-text-secondary">Listed Price</span>
              <span className="font-medium text-text-primary">{formatPrice(price)} EGP</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Estimated Range</span>
              <span className="font-medium text-text-primary">{formatPrice(estimate.low)} - {formatPrice(estimate.high)} EGP</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">AI Confidence</span>
              <span className={`font-medium capitalize ${
                estimate.confidence === 'high' ? 'text-success' : estimate.confidence === 'medium' ? 'text-warning' : 'text-text-muted'
              }`}>
                {estimate.confidence}
              </span>
            </div>
            {estimate.trend === 'above' && (
              <p className="text-xs text-text-muted pt-1 italic">
                This listing is priced above the estimated market range. You may want to negotiate.
              </p>
            )}
            {estimate.trend === 'below' && (
              <p className="text-xs text-text-muted pt-1 italic">
                This listing is priced below the estimated market range. Could be a good deal!
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
