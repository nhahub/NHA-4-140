import logging
from uuid import UUID
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.enums import TaskType
from app.graph.state import CarsChatState
from app.core.hallucination_guard import build_grounding_block, validate_response

logger = logging.getLogger(__name__)


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

async def advisor_node(state: CarsChatState, config: RunnableConfig) -> dict:
    llm_router = config["configurable"].get("llm_router")
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
        except Exception as e:
            logger.warning("Failed to fetch context ad %s: %s: %s", context_ad_id, type(e).__name__, str(e)[:200])

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
            pick_msgs = [
                SystemMessage(content=(
                    "The user had these search results and is now asking a follow-up.\n"
                    f"Cars:\n{cars_list}\n\n"
                    f"User: \"{last_message}\"\n\n"
                    "Return ONLY the 1-based index number of the most relevant car, "
                    "or 0 if none matches."
                )),
                HumanMessage(content=last_message),
            ]
            if llm_router:
                pick_resp = await llm_router.ainvoke_task(TaskType.ADVISOR, pick_msgs)
            else:
                pick_resp = await llm_fast.ainvoke(pick_msgs)
            try:
                idx = int(pick_resp.content.strip()) - 1
                if 0 <= idx < len(retrieved):
                    ad_payload = retrieved[idx]
            except (ValueError, IndexError):
                ad_payload = retrieved[0]

    if not ad_payload:
        fallback = (
            "I couldn't find that specific car in your current results. "
            "Would you like me to search again with different filters "
            "or try a different car instead?"
        )
        return {"node_response": fallback}

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
        except Exception as e:
            logger.warning("Web search in advisor_node failed: %s: %s", type(e).__name__, str(e)[:200])

    # Build message history summary
    history_msgs = []
    for m in state.get("messages", []):
        history_msgs.append(f"{m.type}: {m.content}")
    message_history = "\n".join(history_msgs[-6:]) if history_msgs else ""

    # Step 3: LLM response (streaming)
    streamed_text = ""
    response_msgs = [
        SystemMessage(content=ADVISOR_SYSTEM.format(
            grounding_block=grounding_block,
            web_context=web_context,
            message_history=message_history,
        )),
        HumanMessage(content=last_message),
    ]
    if llm_router:
        async for chunk in llm_router.astream_task(TaskType.ADVISOR, response_msgs):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            streamed_text += content
    else:
        async for chunk in llm_stream.astream(response_msgs):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            streamed_text += content

    # Step 4: Validate response
    streamed_text = validate_response(streamed_text, ad_payload)

    # Step 5: Fetch similar cars (MCP or direct)
    similar_ads = []
    try:
        car_text = (
            f"{ad_payload.get('brand', '')} {ad_payload.get('model', '')} "
            f"{ad_payload.get('year', '')} {ad_payload.get('body_type', '')}"
        ).lower()
        mcp_registry = config["configurable"].get("mcp_registry")
        similar = []
        if mcp_registry:
            try:
                mcp_result = await mcp_registry.call_tool("find_similar_cars", {
                    "brand": ad_payload.get("brand", ""),
                    "model": ad_payload.get("model", ""),
                    "year": ad_payload.get("year"),
                    "body_type": ad_payload.get("body_type"),
                    "exclude_ad_id": str(ad_payload.get("ad_id", "")),
                    "limit": 4,
                })
                if isinstance(mcp_result, list):
                    similar = mcp_result
            except Exception as e:
                logger.warning("MCP find_similar_cars failed, falling back: %s", e)
        if not similar and qdrant_search:
            vector = embedder.encode(car_text)
            similar = qdrant_search.hybrid_search(
                query_text=car_text,
                vector=vector,
                limit=4,
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
    except Exception as e:
        logger.warning("Similar car fetch in advisor_node failed: %s: %s", type(e).__name__, str(e)[:200])

    return {
        "node_response": streamed_text,
        "similar_ads": similar_ads,
    }
