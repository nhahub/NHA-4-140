from dotenv import load_dotenv
load_dotenv()

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

from app.config import settings
from app.core.llm import get_llm
from app.core.openrouter import get_openrouter_llm
from app.core.tavily import TavilyWrapper
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers import compare as compare_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Comparison service starting...")

    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)
    app.state.pool = pool

    app.state.llm = get_openrouter_llm()
    app.state.groq_llm = get_llm()
    app.state.tavily = TavilyWrapper(settings.tavily_api_key)
    app.state.report_cache = {}

    logger.info("Comparison service ready")

    yield

    logger.info("Comparison service shutting down...")
    if pool:
        await pool.close()


app = FastAPI(
    title="Cars Marketplace Comparison Analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(compare_router.router)

Instrumentator().instrument(app).expose(app)
