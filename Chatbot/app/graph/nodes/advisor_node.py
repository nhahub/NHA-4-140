import json
from uuid import UUID
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.graph.state import CarsChatState
from app.core.hallucination_guard import build_grounding_block, validate_response


ADVISOR_SYSTEM = """You are a car expert assistant helping a user evaluate a specific car listing.

{grounding_block}
{web_context}

Rules:
- Answer ONLY based on the verified data above
- If asked about something not in the data, say "I don't have that information
  from the listing — you should ask the seller directly"
- Never invent prices, km readings, years, or features
- You CAN give general advice about this car model/brand from your knowledge,
  but clearly label it as general knowledge, not listing-specific
- If "Images available" is "Yes", tell the user the image is shown in the car
  card above. Do NOT say images are unavailable or missing.
- After answering, if relevant, mention that you can show similar alternatives
- Always respond in the same language as the user (Arabic or English)

Conversation history:
{message_history}
"""

PREF_REFINE_SYSTEM = """The user was asking about a {brand} {model} {year} listed at {price} EGP.
Did the user express any preference signals? (liked the price, concerned about km,
wanted automatic, preferred a different city, etc.)
Extract any NEW signals not already in their preferences.
Return ONLY JSON with the same preference schema. Use null for unchanged fields.

Existing preferences: {preferences_json}
User message: "{message}"
"""


async def advisor_node(state: CarsChatState, config: RunnableConfig) -> dict:
    llm_fast = config["configurable"]["llm_fast"]
    llm_stream = config["configurable"]["llm_stream"]
    embedder = config["configurable"]["embedder"]
    qdrant_search = config["configurable"]["qdrant_search"]
    pool = config["configurable"].get("db_pool")

    last_message = state["messages"][-1].content if state.get("messages") else ""

    # Step 1: Determine which car the user is asking about
    ad_payload = None
    context_ad_id = state.get("context_ad_id")
    retrieved = state.get("retrieved_ads", [])

    if context_ad_id and pool:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM ads WHERE id = $1 AND is_active = TRUE",
                    UUID(context_ad_id),
                )
                if row:
                    ad_payload = dict(row)
        except Exception:
            pass

    if not ad_payload and retrieved:
        if len(retrieved) == 1:
            ad_payload = retrieved[0]
        else:
            # Multiple results — use LLM to pick the most relevant one
            cars_list = "\n".join(
                f"{i+1}. {c.get('brand','')} {c.get('model','')} ({c.get('year','')}) - "
                f"{c.get('price','')} EGP - {c.get('city','')}"
                for i, c in enumerate(retrieved)
            )
            pick_resp = await llm_fast.ainvoke([
                SystemMessage(content=(
                    "The user had these search results and is now asking a follow-up.\n"
                    f"Cars:\n{cars_list}\n\n"
                    f"User: \"{last_message}\"\n\n"
                    "Return ONLY the 1-based index number of the most relevant car, "
                    "or 0 if none matches."
                )),
                HumanMessage(content=last_message),
            ])
            try:
                idx = int(pick_resp.content.strip()) - 1
                if 0 <= idx < len(retrieved):
                    ad_payload = retrieved[idx]
            except (ValueError, IndexError):
                # Default to first result
                ad_payload = retrieved[0]

    if not ad_payload:
        return {"next_node": "general_node", "node_response": ""}

    # Step 2: Build grounded context
    grounding_block = build_grounding_block(ad_payload)

    # Web search for supplementary model info
    web_context = ""
    web_search = config["configurable"].get("web_search")
    if web_search:
        try:
            brand = ad_payload.get("brand", "")
            model = ad_payload.get("model", "")
            year = ad_payload.get("year", "")
            search_query = f"{brand} {model} {year} car reliability review common problems"
            results = web_search.search(search_query)
            if results:
                web_context = f"\n\nSupplementary web info for {brand} {model}:\n{results}"
        except Exception:
            pass

    # Build message history summary
    history_msgs = []
    for m in state.get("messages", []):
        history_msgs.append(f"{m.type}: {m.content}")
    message_history = "\n".join(history_msgs[-6:]) if history_msgs else ""

    # Step 3: LLM response (streaming)
    streamed_text = ""
    async for chunk in llm_stream.astream([
        SystemMessage(content=ADVISOR_SYSTEM.format(
            grounding_block=grounding_block,
            web_context=web_context,
            message_history=message_history,
        )),
        HumanMessage(content=last_message),
    ]):
        content = chunk.content if hasattr(chunk, "content") else str(chunk)
        streamed_text += content

    # Step 4: Validate response
    streamed_text = validate_response(streamed_text, ad_payload)

    # Step 5: Extract refined preferences
    try:
        pref_response = await llm_fast.ainvoke([
            SystemMessage(content=PREF_REFINE_SYSTEM.format(
                brand=ad_payload.get("brand", ""),
                model=ad_payload.get("model", ""),
                year=ad_payload.get("year", ""),
                price=ad_payload.get("price", 0),
                preferences_json=json.dumps(state.get("preferences", {}), ensure_ascii=False, default=str),
                message=last_message,
            )),
            HumanMessage(content=last_message),
        ])
        extracted = json.loads(pref_response.content.strip().removeprefix("```json").removesuffix("```").strip())
        merged = dict(state.get("preferences", {}))
        for key, val in extracted.items():
            if val is None:
                continue
            if isinstance(val, list):
                existing = merged.get(key, [])
                if not isinstance(existing, list):
                    existing = []
                for item in val:
                    if item not in existing:
                        existing.append(item)
                merged[key] = existing
            else:
                merged[key] = val

        if pool:
            import asyncio
            from app.db.queries import upsert_user_preferences
            prefs_for_db = dict(merged)
            prefs_for_db["intent_history"] = state.get("intent_history", [])
            prefs_for_db["turn_count"] = state.get("turn_count", 0)
            asyncio.ensure_future(
                upsert_user_preferences(pool, state["session_token"], state.get("user_id"), prefs_for_db)
            )

        pref_update = {"preferences": merged}
    except Exception:
        pref_update = {}

    # Step 6: Fetch similar cars
    similar_ads = []
    try:
        text_to_embed = (
            f"{ad_payload.get('brand', '')} {ad_payload.get('model', '')} "
            f"{ad_payload.get('year', '')} {ad_payload.get('body_type', '')}"
        ).lower()
        vector = embedder.encode(text_to_embed)
        similar = qdrant_search.search(
            vector=vector,
            limit=3,
            exclude_ad_id=str(ad_payload.get("ad_id", "")),
        )
        for s in similar[:2]:
            similar_ads.append({
                "id": s.get("ad_id", s["id"]),
                "brand": s.get("brand", ""),
                "model": s.get("model", ""),
                "year": s.get("year", 0),
                "price": float(s.get("price", 0)),
                "city": s.get("city", ""),
                "cover_image_url": s.get("cover_image_url", ""),
                "condition": s.get("condition", ""),
            })
    except Exception:
        pass

    return {
        "node_response": streamed_text,
        "similar_ads": similar_ads,
        **pref_update,
    }
