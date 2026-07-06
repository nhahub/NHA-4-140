import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/price-analysis", tags=["price-analysis"])


class PriceAnalysisRequest(BaseModel):
    make: str
    model: str
    year: int


@router.post("")
async def price_analysis(body: PriceAnalysisRequest):
    comparison_url = settings.comparison_service_url
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            resp = await client.post(
                f"{comparison_url}/price-analysis",
                json={"make": body.make, "model": body.model, "year": body.year},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        return JSONResponse(
            status_code=503,
            content={"error": "Price analysis service is not available. Start Comparison_Analysis service."},
        )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"error": "Price analysis service timed out. Try again later."},
        )
