from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages


class UserPreferences(TypedDict):
    budget_min: float | None
    budget_max: float | None
    preferred_brands: list[str]
    preferred_body_types: list[str]
    preferred_fuel_types: list[str]
    preferred_transmission: str | None
    preferred_cities: list[str]
    max_km_driven: int | None
    year_min: int | None
    year_max: int | None
    use_case: str | None
    is_seller: bool
    seller_car_brand: str | None
    seller_car_model: str | None
    seller_car_year: int | None
    seller_asking_price: float | None
    seller_intent: str | None
    # --- Inferred needs (derived from use-case language, not explicitly stated) ---
    inferred_body_types: list[str]
    inferred_min_seats: int | None
    inferred_use_case: str | None
    # --- Excluded/negative preferences ---
    excluded_body_types: list[str]
    excluded_brands: list[str]
    excluded_models: list[str]


class CarsChatState(TypedDict):
    messages: Annotated[list, add_messages]

    next_node: str
    intent: str

    session_token: str
    user_id: str | None
    context_ad_id: str | None

    preferences: UserPreferences

    retrieved_ads: list[dict]
    similar_ads: list[dict]
    price_analysis: dict | None
    node_response: str

    catalogue_check: dict | None
    recommendations: list[dict]

    turn_count: int
    intent_history: list[str]
