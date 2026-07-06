from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages


class CarsChatState(TypedDict):
    messages: Annotated[list, add_messages]

    next_node: str
    intent: str

    session_token: str
    user_id: str | None
    context_ad_id: str | None

    retrieved_ads: list[dict]
    similar_ads: list[dict]
    price_analysis: dict | None
    node_response: str

    catalogue_check: dict | None
    recommendations: list[dict]

    turn_count: int
    intent_history: list[str]
