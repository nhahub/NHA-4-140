import json
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.graph.state import CarsChatState


SELLER_EXTRACT_SYSTEM = """The user is a seller. Extract the details of the car they want to sell or
price. Return ONLY valid JSON:
{{
  "brand": null,
  "model": null,
  "year": null,
  "condition": null,
  "km_driven": null,
  "seller_intent": "pricing" | "tips" | "listing" | "general"
}}

Use null for any field not mentioned.
Existing seller info: {seller_fields_json}
User message: "{message}"
"""

PRICING_SYSTEM = """You are a car pricing expert for the Egyptian market.
The seller wants to price their {brand} {model} {year}.

Market data from current active listings (DO NOT contradict these numbers):
- Listings analyzed: {sample_count}
- Lowest asking price: {min_price} EGP
- Highest asking price: {max_price} EGP
- Median price: {median_price} EGP
- Recommended range: {recommended_min} – {recommended_max} EGP

Seller's car:
- Condition: {condition}
- KM driven: {km_driven}
{web_context}

Give a clear pricing recommendation with reasoning. Be specific.
Mention if their km or condition affects the price vs market median.
Always respond in the same language as the user (Arabic or English).
"""

TIPS_SYSTEM = """You are a car selling expert for the Egyptian market.
Give the seller practical, specific advice for listing their {brand} {model} {year}.
Cover: photos (lighting, angles, must-have shots), description writing
(keywords that attract buyers), pricing psychology, and timing.
Be concrete and actionable. Use numbered points.
Always respond in the same language as the user (Arabic or English).
"""


async def seller_node(state: CarsChatState, config: RunnableConfig) -> dict:
    llm_fast = config["configurable"]["llm_fast"]
    llm_stream = config["configurable"]["llm_stream"]
    embedder = config["configurable"]["embedder"]
    qdrant_search = config["configurable"]["qdrant_search"]
    pool = config["configurable"].get("db_pool")

    last_message = state["messages"][-1].content if state.get("messages") else ""
    prefs = state.get("preferences", {})

    # Step 1: Extract seller car details
    seller_fields = {k: prefs.get(k) for k in ("seller_car_brand", "seller_car_model", "seller_car_year",
                                                 "seller_asking_price", "seller_intent") if prefs.get(k)}
    extract_response = await llm_fast.ainvoke([
        SystemMessage(content=SELLER_EXTRACT_SYSTEM.format(
            seller_fields_json=json.dumps(seller_fields, ensure_ascii=False, default=str),
            message=last_message,
        )),
        HumanMessage(content=last_message),
    ])

    try:
        extracted = json.loads(extract_response.content.strip().removeprefix("```json").removesuffix("```").strip())
    except (json.JSONDecodeError, AttributeError):
        extracted = {}

    brand = extracted.get("brand") or prefs.get("seller_car_brand") or ""
    model = extracted.get("model") or prefs.get("seller_car_model") or ""
    year = extracted.get("year") or prefs.get("seller_car_year")
    condition = extracted.get("condition") or ""
    km_driven = extracted.get("km_driven")
    seller_intent = extracted.get("seller_intent") or prefs.get("seller_intent") or "pricing"

    # Step 2: Market price analysis (for pricing intent)
    price_analysis = None
    if seller_intent == "pricing":
        search_text = f"{brand} {model} {year or ''} {condition}".strip().lower()
        vector = embedder.encode(search_text) if search_text else embedder.encode(last_message.lower())

        results = qdrant_search.search(
            vector=vector,
            limit=10,
            brand=brand if brand else None,
            year_min=(int(year) - 2) if year else None,
            year_max=(int(year) + 2) if year else None,
        )

        prices = []
        for r in results:
            p = r.get("price")
            if p:
                try:
                    prices.append(float(p))
                except (ValueError, TypeError):
                    continue

        if prices:
            prices.sort()
            median = prices[len(prices) // 2]
            recommended_min = int(median * 0.9)
            recommended_max = int(median * 1.1)
            if km_driven:
                avg_km = sum(r.get("km_driven", 0) or 0 for r in results) / max(len(results), 1)
                if float(km_driven) > avg_km:
                    recommended_min = int(median * 0.85)
                    recommended_max = int(median * 1.05)

            price_analysis = {
                "min": min(prices),
                "max": max(prices),
                "median": median,
                "mean": sum(prices) / len(prices),
                "recommended_min": recommended_min,
                "recommended_max": recommended_max,
                "sample_count": len(prices),
            }

    # Step 3: Web search for market context
    web_context = ""
    web_search = config["configurable"].get("web_search")
    if web_search and brand:
        try:
            search_query = f"{brand} {model} {year} used car price Egypt market 2026"
            results = web_search.search(search_query)
            if results:
                web_context = f"\n\nWeb market context:\n{results}"
        except Exception:
            pass

    # Step 4: LLM response (streaming)
    if seller_intent == "pricing" and price_analysis:
        system_prompt = PRICING_SYSTEM.format(
            brand=brand or "unknown",
            model=model or "unknown",
            year=year or "unknown",
            sample_count=price_analysis["sample_count"],
            min_price=f"{price_analysis['min']:,.0f}",
            max_price=f"{price_analysis['max']:,.0f}",
            median_price=f"{price_analysis['median']:,.0f}",
            recommended_min=f"{price_analysis['recommended_min']:,.0f}",
            recommended_max=f"{price_analysis['recommended_max']:,.0f}",
            condition=condition or "not specified",
            km_driven=km_driven or "not specified",
            web_context=web_context,
        )
    else:
        system_prompt = TIPS_SYSTEM.format(
            brand=brand or "your",
            model=model or "car",
            year=year or "",
        )

    streamed_text = ""
    async for chunk in llm_stream.astream([
        SystemMessage(content=system_prompt),
        HumanMessage(content=last_message),
    ]):
        content = chunk.content if hasattr(chunk, "content") else str(chunk)
        streamed_text += content

    # Step 4: Refine seller preferences
    merged = dict(prefs)
    seller_updates = {
        "seller_car_brand": brand or prefs.get("seller_car_brand"),
        "seller_car_model": model or prefs.get("seller_car_model"),
        "seller_car_year": year or prefs.get("seller_car_year"),
        "seller_asking_price": extracted.get("seller_asking_price") or prefs.get("seller_asking_price"),
        "seller_intent": seller_intent,
        "is_seller": True,
    }
    for k, v in seller_updates.items():
        if v is not None:
            merged[k] = v

    if pool:
        import asyncio
        from app.db.queries import upsert_user_preferences
        prefs_for_db = dict(merged)
        prefs_for_db["intent_history"] = state.get("intent_history", [])
        prefs_for_db["turn_count"] = state.get("turn_count", 0)
        asyncio.ensure_future(
            upsert_user_preferences(pool, state["session_token"], state.get("user_id"), prefs_for_db)
        )

    return {
        "node_response": streamed_text,
        "price_analysis": price_analysis,
        "preferences": merged,
    }
