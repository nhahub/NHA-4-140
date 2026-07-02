import json
import logging

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

from app.services.comparison.models import ComparisonResult, CarAnalysis
from app.services.comparison.llm_utils import parse_llm_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert automotive analyst for the Egyptian car market.
You have analyzed two cars individually. Now compare them head-to-head
and produce a final verdict.

IMPORTANT RULES:
- Compare only using the supplied analyses. Never invent new facts.
- If the input analyses have low confidence, note that explicitly.
- Explain trade-offs clearly; recommend one vehicle and explain why.
- Note situations where the other vehicle may be the better choice.
- Be honest about uncertainty where input confidence is low.

Return ONLY a valid JSON object — no explanation, no markdown, no extra text.

Your JSON must match this schema exactly:
{
  "winner": "car_a" or "car_b",
  "summary": "2-3 sentence comparison summary highlighting key differences",
  "advantages": {
    "car_a": ["specific advantage of car A over B", "another advantage"],
    "car_b": ["specific advantage of car B over A", "another advantage"]
  },
  "disadvantages": {
    "car_a": ["specific disadvantage of car A vs B"],
    "car_b": ["specific disadvantage of car B vs A"]
  },
  "recommendation": "2-3 sentences of direct advice. Which car to buy and why, referencing specific strengths.",
  "buyer_type": {
    "car_a": "Who car A is best suited for",
    "car_b": "Who car B is best suited for"
  },
  "confidence": 0.0-1.0
}"""

HUMAN_TEMPLATE = """Here are the individual analyses for the two cars being compared:

CAR A ({car_a_brand} {car_a_model} {car_a_year}):
{car_a_json}

CAR B ({car_b_brand} {car_b_model} {car_b_year}):
{car_b_json}

Compare these two analyses and produce a head-to-head comparison with recommendation."""


async def compare(llm: ChatGroq, car_a: CarAnalysis, car_b: CarAnalysis) -> ComparisonResult:
    human_msg = HUMAN_TEMPLATE.format(
        car_a_brand=car_a.brand,
        car_a_model=car_a.model,
        car_a_year=car_a.year,
        car_a_json=json.dumps(car_a.to_dict(), indent=2, ensure_ascii=False),
        car_b_brand=car_b.brand,
        car_b_model=car_b.model,
        car_b_year=car_b.year,
        car_b_json=json.dumps(car_b.to_dict(), indent=2, ensure_ascii=False),
    )

    result = await parse_llm_json(llm, SYSTEM_PROMPT, human_msg)

    comparison = ComparisonResult(
        winner=result.get("winner", "car_a"),
        summary=result.get("summary", ""),
        advantages=result.get("advantages", {"car_a": [], "car_b": []}),
        disadvantages=result.get("disadvantages", {"car_a": [], "car_b": []}),
        recommendation=result.get("recommendation", ""),
        buyer_type=result.get("buyer_type", {"car_a": "", "car_b": ""}),
        confidence=result.get("confidence", 0.5),
    )

    logger.info(
        "Comparison complete: winner=%s, confidence=%.2f",
        comparison.winner, comparison.confidence,
    )
    return comparison
