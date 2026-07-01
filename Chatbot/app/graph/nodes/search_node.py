import json
from uuid import UUID
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.graph.state import CarsChatState
from app.core.hallucination_guard import verify_results

QUERY_BUILDER_SYSTEM = """You are a search query builder for a car marketplace vector database.
Given the user's message and their accumulated preferences, build the best
possible search query string that will retrieve relevant car listings.

Rules:
1. Extract ONLY clear metadata filters: brand, price_min, price_max, city, 
   fuel_type, transmission, body_type. If uncertain, leave null.
2. NEVER extract "condition" filter from words like "conditioner", 
   "conditioning", "AC", "air conditioning" — these are car FEATURES, not 
   the car's mechanical condition.
3. Put EVERYTHING else (features, needs, preferences) into search_query for 
   semantic matching against listing descriptions.
4. Expand colloquial car terms in search_query:
   - "conditioner" / "AC" -> "air conditioning air conditioner AC"
   - "4x4" -> "4x4 four wheel drive 4wd"
   - "sunroof" -> "sunroof moonroof"
   - "leather" -> "leather seats leather interior"
   - "GPS" / "navigation" -> "GPS navigation nav"
   - "camera" -> "backup camera rear camera"
   - "bluetooth" -> "bluetooth handsfree"
   - "push start" -> "push start keyless"
   - "cruise" -> "cruise control"
   - "sensor" -> "sensors parking sensor"
5. If the user asks about features typically in descriptions (not metadata), 
   use a broader search query and leave filters minimal/null.

Return ONLY valid JSON:
{{
  "search_query": "detailed expanded search query for semantic matching",
  "filters": {{
    "price_min": null,
    "price_max": null,
    "brand": null,
    "city": null,
    "fuel_type": null,
    "transmission": null,
    "body_type": null
  }}
}}

User message: "{message}"
Accumulated preferences: {preferences_json}"""

RESPONSE_SYSTEM = """You are a helpful car marketplace assistant.
You have just searched the listings and found the following cars that match
the user's request. Write a natural, friendly 2-3 sentence response
introducing the results. Mention key matching points (city, price range,
body type, etc.) that make these results relevant.
Do NOT list the cars — they will be shown as visual cards below your message.
Always respond in the same language the user wrote in (Arabic or English).

Found cars summary:
{cars_summary}

User message: "{message}"
"""


def evaluate_search_quality(results: list[dict]) -> bool:
    """Evaluate if search results are good enough using score-based heuristic."""
    if not results:
        return False
    avg_score = sum(r.get("score", 0) for r in results) / len(results)
    top_score = results[0].get("score", 0) if results else 0
    return top_score > 0.65 or avg_score > 0.5


def compute_dcg(results: list[dict]) -> float:
    """Compute DCG-like metric using Qdrant scores as relevance gains."""
    dcg = 0.0
    for i, r in enumerate(results):
        gain = r.get("score", 0.0) * 3
        if i == 0:
            dcg += gain
        else:
            dcg += gain / (i + 1)
    return dcg


def merge_dedup_results(primary: list[dict], secondary: list[dict], max_count: int = 5) -> list[dict]:
    seen = set()
    merged = []
    for r in primary + secondary:
        aid = r.get("ad_id", r.get("id"))
        if aid and aid not in seen:
            seen.add(aid)
            merged.append(r)
    return merged[:max_count]


async def search_node(state: CarsChatState, config: RunnableConfig) -> dict:
    llm_fast = config["configurable"]["llm_fast"]
    llm_stream = config["configurable"]["llm_stream"]
    embedder = config["configurable"]["embedder"]
    qdrant_search = config["configurable"]["qdrant_search"]
    pool = config["configurable"].get("db_pool")

    last_message = state["messages"][-1].content if state.get("messages") else ""
    prefs = state.get("preferences", {})

    # Step 1: Build enhanced search query
    prefs_json = json.dumps(prefs, ensure_ascii=False, default=str)
    query_response = await llm_fast.ainvoke([
        SystemMessage(content=QUERY_BUILDER_SYSTEM.format(
            message=last_message,
            preferences_json=prefs_json,
        )),
        HumanMessage(content=last_message),
    ])

    try:
        parsed = json.loads(query_response.content.strip().removeprefix("```json").removesuffix("```").strip())
        search_query = parsed.get("search_query", last_message)
        filters = parsed.get("filters", {})
    except (json.JSONDecodeError, AttributeError):
        search_query = last_message
        filters = {}

    # Step 2: Initial search
    vector = embedder.encode(search_query)
    results = qdrant_search.search(
        vector=vector,
        limit=5,
        price_min=filters.get("price_min"),
        price_max=filters.get("price_max"),
        city=filters.get("city"),
        brand=filters.get("brand"),
        fuel_type=filters.get("fuel_type"),
        transmission=filters.get("transmission"),
        body_type=filters.get("body_type"),
        year_min=prefs.get("year_min"),
        year_max=prefs.get("year_max"),
    )

    results = verify_results(results)
    search_dcg = compute_dcg(results)

    # Step 2.5: Evaluate quality — retry with broader search if poor
    if not evaluate_search_quality(results):
        broader_query = search_query
        broader_vector = embedder.encode(broader_query)
        broader_results = qdrant_search.search(
            vector=broader_vector,
            limit=10,
        )
        broader_results = verify_results(broader_results)
        broader_dcg = compute_dcg(broader_results)

        if broader_dcg > search_dcg:
            results = merge_dedup_results(broader_results, results, max_count=5)
        else:
            results = merge_dedup_results(results, broader_results, max_count=5)

    # Step 3: Fetch images and build ad list
    ad_ids = []
    for r in results:
        try:
            aid = UUID(r.get("ad_id", r["id"]))
            ad_ids.append(aid)
        except (ValueError, KeyError):
            continue

    ads = []
    if ad_ids and pool:
        from app.db.queries import get_ad_images_by_ids
        images_map = await get_ad_images_by_ids(pool, ad_ids)
        for r in results:
            aid = r.get("ad_id", r["id"])
            try:
                ad = {
                    "id": aid,
                    "brand": r.get("brand", ""),
                    "model": r.get("model", ""),
                    "year": r.get("year", 0),
                    "price": float(r.get("price", 0)),
                    "condition": r.get("condition", ""),
                    "km_driven": r.get("km_driven", 0),
                    "body_type": r.get("body_type", ""),
                    "transmission": r.get("transmission", ""),
                    "fuel_type": r.get("fuel_type", ""),
                    "city": r.get("city", ""),
                    "cover_image_url": r.get("cover_image_url", ""),
                    "images": images_map.get(aid, []),
                    "score": r.get("score", 0),
                }
                ads.append(ad)
            except (ValueError, KeyError):
                continue

    # Step 4: Draft conversational response (streaming)
    count = len(ads)
    cars_summary = f"{count} car{'s' if count != 1 else ''} found"
    if prefs.get("preferred_cities"):
        cars_summary += f" in {', '.join(prefs['preferred_cities'])}"

    streamed_text = ""
    async for chunk in llm_stream.astream([
        SystemMessage(content=RESPONSE_SYSTEM.format(
            message=last_message,
            cars_summary=cars_summary,
        )),
        HumanMessage(content=last_message),
    ]):
        content = chunk.content if hasattr(chunk, "content") else str(chunk)
        streamed_text += content

    # Step 5: Proactive new-match check
    new_match_ads = []
    try:
        if pool and prefs:
            from app.db.queries import get_new_matching_ads
            session_start = config["configurable"].get("session_start")
            if session_start:
                import datetime
                created_at_dt = datetime.datetime.fromtimestamp(session_start)
                new_ads = await get_new_matching_ads(pool, created_at_dt, prefs)
                for a in new_ads:
                    ad = {
                        "id": str(a["id"]),
                        "brand": a["brand"],
                        "model": a["model"],
                        "year": a["year"],
                        "price": float(a["price"]),
                        "city": a["city"],
                        "_is_new_match": True,
                    }
                    new_match_ads.append(ad)
    except Exception:
        pass

    all_ads = ads + new_match_ads

    return {
        "retrieved_ads": all_ads,
        "node_response": streamed_text,
    }
