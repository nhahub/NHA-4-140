from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.graph.state import CarsChatState


ROUTER_SYSTEM = """You are the routing brain of a car marketplace AI assistant.
Based on the conversation history and the latest user message, decide which
specialist agent should handle this request.

Available agents and when to use each:
- catalogue_node: user wants to find, browse, filter, or GET RECOMMENDATIONS for
  cars. Any mention of specs, budget, city, brand, condition, "show me cars",
  "recommend", "suggest", "what should I buy", "best car", "help me choose",
  "offer me" (meaning "show me offers/deals"), or "offers" in a buying context.
- advisor_node: user is asking about a SPECIFIC car already in the conversation
  or on the current page. Questions like "is this a good deal?", "what are the
  problems with this car?", "should I buy it?" when a car is in context.
- seller_node: user wants to sell a car, price their car, get listing advice,
  or understand how to write a better ad. KEY DISTINCTION: "offer me" is BUYING
  intent (give me offers = show me cars). Only route here if they explicitly say
  "I want to sell" or "I'm offering my car".
- guide_node: user needs help using the website. How to post an ad, how to
  filter, how to compare, how favorites work, how to contact a seller.
- general_node: general car knowledge, reliability questions, maintenance advice,
  insurance, market trends, news, greetings, unclear intent, or anything that
  doesn't fit the above.

Conversation so far:
{message_history}

Current context:
- User has a car page open: {has_context}
- User is identified as a seller: {is_seller}
- User's accumulated preferences: {preferences_summary}

Latest user message: "{latest_message}"

Respond with ONLY one of these exact strings:
catalogue_node | advisor_node | seller_node | guide_node | general_node
"""


async def router_node(state: CarsChatState, config: RunnableConfig) -> dict:
    llm_router = config["configurable"].get("llm_router")

    last_message = state["messages"][-1].content if state.get("messages") else ""
    prefs = state.get("preferences", {})

    # Build message history
    history_msgs = []
    for m in state.get("messages", []):
        role = "user" if m.type == "human" else "assistant"
        history_msgs.append(f"{role}: {m.content}")
    message_history = "\n".join(history_msgs) if history_msgs else "No prior conversation."

    pref_summary = ", ".join(
        f"{k}={v}" for k, v in prefs.items() if v and (not isinstance(v, list) or v)
    ) or "none yet"

    if llm_router:
        response = await llm_router.ainvoke_task("router", [
            SystemMessage(content=ROUTER_SYSTEM.format(
                message_history=message_history,
                has_context="yes" if state.get("context_ad_id") else "no",
                is_seller="yes" if prefs.get("is_seller") else "no",
                preferences_summary=pref_summary,
                latest_message=last_message,
            )),
            HumanMessage(content=last_message),
        ])
    else:
        response = await config["configurable"]["llm_fast"].ainvoke([
            SystemMessage(content=ROUTER_SYSTEM.format(
                message_history=message_history,
                has_context="yes" if state.get("context_ad_id") else "no",
                is_seller="yes" if prefs.get("is_seller") else "no",
                preferences_summary=pref_summary,
                latest_message=last_message,
            )),
            HumanMessage(content=last_message),
        ])

    node_name = response.content.strip().lower() if response.content else "general_node"

    valid_nodes = {"catalogue_node", "advisor_node", "seller_node", "guide_node", "general_node"}
    if node_name not in valid_nodes:
        node_name = "general_node"

    intent_history = state.get("intent_history", []) + [node_name]

    result = {
        "next_node": node_name,
        "intent": node_name,
        "intent_history": intent_history,
        "node_response": "",
    }

    if node_name == "catalogue_node":
        result["retrieved_ads"] = []
        result["similar_ads"] = []
        result["price_analysis"] = None
        result["catalogue_check"] = None
        result["recommendations"] = []

    return result
