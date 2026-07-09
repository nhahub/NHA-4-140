from uuid import uuid4
from datetime import datetime


def extract_unique_sources(research: dict) -> list[dict]:
    seen_urls = set()
    sources = []
    for key in ("reliability_research", "price_research", "reputation_research"):
        for s in research.get(key, {}).get("results", []):
            url = s.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "title": s.get("title", "Untitled"),
                    "url": url,
                })
    return sources


def build_report(
    ads: list[dict],
    car_analyses: list[dict],
    comparison: dict,
    research_results: list[dict],
) -> dict:
    return {
        "report_id": str(uuid4()),
        "generated_at": datetime.utcnow().isoformat(),
        "cars_count": len(ads),
        "cars": car_analyses,
        "head_to_head": comparison.get("head_to_head", {}),
        "score_comparison": comparison.get("score_comparison", []),
        "key_differences": comparison.get("key_differences", []),
        "verdict": comparison.get("verdict", {}),
        "buyer_persona_match": comparison.get("buyer_persona_match", []),
        "final_recommendation": comparison.get("final_recommendation", ""),
        "research_sources": [
            {
                "ad_id": r["ad_id"],
                "brand": r["brand"],
                "model": r["model"],
                "sources": extract_unique_sources(r),
            }
            for r in research_results
        ],
    }
