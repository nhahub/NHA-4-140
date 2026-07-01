import asyncpg
from uuid import UUID


async def has_recent_view(
    pool: asyncpg.Pool,
    ad_id: UUID,
    user_id: UUID | None,
    viewer_ip: str,
) -> bool:
    async with pool.acquire() as conn:
        if user_id:
            row = await conn.fetchval(
                "SELECT 1 FROM ad_views WHERE ad_id = $1 AND user_id = $2 LIMIT 1",
                ad_id, user_id,
            )
        else:
            row = await conn.fetchval(
                "SELECT 1 FROM ad_views WHERE ad_id = $1 AND viewer_ip = $2::inet LIMIT 1",
                ad_id, viewer_ip,
            )
        return bool(row)


async def increment_views_count(pool: asyncpg.Pool, ad_id: UUID) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE ads SET views_count = views_count + 1 WHERE id = $1",
            ad_id,
        )


async def insert_ad_view(
    pool: asyncpg.Pool,
    ad_id: UUID,
    user_id: UUID | None,
    viewer_ip: str,
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO ad_views (ad_id, user_id, viewer_ip) VALUES ($1, $2, $3::inet)",
            ad_id, user_id, viewer_ip,
        )
