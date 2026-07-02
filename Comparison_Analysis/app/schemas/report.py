from typing import TypedDict, List


class CarAnalysis(TypedDict):
    ad_id: str
    brand: str
    model: str
    year: int
    price: float
    condition: str
    cover_image_url: str
    pros: List[str]
    cons: List[str]
    scores: dict
    market_context: str
    reliability_summary: str
    best_for: str
    red_flags: List[str]
    spare_parts_availability: str
    service_centers_egypt: str


class ScoreComparison(TypedDict):
    category: str
    scores: dict


class Verdict(TypedDict):
    winner_ad_id: str
    confidence: str
    reasoning: str
    runner_up_ad_id: str | None
    runner_up_reasoning: str | None


class BuyerPersonaMatch(TypedDict):
    persona: str
    best_match_ad_id: str
    reason: str


class ResearchSource(TypedDict):
    ad_id: str
    brand: str
    model: str
    sources: List[dict]


class ComparisonReport(TypedDict):
    report_id: str
    generated_at: str
    cars_count: int
    cars: List[CarAnalysis]
    head_to_head: dict
    score_comparison: List[ScoreComparison]
    key_differences: List[str]
    verdict: Verdict
    buyer_persona_match: List[BuyerPersonaMatch]
    final_recommendation: str
    research_sources: List[ResearchSource]
