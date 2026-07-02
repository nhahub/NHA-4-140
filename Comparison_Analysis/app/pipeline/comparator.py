import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

COMPARE_SYSTEM = """You are an expert automotive analyst for the Egyptian car market.
You have analyzed multiple cars individually. Now compare them head-to-head
and produce a final verdict.
REASONING SUPPRESSION: Do NOT include any reasoning, explanation, or thinking text. Output ONLY the raw JSON object.
Return ONLY valid JSON — no markdown, no explanation, no extra text.
"""

COMPARE_HUMAN_TEMPLATE = """Here are the individual analyses for {n} cars being compared:

{car_analyses_text}

{language_instruction}Produce a head-to-head comparison and final verdict using this exact JSON structure:
{{
  "head_to_head": {{
    "best_value": "ad_id of best value car",
    "most_reliable": "ad_id of most reliable car",
    "lowest_running_cost": "ad_id of lowest running cost",
    "best_resale": "ad_id of best resale value"
  }},

  "score_comparison": [
    {{
      "category": "Value for Money",
      "scores": {{"ad_id_1": 8, "ad_id_2": 6, "ad_id_3": 7}}
    }},
    {{
      "category": "Reliability",
      "scores": {{"ad_id_1": 7, "ad_id_2": 9, "ad_id_3": 6}}
    }},
    {{
      "category": "Running Cost",
      "scores": {{"ad_id_1": 8, "ad_id_2": 7, "ad_id_3": 9}}
    }},
    {{
      "category": "Resale Value",
      "scores": {{"ad_id_1": 9, "ad_id_2": 6, "ad_id_3": 7}}
    }},
    {{
      "category": "Overall",
      "scores": {{"ad_id_1": 8, "ad_id_2": 7, "ad_id_3": 7}}
    }}
  ],

  "key_differences": [
    "Specific factual difference between the cars",
    "Specific factual difference between the cars",
    "Specific factual difference between the cars"
  ],

  "verdict": {{
    "winner_ad_id": "ad_id of overall best choice",
    "confidence": "high | medium | low",
    "reasoning": "3-4 sentences explaining why this car wins overall, referencing specific data points from the analyses",
    "runner_up_ad_id": "ad_id of second best, or null if only 2 cars",
    "runner_up_reasoning": "1-2 sentences on why this is second choice"
  }},

  "buyer_persona_match": [
    {{
      "persona": "Family with kids",
      "best_match_ad_id": "ad_id",
      "reason": "1 sentence"
    }},
    {{
      "persona": "Daily commuter",
      "best_match_ad_id": "ad_id",
      "reason": "1 sentence"
    }},
    {{
      "persona": "Budget-conscious buyer",
      "best_match_ad_id": "ad_id",
      "reason": "1 sentence"
    }},
    {{
      "persona": "First-time car owner",
      "best_match_ad_id": "ad_id",
      "reason": "1 sentence"
    }}
  ],

  "final_recommendation": "2-3 sentences of direct, honest advice to the buyer. Which car to buy and why, or what to watch out for before deciding."
}}
"""


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


async def _compare_with_llm(llm, system: str, human: str) -> dict:
    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=human),
    ])
    content = response.content.strip()

    def _ensure_dict(result):
        if isinstance(result, dict):
            return result
        if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict):
            return result[0]
        raise ValueError(f"Expected dict, got {type(result).__name__}")

    try:
        cleaned = _clean_json(content)
        return _ensure_dict(json.loads(cleaned))
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.warning("First compare attempt failed: %s | preview: %s", e, content[:200])

    retry_response = await llm.ainvoke([
        SystemMessage(content=system + "\nCRITICAL: Your previous response contained NO JSON at all. You MUST output ONLY a raw JSON object. Start with { and end with }. NO reasoning, NO explanation, NO markdown, NO text before or after."),
        HumanMessage(content=human),
    ])
    retry_content = retry_response.content.strip()
    try:
        cleaned = _clean_json(retry_content)
        return _ensure_dict(json.loads(cleaned))
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.error("Second compare attempt also failed: %s | content: %s", e, retry_content[:500])
        raise ValueError("LLM failed to return valid JSON after retry")


async def compare(car_analyses: list[dict], primary_llm, fallback_llm, language: str = "en") -> dict:
    lang_instr = ""
    if language == "ar":
        lang_instr = "Respond in Arabic. All text fields in the JSON must be in Arabic.\n\n"

    car_texts = []
    for i, ca in enumerate(car_analyses, 1):
        car_texts.append(
            f"CAR {i}: {ca.get('brand', 'Unknown')} {ca.get('model', 'Unknown')} "
            f"{ca.get('year', '')} — {ca.get('price', 0)} EGP\n"
            f"Analysis: {json.dumps(ca, ensure_ascii=False)}"
        )

    human_msg = COMPARE_HUMAN_TEMPLATE.format(
        n=len(car_analyses),
        car_analyses_text="\n\n".join(car_texts),
        language_instruction=lang_instr,
    )

    try:
        logger.info("Attempting OpenRouter comparison...")
        return await _compare_with_llm(primary_llm, COMPARE_SYSTEM, human_msg)
    except Exception as e:
        logger.warning("OpenRouter comparison failed (%s: %s), falling back to Groq", type(e).__name__, e)
        return await _compare_with_llm(fallback_llm, COMPARE_SYSTEM, human_msg)
