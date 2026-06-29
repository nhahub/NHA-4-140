'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '@/lib/api'
import type { Ad, AdFilters, AdListResponse } from '@/types/ad'

interface UseAdsOptions {
  initialFilters?: AdFilters
  autoFetch?: boolean
}

export function useAds(options: UseAdsOptions = {}) {
  const { initialFilters = {}, autoFetch = true } = options
  const [ads, setAds] = useState<Ad[]>([])
  const [filters, setFilters] = useState<AdFilters>(initialFilters)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const isFirstRender = useRef(true)

  const fetchAds = useCallback(async (pageNum: number, append: boolean = false) => {
    setIsLoading(true)
    try {
      const data = await api.get<AdListResponse>('/ads', { ...filters, page: pageNum, limit: 12 })
      if (append) {
        setAds((prev) => [...prev, ...data.ads])
      } else {
        setAds(data.ads)
      }
      setTotalPages(data.total_pages)
      setHasMore(pageNum < data.total_pages)
    } catch {
      // handle error silently
    } finally {
      setIsLoading(false)
    }
  }, [filters])

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }
    if (autoFetch) {
      setPage(1)
      fetchAds(1)
    }
  }, [filters, autoFetch])

  const loadMore = useCallback(() => {
    if (!isLoading && hasMore) {
      const nextPage = page + 1
      setPage(nextPage)
      fetchAds(nextPage, true)
    }
  }, [isLoading, hasMore, page, fetchAds])

  const updateFilters = useCallback((newFilters: AdFilters) => {
    setFilters((prev) => ({ ...prev, ...newFilters }))
  }, [])

  const resetFilters = useCallback(() => {
    setFilters(initialFilters)
  }, [initialFilters])

  return { ads, filters, isLoading, hasMore, loadMore, updateFilters, resetFilters }
}
