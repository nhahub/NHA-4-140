import logging

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

from app.services.comparison.models import StructuredAnalysis
from app.services.comparison.llm_utils import parse_llm_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert automotive analyst specializing in the Egyptian car market.
Analyze the following car listing using ONLY the structured data provided.
Be objective, data-driven, and specific to the Egyptian market context.

Return ONLY a valid JSON object — no explanation, no markdown, no extra text.

Your JSON must match this schema exactly:
{
  "summary": "2-3 sentence summary of this car's overall proposition",
  "pros": ["specific pro based on data", "specific pro based on data", "specific pro based on data"],
  "cons": ["specific con based on data", "specific con based on data", "specific con based on data"],
  "risks": ["specific risk or concern", "specific risk or concern"],
  "maintenance_expectations": "1-2 sentences on expected maintenance costs and availability of parts in Egypt",
  "value_for_money": "1-2 sentences assessing value relative to price",
  "price_fairness": "fair | slightly_overpriced | overpriced | bargain",
  "suitable_buyer_type": "Who this car is best suited for (family, single, daily commute, business, etc.)",
  "overall_score": 0-100,
  "condition_score": 0-100,
  "price_score": 0-100,
  "reliability_score": 0-100,
  "market_reputation": "excellent | good | average | poor | unknown",
  "confidence": 0.0-1.0
}

IMPORTANT RULES:
- Never invent facts. Base everything on the provided data.
- If the data is insufficient to assess something, score it neutrally and note it in the summary.
- Be honest about limitations in the data."""

HUMAN_TEMPLATE = """CAR LISTING DATA:
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
Color: {color}
Special Conditions: {special_conditions}
Description: {description}"""


async def analyze_car(llm: ChatGroq, ad: dict) -> StructuredAnalysis:
    human_msg = HUMAN_TEMPLATE.format(
        brand=ad.get("brand", "Unknown"),
        model=ad.get("model", "Unknown"),
        year=ad.get("year", ""),
        price=ad.get("price", 0),
        condition=ad.get("condition", "Unknown"),
        km_driven=ad.get("km_driven", 0),
        fuel_type=ad.get("fuel_type", "Unknown"),
        transmission=ad.get("transmission", "Unknown"),
        body_type=ad.get("body_type", "Unknown"),
        city=ad.get("city", "Unknown"),
        cc_range=ad.get("cc_range", "N/A"),
        color=ad.get("color", "N/A"),
        special_conditions=ad.get("special_conditions", "N/A"),
        description=ad.get("description", "N/A"),
    )

    result = await parse_llm_json(llm, SYSTEM_PROMPT, human_msg)

    analysis = StructuredAnalysis(
        summary=result.get("summary", ""),
        pros=result.get("pros", []),
        cons=result.get("cons", []),
        risks=result.get("risks", []),
        maintenance_expectations=result.get("maintenance_expectations", ""),
        value_for_money=result.get("value_for_money", ""),
        price_fairness=result.get("price_fairness", "fair"),
        suitable_buyer_type=result.get("suitable_buyer_type", ""),
        overall_score=result.get("overall_score", 50),
        condition_score=result.get("condition_score", 50),
        price_score=result.get("price_score", 50),
        reliability_score=result.get("reliability_score", 50),
        market_reputation=result.get("market_reputation", "unknown"),
        confidence=result.get("confidence", 0.5),
    )

    logger.info(
        "Structured analysis complete for %s %s %s (score=%d, confidence=%.2f)",
        ad.get("brand"), ad.get("model"), ad.get("year"),
        analysis.overall_score, analysis.confidence,
    )
    return analysis
