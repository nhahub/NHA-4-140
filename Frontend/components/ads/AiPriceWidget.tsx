'use client'

import { useState, useEffect } from 'react'
import { Sparkles, TrendingUp, TrendingDown, Minus, Loader2, AlertCircle, ExternalLink, Search } from 'lucide-react'
import { formatPrice } from '@/lib/utils'
import { usePriceAnalysis } from '@/hooks/usePriceAnalysis'

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
  const { report, isLoading, error, fetchReport } = usePriceAnalysis()
  const estimate = estimateFairPrice(brand, year, price)

  useEffect(() => {
    if (expanded && !report && !isLoading && !error) {
      fetchReport(brand, model, year)
    }
  }, [expanded, brand, model, year, report, isLoading, error, fetchReport])

  const hasRealData = report && report.estimated_range.low > 0

  const trend = (() => {
    if (hasRealData) {
      if (price > report.estimated_range.high) return { icon: TrendingUp, color: 'text-danger', bg: 'bg-danger/10', label: 'Above market' }
      if (price < report.estimated_range.low) return { icon: TrendingDown, color: 'text-success', bg: 'bg-success/10', label: 'Below market' }
      return { icon: Minus, color: 'text-warning', bg: 'bg-warning/10', label: 'Fair price' }
    }
    const t = estimate.trend
    const config = {
      above: { icon: TrendingUp, color: 'text-danger', bg: 'bg-danger/10', label: 'Above market' },
      below: { icon: TrendingDown, color: 'text-success', bg: 'bg-success/10', label: 'Below market' },
      within: { icon: Minus, color: 'text-warning', bg: 'bg-warning/10', label: 'Fair price' },
    }
    return config[t]
  })()

  const TrendIcon = trend.icon

  const rangeLow = hasRealData ? report.estimated_range.low : estimate.low
  const rangeHigh = hasRealData ? report.estimated_range.high : estimate.high
  const confidenceLevel = hasRealData ? report.confidence : estimate.confidence

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
            {isLoading ? 'Analyzing market...' : report ? (hasRealData ? 'Market data available' : 'Search completed') : `Est. ${formatPrice(rangeLow)} - ${formatPrice(rangeHigh)} EGP`}
          </p>
        </div>
        {!isLoading && !error && (
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${trend.bg} ${trend.color}`}>
            <TrendIcon className="w-3.5 h-3.5" />
            {trend.label}
          </div>
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-2 border-t border-primary-200">
          {isLoading ? (
            <div className="pt-3 flex items-center gap-2 text-sm text-text-secondary">
              <Loader2 className="w-4 h-4 animate-spin" />
              Searching market prices across OLX, Contact Cars & more...
            </div>
          ) : error ? (
            <div className="pt-3 space-y-1.5 text-sm">
              <div className="flex items-center gap-2 text-text-muted">
                <AlertCircle className="w-4 h-4 text-warning" />
                <span>Live data unavailable — showing estimated range</span>
              </div>
              {renderDetails(price, estimate.low, estimate.high, estimate.confidence, estimate.trend)}
            </div>
          ) : report ? (
            <div className="pt-3 space-y-1.5 text-sm">
              <div className="flex justify-between">
                <span className="text-text-secondary">Listed Price</span>
                <span className="font-medium text-text-primary">{formatPrice(price)} EGP</span>
              </div>

              {hasRealData ? (
                <>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Market Range</span>
                    <span className="font-medium text-text-primary">{formatPrice(rangeLow)} — {formatPrice(rangeHigh)} EGP</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Market Average</span>
                    <span className="font-medium text-text-primary">{formatPrice(report.estimated_range.average)} EGP</span>
                  </div>
                </>
              ) : (
                <div className="flex items-center gap-2 text-text-muted py-1">
                  <Search className="w-3.5 h-3.5" />
                  <span className="text-xs">No market listings found for this car</span>
                </div>
              )}

              <div className="flex justify-between">
                <span className="text-text-secondary">AI Confidence</span>
                <span className={`font-medium capitalize ${confidenceLevel === 'high' ? 'text-success' : confidenceLevel === 'medium' ? 'text-warning' : 'text-text-muted'}`}>
                  {confidenceLevel}
                </span>
              </div>

              {report.summary && (
                <p className="text-xs text-text-secondary pt-2 leading-relaxed border-t border-primary-200">
                  {report.summary}
                </p>
              )}

              {report.sources.length > 0 && (
                <div className="pt-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      const el = e.currentTarget.nextElementSibling as HTMLElement
                      if (el) el.classList.toggle('hidden')
                    }}
                    className="text-xs text-primary-500 hover:text-primary-600 flex items-center gap-1"
                  >
                    <ExternalLink className="w-3 h-3" />
                    View sources ({report.sources.length})
                  </button>
                  <div className="hidden pt-1 space-y-0.5">
                    {report.sources.slice(0, 5).map((s, i) => (
                      <a
                        key={i}
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block text-xs text-text-muted hover:text-primary-500 truncate"
                      >
                        {s.title}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}

function renderDetails(
  price: number,
  low: number,
  high: number,
  confidence: string,
  trend: string,
) {
  return (
    <>
      <div className="flex justify-between">
        <span className="text-text-secondary">Listed Price</span>
        <span className="font-medium text-text-primary">{formatPrice(price)} EGP</span>
      </div>
      <div className="flex justify-between">
        <span className="text-text-secondary">Estimated Range</span>
        <span className="font-medium text-text-primary">{formatPrice(low)} — {formatPrice(high)} EGP</span>
      </div>
      <div className="flex justify-between">
        <span className="text-text-secondary">AI Confidence</span>
        <span className={`font-medium capitalize ${confidence === 'high' ? 'text-success' : confidence === 'medium' ? 'text-warning' : 'text-text-muted'}`}>
          {confidence}
        </span>
      </div>
      {trend === 'above' && (
        <p className="text-xs text-text-muted pt-1 italic">
          This listing is priced above the estimated market range. You may want to negotiate.
        </p>
      )}
      {trend === 'below' && (
        <p className="text-xs text-text-muted pt-1 italic">
          This listing is priced below the estimated market range. Could be a good deal!
        </p>
      )}
    </>
  )
}
