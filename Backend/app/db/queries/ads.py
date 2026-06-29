import asyncpg
from uuid import UUID
from typing import List


async def insert_ad(
    pool: asyncpg.Pool,
    user_id: UUID,
    brand: str,
    model: str,
    year: int,
    price: float,
    condition: str,
    km_driven: int,
    color: str | None,
    body_type: str,
    transmission: str,
    fuel_type: str,
    cc_range: str | None,
    special_conditions: str | None,
    description: str | None,
    city: str,
    idempotency_key: str | None = None,
) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO ads (user_id, brand, model, year, price, condition, km_driven,
                             color, body_type, transmission, fuel_type, cc_range,
                             special_conditions, description, city, idempotency_key)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
            RETURNING *
            """,
            user_id, brand, model, year, price, condition, km_driven,
            color, body_type, transmission, fuel_type, cc_range,
            special_conditions, description, city, idempotency_key,
        )
        return dict(row)


async def get_ad_by_id(pool: asyncpg.Pool, ad_id: UUID) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM ads WHERE id = $1", ad_id)
        return dict(row) if row else None


async def update_ad(pool: asyncpg.Pool, ad_id: UUID, **kwargs) -> dict | None:
    sets = []
    values = []
    idx = 1
    for key, val in kwargs.items():
        if val is not None:
            sets.append(f"{key} = ${idx}")
            values.append(val)
            idx += 1
    if not sets:
        return await get_ad_by_id(pool, ad_id)
    values.append(ad_id)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"UPDATE ads SET {', '.join(sets)} WHERE id = ${idx} RETURNING *",
            *values,
        )
        return dict(row) if row else None


async def soft_delete_ad(pool: asyncpg.Pool, ad_id: UUID) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE ads SET is_active = FALSE WHERE id = $1", ad_id
        )


async def list_ads(
    pool: asyncpg.Pool,
    page: int = 1,
    limit: int = 12,
    brand: str | None = None,
    model: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    condition: str | None = None,
    fuel_type: str | None = None,
    transmission: str | None = None,
    body_type: str | None = None,
    city: str | None = None,
    sort: str = "newest",
    user_id: UUID | None = None,
) -> dict:
    conditions = ["a.is_active = TRUE"]
    params = []
    idx = 1

    if user_id is not None:
        conditions.append(f"a.user_id = ${idx}")
        params.append(user_id)
        idx += 1
    if brand:
        conditions.append(f"a.brand = ${idx}")
        params.append(brand)
        idx += 1
    if model:
        conditions.append(f"a.model ILIKE ${idx}")
        params.append(f"%{model}%")
        idx += 1
    if year_min:
        conditions.append(f"a.year >= ${idx}")
        params.append(year_min)
        idx += 1
    if year_max:
        conditions.append(f"a.year <= ${idx}")
        params.append(year_max)
        idx += 1
    if price_min:
        conditions.append(f"a.price >= ${idx}")
        params.append(price_min)
        idx += 1
    if price_max:
        conditions.append(f"a.price <= ${idx}")
        params.append(price_max)
        idx += 1
    if condition:
        conditions.append(f"a.condition = ${idx}")
        params.append(condition)
        idx += 1
    if fuel_type:
        conditions.append(f"a.fuel_type = ${idx}")
        params.append(fuel_type)
        idx += 1
    if transmission:
        conditions.append(f"a.transmission = ${idx}")
        params.append(transmission)
        idx += 1
    if body_type:
        conditions.append(f"a.body_type = ${idx}")
        params.append(body_type)
        idx += 1
    if city:
        conditions.append(f"a.city = ${idx}")
        params.append(city)
        idx += 1

    where = " AND ".join(conditions)

    order_map = {
        "newest": "a.created_at DESC",
        "price_asc": "a.price ASC",
        "price_desc": "a.price DESC",
        "most_viewed": "a.views_count DESC",
    }
    order_by = order_map.get(sort, "a.created_at DESC")

    offset = (page - 1) * limit

    async with pool.acquire() as conn:
        count_row = await conn.fetchval(
            f"SELECT COUNT(*) FROM ads a WHERE {where}", *params
        )
        total = count_row or 0
        rows = await conn.fetch(
            f"SELECT a.* FROM ads a WHERE {where} ORDER BY {order_by} LIMIT ${idx} OFFSET ${idx + 1}",
            *params, limit, offset,
        )
    items = [dict(r) for r in rows]
    pages = (total + limit - 1) // limit
    return {"ads": items, "total": total, "page": page, "limit": limit, "total_pages": pages}


async def get_ads_by_ids(pool: asyncpg.Pool, ad_ids: List[UUID]) -> List[dict]:
    if not ad_ids:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM ads WHERE id = ANY($1::uuid[]) AND is_active = TRUE",
            ad_ids,
        )
        return [dict(r) for r in rows]


async def get_ad_images(pool: asyncpg.Pool, ad_id: UUID) -> List[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, url, order_index FROM ad_images WHERE ad_id = $1 ORDER BY order_index",
            ad_id,
        )
        return [{"id": str(r["id"]), "url": r["url"], "order_index": r["order_index"]} for r in rows]


async def batch_get_ad_images(pool: asyncpg.Pool, ad_ids: List[UUID]) -> dict:
    if not ad_ids:
        return {}
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, ad_id, url, order_index FROM ad_images WHERE ad_id = ANY($1::uuid[]) ORDER BY order_index",
            ad_ids,
        )
    result: dict = {}
    for r in rows:
        d = dict(r)
        aid = str(d["ad_id"])
        if aid not in result:
            result[aid] = []
        result[aid].append({"id": str(d["id"]), "url": d["url"], "order_index": d["order_index"]})
    return result


async def insert_ad_images(pool: asyncpg.Pool, ad_id: UUID, images: List[dict]) -> List[dict]:
    if not images:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "INSERT INTO ad_images (ad_id, url, order_index) "
            "SELECT $1, unnest($2::text[]), unnest($3::smallint[]) "
            "RETURNING id, url, order_index",
            ad_id,
            [img["url"] for img in images],
            [img["order_index"] for img in images],
        )
        return [dict(r) for r in rows]


async def delete_ad_image(pool: asyncpg.Pool, image_id: UUID) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "DELETE FROM ad_images WHERE id = $1 RETURNING url", image_id
        )
        return dict(row) if row else None


async def get_ad_by_idempotency_key(pool: asyncpg.Pool, key: str) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM ads WHERE idempotency_key = $1", key
        )
        return dict(row) if row else None


async def set_qdrant_synced(pool: asyncpg.Pool, ad_id: UUID, synced: bool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE ads SET qdrant_synced = $1 WHERE id = $2", synced, ad_id
        )
