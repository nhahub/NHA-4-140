import json
import logging
from fastapi import APIRouter, Request
from pydantic import BaseModel

from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.core.duckduckgo import DuckDuckGoSearch

logger = logging.getLogger(__name__)
router = APIRouter(tags=["price-analysis"])


class PriceAnalysisRequest(BaseModel):
    make: str
    model: str
    year: int


PRICE_SYSTEM = """You are an expert automotive analyst for the Egyptian car market.
Analyze the web search results for a car and extract real price data.
Look for actual numbers (prices in EGP) mentioned in the results.
If you find multiple prices, use them to determine the range and average.
If no specific prices are found, set confidence to "low" and all values to 0.

Return ONLY valid JSON — no markdown, no explanation.
"""

PRICE_HUMAN_TEMPLATE = """Web search results for {year} {make} {model} in Egypt:

{search_results}

Based on the search results above, extract price information.
- Look for prices followed by "EGP", "جنيه", "LE", or number ranges
- If you find specific prices, calculate low/high/average from them
- If the snippets mention no prices at all, set all values to 0 and confidence "low"

Return ONLY this JSON:
{{
  "estimated_range": {{"low": <number>, "high": <number>, "average": <number>}},
  "confidence": "high | medium | low",
  "summary": "2-3 sentence summary of what the search results indicate about the price"
}}
"""


@router.post("/price-analysis")
async def price_analysis(body: PriceAnalysisRequest, req: Request):
    make = body.make.strip().lower()
    model = body.model.strip().lower()
    year = body.year
    cache_key = f"price:{make}:{model}:{year}"

    redis = getattr(req.app.state, "redis", None)
    if redis:
        cached = await redis.get_json(cache_key)
        if cached is not None:
            return cached

    searcher = DuckDuckGoSearch()
    search_results = await searcher.search_prices(make, model, year)

    snippets_text = "\n\n".join(
        f"Query: {r['query']}\n{r['snippets']}" for r in search_results if r["snippets"]
    )
    if not snippets_text:
        snippets_text = "No search results found."

    human_msg = PRICE_HUMAN_TEMPLATE.format(
        make=body.make,
        model=body.model,
        year=year,
        search_results=snippets_text,
    )

    llm = getattr(req.app.state, "groq_llm", None)
    if llm:
        try:
            response = await llm.ainvoke([
                SystemMessage(content=PRICE_SYSTEM),
                HumanMessage(content=human_msg),
            ])
            content = response.content.strip()
            if content.startswith("```"):
                content = content[3:]
            if content.startswith("json"):
                content = content[4:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            llm_result = json.loads(content)
        except Exception as e:
            logger.warning("LLM price analysis failed: %s", e)
            llm_result = None
    else:
        llm_result = None

    if llm_result and "estimated_range" in llm_result:
        report = {
            "make": body.make,
            "model": body.model,
            "year": year,
            "estimated_range": llm_result["estimated_range"],
            "confidence": llm_result.get("confidence", "low"),
            "summary": llm_result.get("summary", ""),
            "currency": "EGP",
            "sources": _extract_sources(search_results),
        }
    else:
        fallback = _fallback_estimate(search_results)
        report = {
            "make": body.make,
            "model": body.model,
            "year": year,
            "estimated_range": fallback["estimated_range"],
            "confidence": "low",
            "summary": fallback["summary"],
            "currency": "EGP",
            "sources": _extract_sources(search_results),
        }

    if redis:
        await redis.set_json(cache_key, report, ttl=3600)

    return report


def _extract_sources(search_results: list[dict]) -> list[dict]:
    seen = set()
    sources = []
    for r in search_results:
        for line in r.get("snippets", "").split("\n"):
            if "(" in line and line.endswith(")"):
                url = line[line.rindex("(") + 1 : -1]
                if url and url not in seen:
                    seen.add(url)
                    title = line.split(":", 1)[0].lstrip("- ") if ":" in line else "Search result"
                    sources.append({"title": title, "url": url})
    return sources[:10]


def _fallback_estimate(search_results: list[dict]) -> dict:
    snippets_text = "\n".join(r.get("snippets", "") for r in search_results if r["snippets"])
    return {
        "estimated_range": {"low": 0, "high": 0, "average": 0},
        "summary": snippets_text[:500] if snippets_text else "No market data available for this car.",
    }
