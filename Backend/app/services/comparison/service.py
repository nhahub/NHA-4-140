import asyncio
import logging
from typing import AsyncGenerator

import asyncpg
from langchain_groq import ChatGroq

from app.services.comparison.ad_loader import load_ads
from app.services.comparison.structured_analyzer import analyze_car
from app.services.comparison.vision_analyzer import analyze_car_images
from app.services.comparison.comparison_agent import compare as compare_agent
from app.services.comparison.hallucination_guard import validate_comparison, HallucinationGuardError
from app.services.comparison.response_formatter import format_response
from app.services.comparison.models import CarAnalysis, ComparisonReport, ComparisonResult

logger = logging.getLogger(__name__)


class ComparisonService:

    def __init__(self, pool: asyncpg.Pool, llm: ChatGroq):
        self.pool = pool
        self.llm = llm

    @staticmethod
    async def create(pool: asyncpg.Pool, llm: ChatGroq) -> "ComparisonService":
        return ComparisonService(pool=pool, llm=llm)

    async def run(
        self, ad_id_1: str, ad_id_2: str
    ) -> AsyncGenerator[dict, None]:
        try:
            yield {"type": "status", "content": "Loading car details..."}
            ad1, ad2 = await load_ads(self.pool, ad_id_1, ad_id_2)

            yield {"type": "status", "content": f"Analyzing {ad1['brand']} {ad1['model']}..."}
            analysis_a = await self._analyze_single_car(ad1)

            yield {"type": "status", "content": f"Analyzing {ad2['brand']} {ad2['model']}..."}
            analysis_b = await self._analyze_single_car(ad2)

            yield {"type": "status", "content": "Generating comparison..."}
            comparison = await self._run_comparison(analysis_a, analysis_b)

            yield {"type": "status", "content": "Validating results..."}
            validate_comparison(comparison, analysis_a, analysis_b)

            report = ComparisonReport(
                car_a=analysis_a,
                car_b=analysis_b,
                comparison=comparison,
            )

            yield {"type": "report", "content": format_response(report)}
            yield {"type": "done", "content": None}

        except HallucinationGuardError as e:
            logger.error("Hallucination guard rejected comparison: %s", e)
            yield {"type": "error", "content": "Comparison validation failed. Please try again."}
            yield {"type": "done", "content": None}

        except ValueError as e:
            logger.error("Comparison failed: %s", e)
            yield {"type": "error", "content": str(e)}
            yield {"type": "done", "content": None}

        except Exception as e:
            logger.exception("Unexpected error during comparison")
            yield {"type": "error", "content": "An unexpected error occurred. Please try again."}
            yield {"type": "done", "content": None}

    async def _analyze_single_car(self, ad: dict) -> CarAnalysis:
        structured_task = analyze_car(self.llm, ad)
        vision_task = analyze_car_images(ad)

        structured, vision = await asyncio.gather(
            structured_task, vision_task, return_exceptions=True
        )

        if isinstance(structured, Exception):
            raise ValueError(f"Structured analysis failed: {structured}")

        vision_result = None
        vision_confidence = 1.0
        if isinstance(vision, Exception):
            logger.warning("Vision analysis failed: %s", vision)
        elif vision:
            vision_result = vision
            vision_confidence = vision.get("confidence", 0.5) if isinstance(vision, dict) else 0.5

        combined_confidence = round(structured.confidence * vision_confidence, 2)

        return CarAnalysis(
            ad_id=str(ad["id"]),
            brand=ad.get("brand", "Unknown"),
            model=ad.get("model", "Unknown"),
            year=ad.get("year", 0),
            price=float(ad.get("price", 0)),
            structured=structured,
            vision=vision_result,
            market=None,
            confidence=combined_confidence,
        )

    async def _run_comparison(
        self, car_a: CarAnalysis, car_b: CarAnalysis
    ) -> ComparisonResult:
        comparison = await compare_agent(self.llm, car_a, car_b)
        return comparison

    async def run_sync(self, ad_id_1: str, ad_id_2: str) -> dict:
        ad1, ad2 = await load_ads(self.pool, ad_id_1, ad_id_2)

        analysis_a_task = self._analyze_single_car(ad1)
        analysis_b_task = self._analyze_single_car(ad2)
        analysis_a, analysis_b = await asyncio.gather(analysis_a_task, analysis_b_task)

        comparison = await self._run_comparison(analysis_a, analysis_b)

        validate_comparison(comparison, analysis_a, analysis_b)

        report = ComparisonReport(
            car_a=analysis_a,
            car_b=analysis_b,
            comparison=comparison,
        )

        return format_response(report)
