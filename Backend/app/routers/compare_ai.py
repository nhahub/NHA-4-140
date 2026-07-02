import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
import asyncpg

from app.dependencies import get_db
from app.services.comparison import ComparisonService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compare-ai", tags=["compare-ai"])


class CompareAiRequest(BaseModel):
    ad_id_1: str
    ad_id_2: str

    @field_validator("ad_id_1", "ad_id_2")
    @classmethod
    def validate_uuids(cls, v: str) -> str:
        UUID(v)
        return v


@router.post("")
async def compare_ai(
    body: CompareAiRequest,
    request: Request,
    pool: asyncpg.Pool = Depends(get_db),
):
    llm = request.app.state.llm
    service = ComparisonService(pool=pool, llm=llm)

    async def event_stream():
        async for event in service.run(body.ad_id_1, body.ad_id_2):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
