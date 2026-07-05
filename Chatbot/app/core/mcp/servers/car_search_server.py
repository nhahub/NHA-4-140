"""MCP server: car-search — wraps Qdrant hybrid search + PostgreSQL car queries."""

import json
import logging
from uuid import UUID

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

# Will be set at startup with actual clients
_qdrant_search = None
_embedder = None
_db_pool = None

_TOOLS_METADATA = [
    {
        "name": "search_cars",
        "description": "Hybrid search car listings (BM25 + vector) with metadata filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 10},
                "budget_min": {"type": "number", "description": "Minimum price in EGP"},
                "budget_max": {"type": "number", "description": "Maximum price in EGP"},
                "brand": {"type": "string", "description": "Single brand filter"},
                "brands": {"type": "array", "items": {"type": "string"}, "description": "Multiple brand filter"},
                "city": {"type": "string", "description": "City name"},
                "fuel_type": {"type": "string", "description": "Fuel type: gasoline|diesel|electric|hybrid"},
                "transmission": {"type": "string", "description": "Transmission: automatic|manual"},
                "body_type": {"type": "string", "description": "[DEPRECATED — will be removed after Cluster A] Use body_types instead"},
                "body_types": {"type": "array", "items": {"type": "string"}, "description": "Body types to include (MatchAny). Replaces deprecated body_type scalar."},
                "excluded_body_types": {"type": "array", "items": {"type": "string"}, "description": "Body types to exclude (must_not)"},
                "excluded_brands": {"type": "array", "items": {"type": "string"}, "description": "Brands to exclude (must_not)"},
                "excluded_models": {"type": "array", "items": {"type": "string"}, "description": "Models to exclude (must_not)"},
                "year_min": {"type": "integer", "description": "Minimum year"},
                "year_max": {"type": "integer", "description": "Maximum year"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_car_details",
        "description": "Get full ad details for a specific car from PostgreSQL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ad_id": {"type": "string", "description": "UUID of the ad"},
            },
            "required": ["ad_id"],
        },
    },
    {
        "name": "find_similar_cars",
        "description": "Find similar cars by brand/model/year using hybrid search",
        "inputSchema": {
            "type": "object",
            "properties": {
                "brand": {"type": "string"},
                "model": {"type": "string"},
                "year": {"type": "integer"},
                "body_type": {"type": "string"},
                "exclude_ad_id": {"type": "string"},
                "limit": {"type": "integer", "default": 4},
            },
            "required": ["brand", "model"],
        },
    },
    {
        "name": "check_catalogue",
        "description": "Check if specific car model exists in active listings",
        "inputSchema": {
            "type": "object",
            "properties": {
                "brand": {"type": "string"},
                "model": {"type": "string"},
                "year": {"type": "integer"},
                "body_type": {"type": "string"},
            },
        },
    },
    {
        "name": "get_car_images",
        "description": "Get image URLs for car ads",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ad_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of ad UUIDs",
                },
            },
            "required": ["ad_ids"],
        },
    },
]

if _MCP_AVAILABLE:
    app = Server("car-search")

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
            return [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}]
        except Exception as e:
            logger.error("MCP tool '%s' error: %s", name, e, exc_info=True)
            return [{"type": "text", "text": json.dumps({"error": str(e)})}]


async def _search_cars(args: dict) -> list[dict]:
    if _qdrant_search is None or _embedder is None:
        raise RuntimeError("car-search MCP server not initialized with Qdrant/Embedder")

    query = args["query"]
    vector = _embedder.encode(query)
    limit = args.get("limit", 10)
    brand = args.get("brand")
    brands = args.get("brands")
    if not brands and brand:
        brands = [brand]

    # body_types: prefer new array param, fall back to deprecated scalar
    body_types = args.get("body_types")
    if not body_types and args.get("body_type"):
        body_types = [args["body_type"]]

    results = _qdrant_search.hybrid_search(
        query_text=query,
        vector=vector,
        limit=limit,
        price_min=args.get("budget_min"),
        price_max=args.get("budget_max"),
        city=args.get("city"),
        brands=brands,
        fuel_type=args.get("fuel_type"),
        transmission=args.get("transmission"),
        body_types=body_types,
        excluded_body_types=args.get("excluded_body_types"),
        excluded_brands=args.get("excluded_brands"),
        excluded_models=args.get("excluded_models"),
        year_min=args.get("year_min"),
        year_max=args.get("year_max"),
    )

    if _db_pool and results:
        from app.db.queries import get_ad_images_by_ids
        ad_ids = []
        for r in results:
            try:
                ad_ids.append(UUID(r.get("ad_id", r["id"])))
            except (ValueError, KeyError):
                continue
        if ad_ids:
            images_map = await get_ad_images_by_ids(_db_pool, ad_ids)
            for r in results:
                aid = r.get("ad_id", r["id"])
                r["images"] = images_map.get(aid, [])

    return results


async def _get_car_details(args: dict) -> dict | None:
    if _db_pool is None:
        raise RuntimeError("car-search MCP server not initialized with DB pool")
    async with _db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM ads WHERE id = $1 AND is_active = TRUE",
            UUID(args["ad_id"]),
        )
        return dict(row) if row else None


async def _find_similar_cars(args: dict) -> list[dict]:
    if _qdrant_search is None or _embedder is None:
        raise RuntimeError("car-search MCP server not initialized")
    text = f"{args['brand']} {args.get('model', '')} {args.get('year', '')} {args.get('body_type', '')}".lower().strip()
    vector = _embedder.encode(text)
    results = _qdrant_search.hybrid_search(
        query_text=text,
        vector=vector,
        limit=args.get("limit", 4),
        exclude_ad_id=args.get("exclude_ad_id"),
    )
    return results


async def _check_catalogue(args: dict) -> dict:
    if _db_pool is None:
        raise RuntimeError("car-search MCP server not initialized with DB pool")
    from app.db.queries import check_catalogue_availability
    return await check_catalogue_availability(
        _db_pool,
        brand=args.get("brand"),
        model=args.get("model"),
        year=args.get("year"),
        body_type=args.get("body_type"),
    )


async def _get_car_images(args: dict) -> dict:
    if _db_pool is None:
        raise RuntimeError("car-search MCP server not initialized with DB pool")
    from app.db.queries import get_ad_images_by_ids
    ad_ids = []
    for aid in args.get("ad_ids", []):
        try:
            ad_ids.append(UUID(aid))
        except (ValueError, KeyError):
            continue
    return await get_ad_images_by_ids(_db_pool, ad_ids)


_TOOL_HANDLERS = {
    "search_cars": _search_cars,
    "get_car_details": _get_car_details,
    "find_similar_cars": _find_similar_cars,
    "check_catalogue": _check_catalogue,
    "get_car_images": _get_car_images,
}


def init_server(qdrant_search, embedder, db_pool):
    """Inject runtime dependencies before starting the server."""
    global _qdrant_search, _embedder, _db_pool
    _qdrant_search = qdrant_search
    _embedder = embedder
    _db_pool = db_pool
