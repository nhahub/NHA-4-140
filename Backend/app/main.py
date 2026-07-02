from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from qdrant_client.http import models as qmodels

from app.config import settings
from app.core.middleware import setup_cors
from app.core.llm import get_llm
from app.core.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    FileTooLargeException,
    UnsupportedMediaTypeException,
    StorageUploadException,
)
from app.schemas.common import ErrorResponse
from app.db.client import create_pool, create_supabase_client, create_qdrant_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    app.state.db = await create_pool()
    try:
        async with app.state.db.acquire() as conn:
            await conn.execute(
                "ALTER TABLE ads ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(64) UNIQUE"
            )
            logger.info("Ensured idempotency_key column exists on ads table")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID,
                    session_token VARCHAR(128) NOT NULL UNIQUE,
                    context_ad_id UUID,
                    last_active TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            logger.info("Ensured chat_sessions table exists")

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
            logger.info("Ensured unique constraint on chat_sessions.session_token")

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
            logger.info("Ensured chat_messages table exists")
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
            logger.info("Ensured user_preferences table exists")
    except Exception as e:
        logger.warning("Failed to ensure database schema: %s", e)
    app.state.supabase = create_supabase_client()
    try:
        buckets = app.state.supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        if settings.supabase_storage_bucket not in bucket_names:
            app.state.supabase.storage.create_bucket(
                id=settings.supabase_storage_bucket,
                options={"public": True},
            )
            logger.info("Created Supabase storage bucket: %s", settings.supabase_storage_bucket)
        else:
            logger.info("Supabase storage bucket already exists: %s", settings.supabase_storage_bucket)
    except Exception as e:
        logger.warning("Failed to ensure Supabase storage bucket: %s", e)

    # Ensure brand images bucket exists
    try:
        buckets = app.state.supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        if settings.supabase_brand_images_bucket not in bucket_names:
            app.state.supabase.storage.create_bucket(
                id=settings.supabase_brand_images_bucket,
                options={"public": True},
            )
            logger.info("Created Supabase storage bucket: %s", settings.supabase_brand_images_bucket)
        else:
            logger.info("Supabase storage bucket already exists: %s", settings.supabase_brand_images_bucket)
    except Exception as e:
        logger.warning("Failed to ensure brand images bucket: %s", e)

    app.state.qdrant = create_qdrant_client()
    collections = app.state.qdrant.get_collections()
    if settings.qdrant_collection not in [c.name for c in collections.collections]:
        app.state.qdrant.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=qmodels.VectorParams(size=384, distance=qmodels.Distance.COSINE),
        )
        logger.info("Created Qdrant collection: %s", settings.qdrant_collection)

    for field_name, field_type in [
        ("is_active", "bool"),
        ("price", "float"),
        ("year", "integer"),
        ("city", "keyword"),
        ("brand", "keyword"),
        ("model", "keyword"),
        ("fuel_type", "keyword"),
        ("transmission", "keyword"),
        ("body_type", "keyword"),
        ("km_driven", "integer"),
    ]:
        try:
            app.state.qdrant.create_payload_index(
                collection_name=settings.qdrant_collection,
                field_name=field_name,
                field_schema=field_type,
            )
        except Exception:
            pass
    try:
        from fastembed import TextEmbedding
        app.state.embedder = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        logger.info("all-MiniLM-L6-v2 embedding model loaded via fastembed")
    except Exception as e:
        app.state.embedder = None
        logger.warning("Failed to load embedding model: %s", e)

    try:
        app.state.llm = get_llm()
        logger.info("Groq LLM initialized: %s", settings.groq_model)
    except Exception as e:
        app.state.llm = None
        logger.warning("Failed to initialize Groq LLM: %s", e)

    yield
    logger.info("Shutting down...")
    if app.state.db:
        await app.state.db.close()


app = FastAPI(
    title="Cars Marketplace API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)

setup_cors(app)


@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="not_found",
            message=exc.detail,
            status_code=exc.status_code,
        ).model_dump(),
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="unauthorized",
            message=exc.detail,
            status_code=exc.status_code,
        ).model_dump(),
    )


@app.exception_handler(ForbiddenException)
async def forbidden_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="forbidden",
            message=exc.detail,
            status_code=exc.status_code,
        ).model_dump(),
    )


@app.exception_handler(ConflictException)
async def conflict_handler(request: Request, exc: ConflictException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="conflict",
            message=exc.detail,
            status_code=exc.status_code,
        ).model_dump(),
    )


@app.exception_handler(FileTooLargeException)
async def file_too_large_handler(request: Request, exc: FileTooLargeException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="file_too_large",
            message=exc.detail,
            status_code=exc.status_code,
        ).model_dump(),
    )


@app.exception_handler(UnsupportedMediaTypeException)
async def unsupported_media_handler(request: Request, exc: UnsupportedMediaTypeException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="unsupported_media_type",
            message=exc.detail,
            status_code=exc.status_code,
        ).model_dump(),
    )


@app.exception_handler(StorageUploadException)
async def storage_upload_handler(request: Request, exc: StorageUploadException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="storage_upload_error",
            message=exc.detail,
            status_code=exc.status_code,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def internal_handler(request: Request, exc: Exception):
    logger.exception("Internal error")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            message="An unexpected error occurred",
            status_code=500,
        ).model_dump(),
    )


from app.routers import auth, users, ads, favorites, search, chat, compare, compare_ai

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(ads.router, prefix="/api/v1")
app.include_router(favorites.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(compare.router, prefix="/api/v1")
app.include_router(compare_ai.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
