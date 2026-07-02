export interface CarAnalysis {
  ad_id: string
  brand: string
  model: string
  year: number
  price: number
  condition: string
  cover_image_url: string
  pros: string[]
  cons: string[]
  scores: {
    value_for_money: number
    reliability: number
    running_cost: number
    resale_value: number
    overall: number
  }
  photo_analysis: string
  market_context: string
  reliability_summary: string
  best_for: string
  red_flags: string[]
  spare_parts_availability: string
  service_centers_egypt: string
}

export interface ScoreComparison {
  category: string
  scores: Record<string, number>
}

export interface Verdict {
  winner_ad_id: string
  confidence: 'high' | 'medium' | 'low'
  reasoning: string
  runner_up_ad_id: string | null
  runner_up_reasoning: string | null
}

export interface BuyerPersonaMatch {
  persona: string
  best_match_ad_id: string
  reason: string
}

export interface ResearchSource {
  ad_id: string
  brand: string
  model: string
  sources: {
    title: string
    url: string
  }[]
}

export interface ComparisonReport {
  report_id: string
  generated_at: string
  cars_count: number
  cars: CarAnalysis[]
  head_to_head: {
    best_value: string
    most_reliable: string
    lowest_running_cost: string
    best_resale: string
  }
  score_comparison: ScoreComparison[]
  key_differences: string[]
  verdict: Verdict
  buyer_persona_match: BuyerPersonaMatch[]
  final_recommendation: string
  research_sources: ResearchSource[]
}

export interface CompareRequest {
  ad_ids: string[]
  language?: 'en' | 'ar'
}

export interface CompareSSEEvent {
  type: 'status' | 'progress' | 'report' | 'error' | 'done'
  content: any
}
