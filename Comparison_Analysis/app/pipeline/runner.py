import asyncio
from typing import AsyncGenerator

from app.schemas.request import CompareRequest
from app.db.queries import fetch_ads_for_comparison
from app.pipeline.analyzer import analyze_car
from app.pipeline.comparator import compare
from app.pipeline.report_builder import build_report


async def run(request: CompareRequest, app_state) -> AsyncGenerator[dict, None]:
    cache_key = frozenset(request.ad_ids)
    if cache_key in app_state.report_cache:
        cached = app_state.report_cache[cache_key]
        yield {"type": "report", "content": cached}
        yield {"type": "done", "content": None}
        return

    pool = app_state.pool
    openrouter_llm = app_state.llm
    groq_llm = app_state.groq_llm
    tavily = app_state.tavily

    # Stage 1: Fetch ads
    yield {"type": "status", "content": "Loading car details..."}
    try:
        ads = await fetch_ads_for_comparison(pool, request.ad_ids)
    except ValueError as e:
        yield {"type": "error", "content": str(e)}
        yield {"type": "done", "content": None}
        return

    # Stage 2: Concurrent Tavily research
    research_tasks = []
    for ad in ads:
        yield {"type": "status", "content": f"Researching {ad['brand']} {ad['model']}..."}
        research_tasks.append(tavily.research_car(ad))

    research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
    processed_results = []
    for r in research_results:
        if isinstance(r, Exception):
            processed_results.append({
                "ad_id": "",
                "brand": "",
                "model": "",
                "year": "",
                "reliability_research": {"tavily_answer": "Research unavailable.", "sources": []},
                "price_research": {"tavily_answer": "Research unavailable.", "sources": []},
                "reputation_research": {"tavily_answer": "Research unavailable.", "sources": []},
            })
        else:
            processed_results.append(r)

    # Stage 3: Parallel LLM analysis per car
    yield {"type": "status", "content": f"Analyzing {len(ads)} cars..."}

    async def _analyze_one(ad: dict, research: dict) -> dict | None:
        try:
            return await analyze_car(ad, research, openrouter_llm, groq_llm, request.language)
        except Exception:
            return None

    analysis_tasks = [_analyze_one(ad, research) for ad, research in zip(ads, processed_results)]
    results = await asyncio.gather(*analysis_tasks)

    car_analyses = []
    for i, (ad, result) in enumerate(zip(ads, results)):
        if result is None:
            yield {"type": "error", "content": f"Analysis failed for {ad['brand']} {ad['model']}."}
            yield {"type": "done", "content": None}
            return
        car_analyses.append(result)
        yield {
            "type": "progress",
            "content": {
                "current": i + 1,
                "total": len(ads),
                "label": f"{ad['brand']} {ad['model']} analyzed",
            },
        }

    # Stage 4: Single LLM comparison call
    yield {"type": "status", "content": "Writing final verdict..."}
    try:
        comparison_result = await compare(car_analyses, openrouter_llm, groq_llm, request.language)
    except Exception:
        yield {"type": "error", "content": "Comparison analysis failed. Please try again."}
        yield {"type": "done", "content": None}
        return

    # Stage 5: Assemble report
    report = build_report(ads, car_analyses, comparison_result, processed_results)

    # Cache the report
    app_state.report_cache[cache_key] = report
    if len(app_state.report_cache) >= 50:
        oldest_key = next(iter(app_state.report_cache))
        del app_state.report_cache[oldest_key]

    yield {"type": "report", "content": report}
    yield {"type": "done", "content": None}
