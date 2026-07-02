from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import asyncpg
import httpx
import json

from app.dependencies import get_db
from app.db.queries import ads as ads_queries
from app.core.exceptions import NotFoundException
from app.config import settings

router = APIRouter(prefix="/compare", tags=["compare"])


class CompareRequest(BaseModel):
    ad_ids: List[str]


@router.post("")
async def compare_ads(
    body: CompareRequest,
    pool: asyncpg.Pool = Depends(get_db),
):
    if len(body.ad_ids) < 2 or len(body.ad_ids) > 3:
        raise NotFoundException("Provide 2 or 3 ad IDs")

    for aid in body.ad_ids:
        ad = await ads_queries.get_ad_by_id(pool, UUID(aid))
        if not ad or not ad["is_active"]:
            raise NotFoundException(f"Ad {aid} not found")

    comparison_url = "http://localhost:8002"

    async def generate():
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0)) as client:
                async with client.stream(
                    "POST",
                    f"{comparison_url}/compare",
                    json={"ad_ids": body.ad_ids, "language": "en"},
                ) as response:
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            yield chunk
        except httpx.ConnectError:
            error = json.dumps({"type": "error", "content": "Comparison service is not running. Start it in Comparison_Analysis/ with: uvicorn app.main:app --host 0.0.0.0 --port 8002"})
            yield f"data: {error}\n\n".encode()
        except httpx.ReadTimeout:
            error = json.dumps({"type": "error", "content": "Comparison service timed out. The AI models are taking too long. Try again later."})
            yield f"data: {error}\n\n".encode()
        yield b"data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
