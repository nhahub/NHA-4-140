import json
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.graph.state import CarsChatState

GENERAL_SYSTEM = """You are a knowledgeable car expert assistant for an Egyptian car marketplace.
You help users with:
- General car knowledge: reliability, common problems, maintenance intervals,
  fuel economy comparisons, which models hold value in Egypt
- Buying advice: what to check when viewing a used car, how to verify history,
  negotiation tactics, insurance tips
- Market context: which brands are popular in Egypt, spare parts availability,
  service center coverage
- Greetings and small talk: be warm and friendly, briefly introduce what you
  can help with (find cars, seller pricing, car advice, website help)
- Unclear requests: ask ONE clarifying question to understand if they are a
  buyer or seller and what they need

Rules:
- Keep answers to 3-5 sentences unless the user explicitly asks for detail
- Never make up statistics, prices, or reliability data you are not confident about
- If you don't know something, say so honestly
- Always respond in the same language as the user (Arabic or English)
- After answering, if relevant, offer to help them search for cars or price their car

Conversation history:
{message_history}

User message: "{message}"
{web_context}
"""

REFINE_SYSTEM = """Did the user reveal any car preferences or seller signals in this message?
Return ONLY JSON with the preference schema. Use null for unchanged fields.
User message: "{message}"
Existing preferences: {preferences_json}
"""

SEARCH_DECIDE_SYSTEM = """Does this car-related question need a web search to answer accurately?
Topics that need web search: reliability ratings, common problems, maintenance
costs, fuel economy, market trends, news, car comparisons, specific model reviews,
spare parts availability, insurance costs, recent prices, or anything time-sensitive.

Topics that DON'T need web search: greetings, thanks, website help requests,
questions about the user's preferences, or questions already answered by
conversation history.

Return ONLY a JSON object:
{{
  "needs_search": true/false,
  "search_query": "optimized search query for web"  
}}

If needs_search is false, set search_query to null.
User message: "{message}"""


async def general_node(state: CarsChatState, config: RunnableConfig) -> dict:
    llm_fast = config["configurable"]["llm_fast"]
    llm_stream = config["configurable"]["llm_stream"]
    pool = config["configurable"].get("db_pool")
    web_search = config["configurable"].get("web_search")

    last_message = state["messages"][-1].content if state.get("messages") else ""

    # Web search decision
    web_context = ""
    if web_search:
        try:
            decide_resp = await llm_fast.ainvoke([
                SystemMessage(content=SEARCH_DECIDE_SYSTEM.format(message=last_message)),
                HumanMessage(content=last_message),
            ])
            decision = json.loads(
                decide_resp.content.strip().removeprefix("```json").removesuffix("```").strip()
            )
            if decision.get("needs_search") and decision.get("search_query"):
                results = web_search.search(decision["search_query"])
                if results:
                    web_context = f"\n\nWeb search results for reference:\n{results}"
        except Exception:
            pass

    # Build message history summary
    history_msgs = []
    for m in state.get("messages", []):
        history_msgs.append(f"{m.type}: {m.content}")
    message_history = "\n".join(history_msgs[-6:]) if history_msgs else ""

    # Main response (streaming)
    streamed_text = ""
    async for chunk in llm_stream.astream([
        SystemMessage(content=GENERAL_SYSTEM.format(
            message_history=message_history,
            message=last_message,
            web_context=web_context,
        )),
        HumanMessage(content=last_message),
    ]):
        content = chunk.content if hasattr(chunk, "content") else str(chunk)
        streamed_text += content

    # Refinement step
    pref_update = {}
    try:
        pref_response = await llm_fast.ainvoke([
            SystemMessage(content=REFINE_SYSTEM.format(
                message=last_message,
                preferences_json=json.dumps(state.get("preferences", {}), ensure_ascii=False, default=str),
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
        pass

    return {
        "node_response": streamed_text,
        **pref_update,
    }
