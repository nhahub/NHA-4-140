import json
import asyncio
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from app.graph.state import CarsChatState


async def responder_node(state: CarsChatState, config: RunnableConfig) -> dict:
    llm_stream = config["configurable"]["llm_stream"]
    pool = config["configurable"].get("db_pool")
    sse_queue = config["configurable"].get("sse_queue")
    session_token = state.get("session_token", "")
    node_response = state.get("node_response", "")
    intent = state.get("intent", "")

    # 1. Emit status event
    status_map = {
        "search_node": "Searching listings...",
        "advisor_node": "Analyzing this car...",
        "seller_node": "Analyzing market data...",
        "guide_node": "Looking that up...",
        "general_node": "",
    }
    status_text = status_map.get(intent, "")
    if status_text:
        _emit(sse_queue, {"type": "status", "content": status_text})

    async def send_tokens():
        words = node_response.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            _emit(sse_queue, {"type": "token", "content": chunk})
            await asyncio.sleep(0.02)

    # 2. Emit node_response text as token events
    token_task = asyncio.ensure_future(send_tokens())

    # 3. Emit retrieved_ads (cars)
    retrieved = state.get("retrieved_ads", [])
    if retrieved:
        regular = [a for a in retrieved if not a.get("_is_new_match")]
        new_matches = [a for a in retrieved if a.get("_is_new_match")]
        if regular:
            _emit(sse_queue, {"type": "cars", "content": regular})
        if new_matches:
            _emit(sse_queue, {"type": "new_match", "content": new_matches})

    # 4. Emit similar_ads
    similar = state.get("similar_ads", [])
    if similar:
        _emit(sse_queue, {"type": "similar_cars", "content": similar})

    # 5. Emit price_analysis
    price_analysis = state.get("price_analysis")
    if price_analysis:
        _emit(sse_queue, {"type": "price_analysis", "content": price_analysis})

    # 6. Wait for token streaming to finish
    await token_task

    # 7. Background persistence tasks
    if pool:
        from app.db.queries import insert_chat_message, upsert_user_preferences

        # Find referenced ad IDs
        ref_ids = []
        for ad in retrieved:
            if ad.get("id"):
                ref_ids.append(str(ad["id"]))

        # Fire-and-forget: insert user message
        if state.get("messages"):
            user_msg = None
            for m in reversed(state["messages"]):
                if hasattr(m, "type") and m.type == "human":
                    user_msg = m.content
                    break
            if user_msg:
                asyncio.ensure_future(
                    insert_chat_message(pool, session_token, "user", user_msg, node_used=intent)
                )

        # Fire-and-forget: insert assistant response
        asyncio.ensure_future(
            insert_chat_message(pool, session_token, "assistant", node_response, node_used=intent, referenced_ad_ids=ref_ids if ref_ids else None)
        )

        # Fire-and-forget: update turn count
        prefs = dict(state.get("preferences", {}))
        prefs["intent_history"] = state.get("intent_history", [])
        prefs["turn_count"] = state.get("turn_count", 0)
        asyncio.ensure_future(
            upsert_user_preferences(pool, session_token, state.get("user_id"), prefs)
        )

    # 8. Emit done event (after all tokens have been sent)
    _emit(sse_queue, {"type": "done", "content": None})

    # 8. Append to messages
    return {
        "messages": [AIMessage(content=node_response)],
    }


def _emit(queue, event: dict):
    if queue:
        queue.put_nowait(event)
