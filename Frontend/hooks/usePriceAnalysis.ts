'use client'

import { useState, useCallback } from 'react'
import type { PriceAnalysisReport } from '@/types/price-analysis'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export function usePriceAnalysis() {
  const [report, setReport] = useState<PriceAnalysisReport | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchReport = useCallback(async (make: string, model: string, year: number) => {
    setIsLoading(true)
    setError(null)
    setReport(null)

    try {
      const res = await fetch(`${API_URL}/price-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ make, model, year }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.error || `Request failed (${res.status})`)
      }

      const data: PriceAnalysisReport = await res.json()
      setReport(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch price analysis')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setReport(null)
    setIsLoading(false)
    setError(null)
  }, [])

  return { report, isLoading, error, fetchReport, reset }
}
