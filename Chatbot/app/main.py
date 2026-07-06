from dotenv import load_dotenv
load_dotenv()

import logging
import time
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from qdrant_client import QdrantClient

from app.config import settings
from app.core.llm import MultiLLM
from app.core.embedder import Embedder
from app.core.qdrant import QdrantSearch
from app.core.web_search import WebSearch
from app.core.mcp_client import MCPToolRegistry
from app.core.mcp.servers import car_search_server, analysis_server
from app.graph.builder import build_graph
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers import chat as chat_router
from app.voice import router as voice_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Chatbot service starting...")

    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)
    app.state.pool = pool
    app.state.session_start = time.time()

    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID,
                    session_token VARCHAR(128) NOT NULL UNIQUE,
                    context_ad_id UUID,
                    last_active TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            await conn.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint c
                        JOIN pg_class t ON c.conrelid = t.oid
                        WHERE t.relname = 'chat_sessions' AND c.contype = 'u'
                    ) THEN
                        ALTER TABLE chat_sessions ADD UNIQUE (session_token);
                    END IF;
                END;
                $$;
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_token VARCHAR(128) NOT NULL REFERENCES chat_sessions(session_token),
                    role VARCHAR(16) NOT NULL,
                    content TEXT NOT NULL,
                    node_used VARCHAR(64),
                    referenced_ad_ids TEXT[],
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created
                ON chat_messages (session_token, created_at)
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_token VARCHAR(128) NOT NULL UNIQUE REFERENCES chat_sessions(session_token),
                    user_id UUID,
                    budget_min NUMERIC,
                    budget_max NUMERIC,
                    preferred_brands TEXT[],
                    preferred_body_types TEXT[],
                    preferred_fuel_types TEXT[],
                    preferred_transmission VARCHAR(32),
                    preferred_cities TEXT[],
                    max_km_driven NUMERIC,
                    year_min INTEGER,
                    year_max INTEGER,
                    use_case VARCHAR(64),
                    is_seller BOOLEAN DEFAULT FALSE,
                    seller_car_brand VARCHAR(64),
                    seller_car_model VARCHAR(64),
                    seller_car_year INTEGER,
                    seller_asking_price NUMERIC,
                    seller_intent VARCHAR(64),
                    intent_history TEXT[],
                    turn_count INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            logger.info("Ensured chat persistence tables exist")
    except Exception as e:
        logger.warning("Failed to ensure database schema: %s", e)

    try:
        embedder = Embedder("all-MiniLM-L6-v2")
        logger.info("all-MiniLM-L6-v2 embedding model loaded")
    except Exception as e:
        embedder = None
        logger.warning("Failed to load embedding model: %s", e)
    app.state.embedder = embedder

    qdrant_client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )
    qdrant_search = QdrantSearch(qdrant_client)
    app.state.qdrant_search = qdrant_search

    llm = MultiLLM()
    app.state.llm_router = llm
    app.state.llm_fast = llm.fast
    app.state.llm_stream = llm.powerful or llm.fast

    app.state.web_search = WebSearch()

    # Initialize in-process MCP servers
    mcp_registry = MCPToolRegistry()

    # Initialize car-search server
    car_search_server.init_server(qdrant_search, embedder, pool)
    car_tools = await car_search_server.list_tools()
    car_tools_meta = [
        {"name": t.name if hasattr(t, "name") else t["name"],
         "inputSchema": t.inputSchema if hasattr(t, "inputSchema") else t["inputSchema"]}
        for t in car_tools
    ]
    mcp_registry.register_in_process("car-search", car_search_server.call_tool, car_tools_meta)

    # Initialize analysis server
    analysis_server.init_server(qdrant_search, embedder, app.state.web_search)
    analysis_tools = await analysis_server.list_tools()
    analysis_tools_meta = [
        {"name": t.name if hasattr(t, "name") else t["name"],
         "inputSchema": t.inputSchema if hasattr(t, "inputSchema") else t["inputSchema"]}
        for t in analysis_tools
    ]
    mcp_registry.register_in_process("analysis", analysis_server.call_tool, analysis_tools_meta)

    app.state.mcp_registry = mcp_registry
    logger.info("MCP registry initialized with %d tools", len(mcp_registry.get_available_tools()))

    app.state.graph = build_graph()
    app.state.sse_queues = {}

    logger.info("Graph compiled with MemorySaver checkpointer")

    yield

    logger.info("Chatbot service shutting down...")
    if pool:
        await pool.close()


app = FastAPI(
    title="Cars Marketplace Chatbot",
    version="2.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)

app.include_router(chat_router.router)
app.include_router(voice_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
