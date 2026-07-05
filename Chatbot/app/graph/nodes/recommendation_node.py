import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.graph.state import CarsChatState
from app.data.constants import RECOMMENDATION_LIMIT

logger = logging.getLogger(__name__)

RECOMMENDATION_SYSTEM = """The user asked for a specific car that is NOT available
in our catalogue. You need to recommend alternative cars that are actually in stock.

They wanted: {requested_description}
What they searched for: brands={brands_searched}, model={model}, year={year}, body_type={body_type}
Their preferences: {preferences_json}

Available alternatives found:
{alternatives_summary}

Write a friendly 2-3 sentence response in the same language the user wrote in:
1. Acknowledge their specific request is not currently available
2. Tell them what alternatives ARE available and why each is a good match
   (same brand different model, same segment different brand, similar price range)
3. End on a positive note

Do NOT list the cars in detail — they will be shown as visual cards below.
Do NOT mention prices or specific numbers from alternatives unless very relevant."""


async def recommendation_node(state: CarsChatState, config: RunnableConfig) -> dict:
    llm_router = config["configurable"].get("llm_router")
    llm_fast = config["configurable"]["llm_fast"]
    llm_stream = config["configurable"]["llm_stream"]
    embedder = config["configurable"]["embedder"]
    qdrant_search = config["configurable"]["qdrant_search"]
    pool = config["configurable"].get("db_pool")

    last_message = state["messages"][-1].content if state.get("messages") else ""
    prefs = state.get("preferences", {})
    catalogue = state.get("catalogue_check", {})

    brands_searched = catalogue.get("brands_searched", [])
    model = catalogue.get("model")
    year = catalogue.get("year")
    body_type = catalogue.get("body_type")
    request_label = catalogue.get("requested", last_message)

    # Build relaxed search query
    query_parts = []
    if brands_searched:
        query_parts.extend(brands_searched)
    if model:
        query_parts.append(model)
    if body_type:
        query_parts.append(body_type)
    if year:
        query_parts.append(str(year))

    search_text = " ".join(query_parts) if query_parts else last_message
    mcp_registry = config["configurable"].get("mcp_registry")

    excluded_body_types = prefs.get("excluded_body_types", None)
    excluded_brands = prefs.get("excluded_brands", None)
    excluded_models = prefs.get("excluded_models", None)
    body_types = [body_type] if body_type else None

    # Search via MCP or direct
    results = []
    if mcp_registry:
        try:
            mcp_results = await mcp_registry.call_tool("search_cars", {
                "query": search_text,
                "limit": RECOMMENDATION_LIMIT + 3,
                "budget_min": prefs.get("budget_min"),
                "budget_max": prefs.get("budget_max"),
                "body_types": body_types,
                "excluded_body_types": excluded_body_types,
                "excluded_brands": excluded_brands,
                "excluded_models": excluded_models,
                "year_min": prefs.get("year_min") or (year - 3 if year else None),
                "year_max": prefs.get("year_max") or (year + 3 if year else None),
            })
            if isinstance(mcp_results, list):
                results = mcp_results
        except Exception as e:
            logger.warning("MCP search_cars in recommendation_node failed, falling back: %s", e)

    if not results and qdrant_search:
        vector = embedder.encode(search_text)
        results = qdrant_search.hybrid_search(
            query_text=search_text,
            vector=vector,
            limit=RECOMMENDATION_LIMIT + 3,
            price_min=prefs.get("budget_min"),
            price_max=prefs.get("budget_max"),
            body_types=body_types,
            excluded_body_types=excluded_body_types,
            excluded_brands=excluded_brands,
            excluded_models=excluded_models,
            year_min=prefs.get("year_min") or (year - 3 if year else None),
            year_max=prefs.get("year_max") or (year + 3 if year else None),
        )

    # Build alternative ads list
    from app.core.hallucination_guard import verify_results
    results = verify_results(results)

    images_map = {}
    if results:
        ad_ids = []
        from uuid import UUID
        for r in results:
            try:
                aid = UUID(r.get("ad_id", r["id"]))
                ad_ids.append(aid)
            except (ValueError, KeyError):
                continue
        if ad_ids:
            if mcp_registry:
                try:
                    images_map = await mcp_registry.call_tool("get_car_images", {"ad_ids": [str(a) for a in ad_ids]})
                    if not isinstance(images_map, dict):
                        images_map = {}
                except Exception:
                    images_map = {}
            if not images_map and pool:
                from app.db.queries import get_ad_images_by_ids
                images_map = await get_ad_images_by_ids(pool, ad_ids)

    ads = []
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

    # Generate response text
    alternatives_summary = ""
    if ads:
        cities = set()
        body_types = set()
        prices = []
        for a in ads:
            if a.get("city"): cities.add(a["city"])
            if a.get("body_type"): body_types.add(a["body_type"])
            if a.get("price"): prices.append(a["price"])
        parts = [f"{len(ads)} alternative car{'s' if len(ads) != 1 else ''} found"]
        if cities:
            parts.append(f"in {', '.join(sorted(cities))}")
        if body_types:
            parts.append(f"({', '.join(sorted(body_types))})")
        if prices:
            parts.append(f"priced {min(prices):,.0f} – {max(prices):,.0f} EGP")
        alternatives_summary = " ".join(parts)
    prefs_json = json.dumps(prefs, ensure_ascii=False, default=str)
    brands_str = ", ".join(brands_searched) if brands_searched else "unknown"
    model_str = model or "any"

    streamed_text = ""
    response_msgs = [
        SystemMessage(content=RECOMMENDATION_SYSTEM.format(
            requested_description=request_label,
            brands_searched=brands_str,
            model=model_str,
            year=year or "any",
            body_type=body_type or "any",
            preferences_json=prefs_json,
            alternatives_summary=alternatives_summary,
        )),
        HumanMessage(content=last_message),
    ]
    if llm_router:
        async for chunk in llm_router.astream_task("recommendation", response_msgs):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            streamed_text += content
    else:
        async for chunk in llm_stream.astream(response_msgs):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            streamed_text += content

    return {
        "retrieved_ads": ads,
        "recommendations": ads,
        "node_response": streamed_text,
    }
