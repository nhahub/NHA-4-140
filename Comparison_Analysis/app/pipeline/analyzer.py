import json
import logging
import time
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.ai_metrics import (
    llm_calls_total, llm_tokens_total, llm_latency_seconds, llm_cost_total,
    llm_fallback_total,
)

logger = logging.getLogger(__name__)

ANALYZE_SYSTEM = """You are an expert automotive analyst specializing in the Egyptian car market.
Analyze the following car listing using both the listing data and web research
provided. Be objective, data-driven, and specific to the Egyptian market context.

IMPORTANT - REASONING SUPPRESSION: Do NOT include any reasoning, explanation, or thinking text. Output ONLY the raw JSON object.
You must return ONLY a valid JSON object — no explanation, no markdown, no extra text.
"""

ANALYZE_HUMAN_TEMPLATE = """CAR LISTING DATA:
Brand: {brand}
Model: {model}
Year: {year}
Price: {price} EGP
Condition: {condition}
KM Driven: {km_driven}
Fuel Type: {fuel_type}
Transmission: {transmission}
Body Type: {body_type}
City: {city}
CC Range: {cc_range}
Special Conditions: {special_conditions}
Description: {description}

WEB RESEARCH RESULTS:

Reliability & Common Problems:
{reliability_answer}
Sources: {reliability_sources}

Market Price & Resale Value:
{price_answer}
Sources: {price_sources}

Owner Reviews & Reputation:
{reputation_answer}
Sources: {reputation_sources}

{language_instruction}Analyze this car and return this exact JSON structure:
{{
  "ad_id": "{ad_id}",
  "brand": "{brand}",
  "model": "{model}",
  "year": {year},
  "price": {price},
  "cover_image_url": "{cover_image_url}",

  "condition": "{condition}",

  "pros": [
    "specific pro based on data",
    "specific pro based on data",
    "specific pro based on data"
  ],
  "cons": [
    "specific con based on data",
    "specific con based on data",
    "specific con based on data"
  ],

  "scores": {{
    "value_for_money": 0-10,
    "reliability": 0-10,
    "running_cost": 0-10,
    "resale_value": 0-10,
    "overall": 0-10
  }},

  "photo_analysis": "2-3 sentences analyzing the car photos: exterior condition, visible damage (scratches, dents, rust), tire wear, cleanliness, any visual red flags. Base this on the image provided above.",

  "market_context": "2-3 sentences on how this car's price compares to market, whether it's overpriced/fair/bargain",
  "reliability_summary": "2-3 sentences on known issues and reliability track record for this model/year",
  "best_for": "1 sentence — who is this car ideal for (family, single, business, daily commute, etc.)",
  "red_flags": ["any serious issues to watch out for based on research, or empty array if none"],
  "spare_parts_availability": "good | fair | poor",
  "service_centers_egypt": "good | fair | poor"
}}
"""


def _sources_text(research: dict) -> str:
    sources = research.get("results", [])
    if not sources:
        return "No sources available."
    lines = []
    for s in sources[:3]:
        title = s.get("title", "Untitled")
        content = s.get("content", "")
        lines.append(f"- {title}: {content[:200]}")
    return "\n".join(lines)


def _build_prompt(ad: dict, research: dict, language: str) -> str:
    lang_instr = ""
    if language == "ar":
        lang_instr = "Respond in Arabic. All text fields in the JSON must be in Arabic.\n\n"

    reliability_research = research.get("reliability_research", {})
    price_research = research.get("price_research", {})
    reputation_research = research.get("reputation_research", {})

    return ANALYZE_HUMAN_TEMPLATE.format(
        ad_id=ad.get("id", ""),
        brand=ad.get("brand", ""),
        model=ad.get("model", ""),
        year=ad.get("year", ""),
        price=ad.get("price", 0),
        cover_image_url=ad.get("cover_image_url", ""),
        condition=ad.get("condition", ""),
        km_driven=ad.get("km_driven", ""),
        fuel_type=ad.get("fuel_type", ""),
        transmission=ad.get("transmission", ""),
        body_type=ad.get("body_type", ""),
        city=ad.get("city", ""),
        cc_range=ad.get("cc_range", ""),
        special_conditions=ad.get("special_conditions", ""),
        description=ad.get("description", ""),
        reliability_answer=reliability_research.get("tavily_answer", "Research unavailable."),
        reliability_sources=_sources_text(reliability_research),
        price_answer=price_research.get("tavily_answer", "Research unavailable."),
        price_sources=_sources_text(price_research),
        reputation_answer=reputation_research.get("tavily_answer", "Research unavailable."),
        reputation_sources=_sources_text(reputation_research),
        language_instruction=lang_instr,
    )


def _build_multimodal_content(text: str, image_url: str | None = None) -> str | list:
    if not image_url:
        return text
    return [
        {"type": "text", "text": text},
        {"type": "image_url", "image_url": {"url": image_url}},
    ]


def _get_llm_provider(llm) -> str:
    return getattr(llm, "_llm_type", None) or llm.__class__.__name__.lower().replace("chat", "").replace("groq", "groq")


async def _parse_llm_json(llm, system: str, human: str, image_url: str | None = None, task_type: str = "unknown") -> dict:
    def _ensure_dict(result):
        if isinstance(result, dict):
            return result
        if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict):
            return result[0]
        raise ValueError(f"Expected dict, got {type(result).__name__}")

    provider = _get_llm_provider(llm)
    human_content = _build_multimodal_content(human, image_url)

    start = time.monotonic()
    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=human_content),
    ])
    duration = time.monotonic() - start
    content = response.content.strip()

    usage = getattr(response, "usage_metadata", None) or {}
    prompt_tokens = usage.get("input_tokens", 0) or 0
    completion_tokens = usage.get("output_tokens", 0) or 0

    llm_calls_total.labels(service="comparison_analysis", provider=provider, model="", task_type=task_type).inc()
    llm_tokens_total.labels(service="comparison_analysis", provider=provider, type="prompt").inc(prompt_tokens)
    llm_tokens_total.labels(service="comparison_analysis", provider=provider, type="completion").inc(completion_tokens)
    llm_latency_seconds.labels(service="comparison_analysis", provider=provider, model="", task_type=task_type).observe(duration)

    try:
        cleaned = _clean_json(content)
        return _ensure_dict(json.loads(cleaned))
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.warning("First LLM attempt failed: %s | preview: %s", e, content[:200])

    retry_human_content = _build_multimodal_content(human, image_url)
    retry_response = await llm.ainvoke([
        SystemMessage(content=system + "\nCRITICAL: Your previous response contained NO JSON at all. You MUST output ONLY a raw JSON object. Start with { and end with }. NO reasoning, NO explanation, NO markdown, NO text before or after."),
        HumanMessage(content=retry_human_content),
    ])
    retry_content = retry_response.content.strip()
    try:
        cleaned = _clean_json(retry_content)
        return _ensure_dict(json.loads(cleaned))
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.error("Second LLM attempt also failed: %s | content: %s", e, retry_content[:500])
        raise ValueError("LLM failed to return valid JSON after retry")


def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text[3:]
    if text.startswith("json"):
        text = text[4:]
    text = text.strip()
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if not text:
        return text

    # Try raw_decode from each {/[ position; prefer objects over arrays
    decoder = json.JSONDecoder()
    candidates = []
    positions = [i for i, ch in enumerate(text) if ch in ("{", "[")]
    for start in positions:
        try:
            obj, end = decoder.raw_decode(text, start)
            priority = 2 if text[start] == "{" else 1
            candidates.append((priority, end - start, text[start:end]))
        except json.JSONDecodeError:
            continue

    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return candidates[0][2]

    return text.strip()


async def analyze_car(ad: dict, research: dict, primary_llm, fallback_llm, language: str = "en") -> dict:
    human_msg = _build_prompt(ad, research, language)
    cover_image = ad.get("cover_image_url") or None

    try:
        logger.info("Attempting OpenRouter analysis for %s %s", ad.get("brand"), ad.get("model"))
        return await _parse_llm_json(primary_llm, ANALYZE_SYSTEM, human_msg, cover_image, task_type="car_analysis")
    except Exception as e:
        logger.warning("OpenRouter failed (%s: %s), falling back to Groq for %s %s", type(e).__name__, e, ad.get("brand"), ad.get("model"))
        llm_fallback_total.labels(service="comparison_analysis", task_type="car_analysis", from_provider="openrouter", to_provider="groq").inc()
        return await _parse_llm_json(fallback_llm, ANALYZE_SYSTEM, human_msg, task_type="car_analysis")
