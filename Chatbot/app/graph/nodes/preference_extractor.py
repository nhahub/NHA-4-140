import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.graph.state import CarsChatState
from app.data.brand_origins import format_brand_origins_prompt

logger = logging.getLogger(__name__)

# ── Pass 1: Need inference ──────────────────────────────────────────

NEED_INFERENCE_SYSTEM = """You are a car-need analyzer. Determine WHAT the user needs
from their message — either from explicit car keywords or implied from use-case language.

STRICT RULE — JSON field conventions:
- null  = "not mentioned in this message — leave existing value unchanged"
- []    = "explicitly cleared by the user — set to empty list"
- [val] = "user stated this value — append to existing list"

1. Infer the use case from language like:
   - family, kids, school run, عائلة, أطفال → family
   - travel, road trip, highway, سفر, طريق سريع → travel
   - big, spacious, roomy, كبير, واسع → large_vehicle
   - cheap, economical, budget, رخيص, اقتصادي → budget
   - luxury, premium, فاخر, بريميوم → luxury
   - off-road, 4x4, adventure, دفع رباعي, مغامرة → offroad

2. Map inferred needs to matching body types:
   - family / travel → ["suv", "mpv", "minivan", "station_wagon"]
   - large_vehicle → ["suv", "pickup", "van"]
   - offroad → ["suv", "pickup"]
   - budget → ["hatchback", "sedan"]
   - luxury → ["sedan", "coupe", "convertible"]

3. Extract explicit rejections ("not X", "I don't want X", "مش عايز"):
   - body types, brands, models

Return ONLY JSON — no explanation, no markdown:
{
  "has_preference_content": true/false,
  "inferred_use_case": "family" | "travel" | "large_vehicle" | "budget" | "luxury" | "offroad" | null,
  "inferred_from_text": ["family", "travel"],
  "inferred_body_types": ["suv", "mpv"],
  "inferred_min_seats": null,
  "explicit_rejections": {
    "body_types": ["sedan"],
    "brands": [],
    "models": []
  }
}

User message: "{message}"
Existing preferences: {preferences_json}"""

# ── Pass 2: Preference extraction ──────────────────────────────────

EXTRACT_SYSTEM_PROMPT = """You are a preference extraction engine for a car marketplace.
Extract any car preference signals from the user message.
Merge with existing preferences — never clear a previously set value
unless the user explicitly contradicts it.

STRICT RULE — JSON field conventions:
- null  = "not mentioned in this message — leave the existing value unchanged"
- []    = "explicitly cleared by the user — set to empty list"
- [val] = "user stated this value — append to existing list"

CRITICAL: When the user mentions a car origin/country (e.g., "German car",
"Japanese car", "American car", "European car", "Korean car", "Italian car"),
expand it to the actual brand names in preferred_brands using this mapping:
{brand_origins_prompt}

Exclusion rules:
- If the user says "not X", "I don't want X", "X isn't what I need",
  add X to the corresponding excluded_* list.
- Exclusion takes priority over inclusion. If they say "sedan is not
  what I want", do NOT add sedan to preferred_body_types.

Inference rules (apply ONLY if available):
- {inference_context}
- Put inferred body types into inferred_body_types, NOT preferred_body_types.
  preferred_body_types is for explicitly stated preferences only.

Existing preferences:
{current_preferences_json}

Extract these fields (use null if not mentioned):
{{
  "budget_min": null,
  "budget_max": null,
  "preferred_brands": [],
  "preferred_body_types": [],
  "preferred_fuel_types": [],
  "preferred_transmission": null,
  "preferred_cities": [],
  "max_km_driven": null,
  "year_min": null,
  "year_max": null,
  "use_case": null,
  "is_seller": false,
  "seller_car_brand": null,
  "seller_car_model": null,
  "seller_car_year": null,
  "seller_asking_price": null,
  "seller_intent": null,
  "inferred_body_types": [],
  "inferred_min_seats": null,
  "inferred_use_case": null,
  "excluded_body_types": [],
  "excluded_brands": [],
  "excluded_models": []
}}

User message: "{message}"
"""


def _is_trivial_message(message: str) -> bool:
    """Fast heuristic gate to skip Pass 1 for messages with no preference content."""
    words = message.strip().split()
    if len(words) < 3:
        return True
    preference_keywords = [
        "car", "cars", "buy", "sell", "big", "small", "family", "travel",
        "need", "want", "look", "search", "find", "recommend",
        "budget", "price", "suv", "sedan", "hatchback", "jeep", "truck",
        "automatic", "manual", "diesel", "petrol", "electric", "hybrid",
        "new", "used", "cheap", "expensive", "good", "best", "show",
        # Arabic
        "عربية", "عربيه", "سيارة", "سياره", "بيع", "شراء", "عايز", "عاوز",
        "كبير", "صغير", "عائلة", "سفر", "كبيرة", "صغيرة",
        "محرك", "بنزين", "ديزل", "كهرباء", "هجين",
        "اتوماتيك", "مانيوال", "مستعمل", "جديد", "رخيص", "غالي",
    ]
    text_lower = message.lower()
    return not any(kw in text_lower for kw in preference_keywords)


async def _inference_pass(message: str, prefs: dict, llm_router) -> dict | None:
    """Pass 1: infer needs from use-case language. Returns None if skipped."""
    if _is_trivial_message(message):
        return None

    prefs_json = json.dumps(prefs, ensure_ascii=False, default=str)
    system_msg = SystemMessage(content=NEED_INFERENCE_SYSTEM.format(
        message=message,
        preferences_json=prefs_json,
    ))
    try:
        response = await llm_router.ainvoke_task("preference_extractor", [
            system_msg,
            HumanMessage(content=message),
        ])
        result = json.loads(
            response.content.strip().removeprefix("```json").removesuffix("```").strip()
        )
        if result.get("has_preference_content"):
            return result
    except Exception as e:
        logger.warning("Need inference pass failed: %s: %s", type(e).__name__, str(e)[:200])
    return None


def _merge_preferences(merged: dict, extracted: dict) -> dict:
    """Three-phase merge: exclusions, inferences, explicit preferences.

    STRICT RULE — JSON field conventions:
    - null  = "not mentioned in this message — leave existing value unchanged"
    - []    = "explicitly cleared by the user — set to empty list"
    - [val] = "user stated this value — append to existing list"
    """
    for key, val in extracted.items():
        if val is None:
            continue

        if isinstance(val, list):
            # Empty list = explicit clear
            if not val:
                merged[key] = []
                continue

            # Phase 1: Exclusions — also remove from corresponding positive list
            if key.startswith("excluded_"):
                existing = merged.get(key, [])
                for item in val:
                    if item not in existing:
                        existing.append(item)
                merged[key] = existing
                # Remove from positive counterpart
                positive_key = key.replace("excluded_", "preferred_")
                if positive_key in merged and isinstance(merged.get(positive_key), list):
                    merged[positive_key] = [x for x in merged[positive_key] if x not in val]
                # Also remove from inferred counterpart
                inferred_key = key.replace("excluded_", "inferred_")
                if inferred_key in merged and isinstance(merged.get(inferred_key), list):
                    merged[inferred_key] = [x for x in merged[inferred_key] if x not in val]

            # Phase 2-3: Inferred or explicit — append
            else:
                existing = merged.get(key, [])
                if not isinstance(existing, list):
                    existing = []
                for item in val:
                    if item not in existing:
                        existing.append(item)
                merged[key] = existing

        else:
            # Scalar fields
            if key == "is_seller":
                merged[key] = val
            else:
                merged[key] = val

    return merged


async def preference_extractor_node(state: CarsChatState, config: RunnableConfig) -> dict:
    llm_router = config["configurable"].get("llm_router")
    llm_fast = config["configurable"].get("llm_fast")
    pool = config["configurable"].get("db_pool")

    if not state.get("messages"):
        return {}

    last_message = state["messages"][-1].content if state["messages"] else ""
    current_prefs = state.get("preferences", {})

    # ── Pass 1: Need inference ───────────────────────────────────────
    inference_result = None
    if llm_router:
        inference_result = await _inference_pass(last_message, current_prefs, llm_router)

    # ── Build inference context for Pass 2 ────────────────────────────
    inference_context = ""
    if inference_result:
        inf_types = inference_result.get("inferred_body_types", [])
        inf_seats = inference_result.get("inferred_min_seats")
        use_case = inference_result.get("inferred_use_case")
        parts = []
        if use_case:
            parts.append(f"Inferred use case: {use_case}")
        if inf_types:
            parts.append(f"Suggested body types: {', '.join(inf_types)}")
        if inf_seats:
            parts.append(f"Suggested min seats: {inf_seats}")
        if parts:
            inference_context = "Need analysis for this message:\n" + "\n".join(parts)

    # ── Pass 2: Extract explicit preferences ─────────────────────────
    current_prefs_json = json.dumps(current_prefs, ensure_ascii=False, default=str)
    system_prompt = EXTRACT_SYSTEM_PROMPT.format(
        current_preferences_json=current_prefs_json,
        brand_origins_prompt=format_brand_origins_prompt(),
        inference_context=inference_context,
        message=last_message,
    )

    if llm_router:
        response = await llm_router.ainvoke_task("preference_extractor", [
            SystemMessage(content=system_prompt),
            HumanMessage(content=last_message),
        ])
    else:
        response = await llm_fast.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=last_message),
        ])

    try:
        extracted = json.loads(response.content.strip().removeprefix("```json").removesuffix("```").strip())
    except (json.JSONDecodeError, AttributeError):
        extracted = {}

    # ── Merge all fields ────────────────────────────────────────────
    merged = dict(current_prefs)
    merged = _merge_preferences(merged, extracted)

    # Apply inference result exclusions to initial state as well
    if inference_result:
        rejections = inference_result.get("explicit_rejections", {})
        merged = _merge_preferences(merged, {
            "excluded_body_types": rejections.get("body_types", []),
            "excluded_brands": rejections.get("brands", []),
            "excluded_models": rejections.get("models", []),
        })

    # Merge inference result body types into inferred_body_types
    if inference_result and inference_result.get("inferred_body_types"):
        merged = _merge_preferences(merged, {
            "inferred_body_types": inference_result["inferred_body_types"],
        })
    if inference_result and inference_result.get("inferred_min_seats") is not None:
        merged["inferred_min_seats"] = inference_result["inferred_min_seats"]
    if inference_result and inference_result.get("inferred_use_case"):
        merged["inferred_use_case"] = inference_result["inferred_use_case"]

    # ── Exclusions always win: strip any excluded values from all positive lists ──
    for excluded_key, positive_key in [
        ("excluded_body_types", "preferred_body_types"),
        ("excluded_body_types", "inferred_body_types"),
        ("excluded_brands", "preferred_brands"),
    ]:
        excluded = merged.get(excluded_key, [])
        if excluded and positive_key in merged and isinstance(merged.get(positive_key), list):
            merged[positive_key] = [x for x in merged[positive_key] if x not in excluded]

    updates = {
        "preferences": merged,
        "turn_count": state.get("turn_count", 0) + 1,
    }

    if pool:
        import asyncio
        from app.db.queries import upsert_user_preferences
        prefs_for_db = dict(merged)
        prefs_for_db["intent_history"] = state.get("intent_history", [])
        prefs_for_db["turn_count"] = state.get("turn_count", 0) + 1
        asyncio.ensure_future(
            upsert_user_preferences(
                pool,
                state["session_token"],
                state.get("user_id"),
                prefs_for_db,
            )
        )

    return updates
