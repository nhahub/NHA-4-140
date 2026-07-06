import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

COMPARISON_KEYS = {"head_to_head", "score_comparison", "key_differences", "verdict", "buyer_persona_match", "final_recommendation"}

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


def _has_comparison_keys(d: dict) -> bool:
    return "head_to_head" in d and "verdict" in d


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

    decoder = json.JSONDecoder()
    candidates = []
    positions = [i for i, ch in enumerate(text) if ch in ("{", "[")]
    for start in positions:
        try:
            obj, end = decoder.raw_decode(text, start)
            priority = 2 if text[start] == "{" else 1
            if isinstance(obj, dict) and _has_comparison_keys(obj):
                priority += 10
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
        result = _ensure_dict(json.loads(cleaned))
        if _has_comparison_keys(result):
            return result
        logger.warning("First compare response missing comparison keys (has: %s)", list(result.keys()))
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.warning("First compare attempt failed: %s | preview: %s", e, content[:200])

    retry_system = system + "\nCRITICAL: Your previous response did not contain the required fields. You MUST output a JSON object with these exact top-level keys: head_to_head, score_comparison, key_differences, verdict, buyer_persona_match, final_recommendation. Start with { and end with }. NO reasoning, NO explanation, NO markdown."
    retry_response = await llm.ainvoke([
        SystemMessage(content=retry_system),
        HumanMessage(content=human),
    ])
    retry_content = retry_response.content.strip()
    try:
        cleaned = _clean_json(retry_content)
        result = _ensure_dict(json.loads(cleaned))
        if _has_comparison_keys(result):
            return result
        logger.warning("Second compare response also missing comparison keys (has: %s)", list(result.keys()))
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.error("Second compare attempt also failed: %s | content: %s", e, retry_content[:500])

    raise ValueError("LLM failed to return valid comparison JSON after retry")


def _build_fallback_comparison(car_analyses: list[dict]) -> dict:
    ad_ids = [ca.get("ad_id", f"car_{i}") for i, ca in enumerate(car_analyses)]
    scores = {}
    for ca in car_analyses:
        aid = ca.get("ad_id", "")
        cs = ca.get("scores", {})
        scores[aid] = cs

    score_comparison = []
    categories = ["Value for Money", "Reliability", "Running Cost", "Resale Value", "Overall"]
    score_keys = ["value_for_money", "reliability", "running_cost", "resale_value", "overall"]
    for cat, sk in zip(categories, score_keys):
        entry = {"category": cat, "scores": {}}
        for aid in ad_ids:
            entry["scores"][aid] = scores.get(aid, {}).get(sk, 5)
        score_comparison.append(entry)

    def _best_ad(key: str, higher=True) -> str:
        best_id = ad_ids[0]
        best_val = scores.get(ad_ids[0], {}).get(key, 0)
        for aid in ad_ids[1:]:
            val = scores.get(aid, {}).get(key, 0)
            if higher and val > best_val:
                best_val, best_id = val, aid
            elif not higher and val < best_val:
                best_val, best_id = val, aid
        return best_id

    sorted_ids = sorted(ad_ids, key=lambda aid: scores.get(aid, {}).get("overall", 0), reverse=True)
    winner = sorted_ids[0] if sorted_ids else ""
    runner_up = sorted_ids[1] if len(sorted_ids) > 1 else None

    key_diffs = []
    for ca in car_analyses:
        for flag in ca.get("red_flags", []):
            key_diffs.append(f"{ca.get('brand', '')} {ca.get('model', '')}: {flag}")

    buyer_personas = [
        {"persona": "Family with kids", "best_match_ad_id": winner, "reason": f"Best overall score of {scores.get(winner, {}).get('overall', 'N/A')}/10."},
        {"persona": "Daily commuter", "best_match_ad_id": _best_ad("running_cost", higher=False), "reason": "Lowest running cost among the compared cars."},
        {"persona": "Budget-conscious buyer", "best_match_ad_id": _best_ad("value_for_money"), "reason": "Best value-for-money score."},
        {"persona": "First-time car owner", "best_match_ad_id": _best_ad("reliability"), "reason": "Highest reliability score."},
    ]

    winner_ca = next((ca for ca in car_analyses if ca.get("ad_id") == winner), car_analyses[0] if car_analyses else {})
    final_rec = f"Based on the analysis, {winner_ca.get('brand', '')} {winner_ca.get('model', '')} (score: {scores.get(winner, {}).get('overall', 'N/A')}/10) is the recommended choice. Consider your priorities around value, reliability, and running costs."

    return {
        "head_to_head": {
            "best_value": _best_ad("value_for_money"),
            "most_reliable": _best_ad("reliability"),
            "lowest_running_cost": _best_ad("running_cost", higher=False),
            "best_resale": _best_ad("resale_value"),
        },
        "score_comparison": score_comparison,
        "key_differences": key_diffs if key_diffs else ["No specific key differences flagged in the analysis."],
        "verdict": {
            "winner_ad_id": winner,
            "confidence": "medium",
            "reasoning": f"After comparing all available data, {winner_ca.get('brand', '')} {winner_ca.get('model', '')} leads with an overall score of {scores.get(winner, {}).get('overall', 'N/A')}/10. The decision is based on the aggregated scores from the individual car analyses.",
            "runner_up_ad_id": runner_up,
            "runner_up_reasoning": f"The runner-up scored lower on overall metrics.",
        },
        "buyer_persona_match": buyer_personas,
        "final_recommendation": final_rec,
    }


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
        try:
            return await _compare_with_llm(fallback_llm, COMPARE_SYSTEM, human_msg)
        except Exception as e2:
            logger.error("Groq comparison also failed (%s: %s), using fallback comparison", type(e2).__name__, e2)
            return _build_fallback_comparison(car_analyses)
