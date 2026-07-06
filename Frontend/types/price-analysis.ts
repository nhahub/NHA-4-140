export interface PriceAnalysisRequest {
  make: string
  model: string
  year: number
}

export interface PriceAnalysisReport {
  make: string
  model: string
  year: number
  estimated_range: {
    low: number
    high: number
    average: number
  }
  confidence: 'high' | 'medium' | 'low'
  summary: string
  currency: string
  sources: { title: string; url: string }[]
}
