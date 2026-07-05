"""MCP server: analysis — wraps price analysis, brand expansion, website guide, web search."""

import json
import logging

logger = logging.getLogger(__name__)

_MCP_AVAILABLE = False
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    _MCP_AVAILABLE = True
except ImportError:
    Server = object
    Tool = object
    TextContent = object

_qdrant_search = None
_embedder = None
_web_search = None

_TOOLS_METADATA = [
    {
        "name": "analyze_market_price",
        "description": "Compute median, min, max, and recommended price range from similar active listings",
        "inputSchema": {
            "type": "object",
            "properties": {
                "brand": {"type": "string", "description": "Car brand"},
                "model": {"type": "string", "description": "Car model"},
                "year": {"type": "integer"},
                "km_driven": {"type": "number", "description": "Kilometers driven"},
                "condition": {"type": "string", "description": "Condition: excellent|good|fair|poor"},
            },
            "required": ["brand", "model"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web for current information (used for market trends, reliability, news)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "language": {"type": "string", "description": "Language hint", "default": "en"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_website_guide",
        "description": "Get website features reference for how-to questions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Optional topic to filter by"},
            },
        },
    },
    {
        "name": "expand_brand_origins",
        "description": "Expand country/car origin to brand names (e.g. 'German car' → BMW, Mercedes, VW)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Country or region name"},
            },
            "required": ["origin"],
        },
    },
    {
        "name": "expand_colloquial_terms",
        "description": "Expand colloquial car terms into standard search vocabulary",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "User's search query with potential slang"},
            },
            "required": ["query"],
        },
    },
]

if _MCP_AVAILABLE:
    app = Server("analysis")

    _TOOL_OBJECTS = [Tool(**t) for t in _TOOLS_METADATA]

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        return _TOOL_OBJECTS

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        handler = _TOOL_HANDLERS.get(name)
        if handler is None:
            raise ValueError(f"Unknown tool: {name}")
        try:
            result = await handler(arguments)
            if isinstance(result, str):
                return [TextContent(type="text", text=result)]
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
        except Exception as e:
            logger.error("MCP tool '%s' error: %s", name, e, exc_info=True)
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
else:
    app = None

    async def list_tools() -> list[dict]:
        return list(_TOOLS_METADATA)

    async def call_tool(name: str, arguments: dict) -> list[dict]:
        handler = _TOOL_HANDLERS.get(name)
        if handler is None:
            raise ValueError(f"Unknown tool: {name}")
        try:
            result = await handler(arguments)
            if isinstance(result, str):
                return [{"type": "text", "text": result}]
            return [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}]
        except Exception as e:
            logger.error("MCP tool '%s' error: %s", name, e, exc_info=True)
            return [{"type": "text", "text": json.dumps({"error": str(e)})}]


async def _analyze_market_price(args: dict) -> dict:
    if _qdrant_search is None or _embedder is None:
        raise RuntimeError("analysis MCP server not initialized")

    brand = args.get("brand", "")
    model = args.get("model", "")
    year = args.get("year")
    km_driven = args.get("km_driven")
    condition = args.get("condition", "")

    search_text = f"{brand} {model} {year or ''} {condition}".strip().lower()
    vector = _embedder.encode(search_text)

    results = _qdrant_search.hybrid_search(
        query_text=search_text,
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

    if not prices:
        return {"error": "No comparable listings found", "sample_count": 0}

    prices.sort()
    median = prices[len(prices) // 2]
    recommended_min = int(median * 0.9)
    recommended_max = int(median * 1.1)

    if km_driven:
        avg_km = sum(r.get("km_driven", 0) or 0 for r in results) / max(len(results), 1)
        if float(km_driven) > avg_km:
            recommended_min = int(median * 0.85)
            recommended_max = int(median * 1.05)

    return {
        "min": min(prices),
        "max": max(prices),
        "median": median,
        "mean": sum(prices) / len(prices),
        "recommended_min": recommended_min,
        "recommended_max": recommended_max,
        "sample_count": len(prices),
    }


async def _web_search(args: dict) -> str:
    if _web_search is None:
        raise RuntimeError("analysis MCP server not initialized with web search")
    results = _web_search.search(args["query"])
    return results or ""


async def _get_website_guide(args: dict) -> str:
    from app.data.website_guide import format_website_guide
    return format_website_guide()


async def _expand_brand_origins(args: dict) -> str:
    from app.data.brand_origins import format_brand_origins_prompt
    return format_brand_origins_prompt()


async def _expand_colloquial_terms(args: dict) -> str:
    from app.data.car_features import format_expansions_prompt
    return format_expansions_prompt()


_TOOL_HANDLERS = {
    "analyze_market_price": _analyze_market_price,
    "web_search": _web_search,
    "get_website_guide": _get_website_guide,
    "expand_brand_origins": _expand_brand_origins,
    "expand_colloquial_terms": _expand_colloquial_terms,
}


def init_server(qdrant_search, embedder, web_search):
    """Inject runtime dependencies before starting the server."""
    global _qdrant_search, _embedder, _web_search
    _qdrant_search = qdrant_search
    _embedder = embedder
    _web_search = web_search
