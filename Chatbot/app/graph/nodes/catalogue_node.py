import json
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.enums import TaskType
from app.graph.state import CarsChatState
from app.data.brand_origins import format_brand_origins_prompt

EXTRACT_CATALOGUE_SYSTEM = """You are a catalogue checker for a car marketplace.
Analyze the user's message and accumulated preferences to determine if they
are asking about a specific car (make, model, year) or doing a general search.

If the user names a SPECIFIC brand and/or model and/or year (e.g., "BMW 318",
"Toyota Corolla 2020", "show me BMWs", "Mercedes E-Class 2018"), extract those
as exact metadata filters.

If the user asks BROADLY ("find me cars", "show me some cars",
"cheap automatic"), set exact_request to null — this is a general
semantic search, not a catalogue lookup.

CRITICAL: Expand brand origin requests into the actual brand names:
{brand_origins_prompt}

Return ONLY valid JSON. No explanation, no markdown:
{{
  "exact_request": {{
    "brands": [],
    "model": null,
    "year": null,
    "body_type": null
  }} | null,
  "is_specific": true | false,
  "request_label": "short description of what user asked for"
}}

User message: "{message}" """


def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").strip()
        if text.endswith("```"):
            text = text.removesuffix("```").strip()
    return text


async def catalogue_node(state: CarsChatState, config: RunnableConfig) -> dict:
    llm_router = config["configurable"].get("llm_router")
    llm_fast = config["configurable"].get("llm_fast")
    pool = config["configurable"].get("db_pool")
    mcp_registry = config["configurable"].get("mcp_registry")

    last_message = state["messages"][-1].content if state.get("messages") else ""

    # Step 1: LLM extracts exact request
    messages = [
        SystemMessage(content=EXTRACT_CATALOGUE_SYSTEM.format(
            message=last_message,
            brand_origins_prompt=format_brand_origins_prompt(),
        )),
        HumanMessage(content=last_message),
    ]
    if llm_router:
        response = await llm_router.ainvoke_task(TaskType.CATALOGUE_CHECK, messages)
    else:
        response = await llm_fast.ainvoke(messages)

    try:
        parsed = json.loads(_clean_json(response.content))
    except (json.JSONDecodeError, AttributeError):
        parsed = {"exact_request": None, "is_specific": False, "request_label": ""}

    exact = parsed.get("exact_request")
    is_specific = parsed.get("is_specific", False)
    request_label = parsed.get("request_label", last_message)

    # Step 2: If specific request, query via MCP or direct DB
    if is_specific and exact and (pool or mcp_registry):
        brands = exact.get("brands", [])
        model = exact.get("model")
        year = exact.get("year")
        body_type = exact.get("body_type")

        available_brands = []
        for brand in brands:
            result = None
            if mcp_registry:
                try:
                    result = await mcp_registry.call_tool("check_catalogue", {
                        "brand": brand, "model": model, "year": year, "body_type": body_type,
                    })
                except Exception as e:
                    logger.warning("MCP check_catalogue failed for %s, falling back: %s", brand, e)
            if not result and pool:
                from app.db.queries import check_catalogue_availability
                result = await check_catalogue_availability(
                    pool, brand=brand, model=model, year=year, body_type=body_type,
                )
            if result and result.get("count", 0) > 0:
                available_brands.append({
                    "brand": brand,
                    "count": result["count"],
                    "ads": result.get("ads", []),
                })

        if available_brands:
            # Found exact matches
            return {
                "catalogue_check": {
                    "available": True,
                    "requested": request_label,
                    "available_brands": available_brands,
                },
                "next_node": "search_node",
            }
        else:
            # Not found — route to recommendation
            return {
                "catalogue_check": {
                    "available": False,
                    "requested": request_label,
                    "brands_searched": brands,
                    "model": model,
                    "year": year,
                    "body_type": body_type,
                },
                "next_node": "recommendation_node",
            }

    # General search — route directly to search_node
    return {
        "catalogue_check": {
            "available": True,
            "requested": request_label,
            "available_brands": [],
        },
        "next_node": "search_node",
    }
