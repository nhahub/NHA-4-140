import logging
from uuid import UUID

import asyncpg

from app.core.exceptions import NotFoundException
from app.db.queries import ads as ads_queries

logger = logging.getLogger(__name__)


async def load_ads(pool: asyncpg.Pool, ad_id_1: str, ad_id_2: str) -> tuple[dict, dict]:
    if ad_id_1 == ad_id_2:
        raise NotFoundException("Cannot compare an ad with itself")

    ad1 = await ads_queries.get_ad_by_id(pool, UUID(ad_id_1))
    if not ad1 or not ad1.get("is_active"):
        raise NotFoundException(f"Ad {ad_id_1} not found or inactive")

    ad2 = await ads_queries.get_ad_by_id(pool, UUID(ad_id_2))
    if not ad2 or not ad2.get("is_active"):
        raise NotFoundException(f"Ad {ad_id_2} not found or inactive")

    images1 = await ads_queries.get_ad_images(pool, ad1["id"])
    images2 = await ads_queries.get_ad_images(pool, ad2["id"])

    ad1["images"] = images1
    ad2["images"] = images2

    logger.info("Loaded ads %s and %s for comparison", ad_id_1, ad_id_2)
    return ad1, ad2
