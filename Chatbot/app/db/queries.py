import asyncpg
from typing import List
from uuid import UUID


async def upsert_user_preferences(pool: asyncpg.Pool, session_token: str, user_id: str | None, prefs: dict) -> None:
    fields = {
        "user_id": user_id,
        "budget_min": prefs.get("budget_min"),
        "budget_max": prefs.get("budget_max"),
        "preferred_brands": prefs.get("preferred_brands"),
        "preferred_body_types": prefs.get("preferred_body_types"),
        "preferred_fuel_types": prefs.get("preferred_fuel_types"),
        "preferred_transmission": prefs.get("preferred_transmission"),
        "preferred_cities": prefs.get("preferred_cities"),
        "max_km_driven": prefs.get("max_km_driven"),
        "year_min": prefs.get("year_min"),
        "year_max": prefs.get("year_max"),
        "use_case": prefs.get("use_case"),
        "is_seller": prefs.get("is_seller", False),
        "seller_car_brand": prefs.get("seller_car_brand"),
        "seller_car_model": prefs.get("seller_car_model"),
        "seller_car_year": prefs.get("seller_car_year"),
        "seller_asking_price": prefs.get("seller_asking_price"),
        "seller_intent": prefs.get("seller_intent"),
        "intent_history": prefs.get("intent_history"),
        "turn_count": prefs.get("turn_count", 0),
        "inferred_body_types": prefs.get("inferred_body_types"),
        "inferred_min_seats": prefs.get("inferred_min_seats"),
        "inferred_use_case": prefs.get("inferred_use_case"),
        "excluded_body_types": prefs.get("excluded_body_types"),
        "excluded_brands": prefs.get("excluded_brands"),
        "excluded_models": prefs.get("excluded_models"),
    }

    col_names = list(fields.keys())
    # $1 is session_token, so field placeholders start at $2
    updates = [f"{k} = EXCLUDED.{k}" for k in col_names]

    async with pool.acquire() as conn:
        await conn.execute(
            f"""
            INSERT INTO user_preferences (session_token, {', '.join(col_names)})
            VALUES ($1::VARCHAR, $2::uuid, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21,
                    $22, $23, $24, $25, $26, $27)
            ON CONFLICT (session_token)
            DO UPDATE SET
                user_id                = EXCLUDED.user_id::uuid,
                budget_min             = EXCLUDED.budget_min,
                budget_max             = EXCLUDED.budget_max,
                preferred_brands       = EXCLUDED.preferred_brands,
                preferred_body_types   = EXCLUDED.preferred_body_types,
                preferred_fuel_types   = EXCLUDED.preferred_fuel_types,
                preferred_transmission = EXCLUDED.preferred_transmission,
                preferred_cities       = EXCLUDED.preferred_cities,
                max_km_driven          = EXCLUDED.max_km_driven,
                year_min               = EXCLUDED.year_min,
                year_max               = EXCLUDED.year_max,
                use_case               = EXCLUDED.use_case,
                is_seller              = EXCLUDED.is_seller,
                seller_car_brand       = EXCLUDED.seller_car_brand,
                seller_car_model       = EXCLUDED.seller_car_model,
                seller_car_year        = EXCLUDED.seller_car_year,
                seller_asking_price    = EXCLUDED.seller_asking_price,
                seller_intent          = EXCLUDED.seller_intent,
                intent_history         = EXCLUDED.intent_history,
                turn_count             = EXCLUDED.turn_count,
                inferred_body_types    = EXCLUDED.inferred_body_types,
                inferred_min_seats     = EXCLUDED.inferred_min_seats,
                inferred_use_case      = EXCLUDED.inferred_use_case,
                excluded_body_types    = EXCLUDED.excluded_body_types,
                excluded_brands        = EXCLUDED.excluded_brands,
                excluded_models        = EXCLUDED.excluded_models
            """,
            session_token,
            user_id,
            fields["budget_min"],
            fields["budget_max"],
            fields["preferred_brands"],
            fields["preferred_body_types"],
            fields["preferred_fuel_types"],
            fields["preferred_transmission"],
            fields["preferred_cities"],
            fields["max_km_driven"],
            fields["year_min"],
            fields["year_max"],
            fields["use_case"],
            fields["is_seller"],
            fields["seller_car_brand"],
            fields["seller_car_model"],
            fields["seller_car_year"],
            fields["seller_asking_price"],
            fields["seller_intent"],
            fields["intent_history"],
            fields["turn_count"],
            fields["inferred_body_types"],
            fields["inferred_min_seats"],
            fields["inferred_use_case"],
            fields["excluded_body_types"],
            fields["excluded_brands"],
            fields["excluded_models"],
        )


async def insert_chat_message(
    pool: asyncpg.Pool,
    session_token: str,
    role: str,
    content: str,
    node_used: str | None = None,
    referenced_ad_ids: List[str] | None = None,
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO chat_messages (session_token, role, content, node_used, referenced_ad_ids) "
            "VALUES ($1::VARCHAR, $2, $3, $4, $5)",
            session_token, role, content, node_used, referenced_ad_ids,
        )


async def get_chat_history(pool: asyncpg.Pool, session_token: str) -> List[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT role, content, node_used, created_at FROM chat_messages "
            "WHERE session_token = $1::VARCHAR ORDER BY created_at",
            session_token,
        )
        return [dict(r) for r in rows]


async def get_preferences(pool: asyncpg.Pool, session_token: str) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM user_preferences WHERE session_token = $1::VARCHAR",
            session_token,
        )
        return dict(row) if row else None


async def get_new_matching_ads(
    pool: asyncpg.Pool,
    session_created_at,
    prefs: dict,
) -> List[dict]:
    conditions = ["is_active = TRUE", "created_at > $1"]
    params = [session_created_at]
    idx = 2
    if prefs.get("preferred_brands"):
        conditions.append(f"brand = ANY(${idx}::varchar[])")
        params.append(prefs["preferred_brands"])
        idx += 1
    if prefs.get("preferred_cities"):
        conditions.append(f"city = ANY(${idx}::varchar[])")
        params.append(prefs["preferred_cities"])
        idx += 1
    if prefs.get("budget_max"):
        conditions.append(f"price <= ${idx}")
        params.append(prefs["budget_max"])
        idx += 1
    if prefs.get("budget_min"):
        conditions.append(f"price >= ${idx}")
        params.append(prefs["budget_min"])
        idx += 1

    where = " AND ".join(conditions)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT id, brand, model, year, price, city, condition, body_type, "
            f"transmission, fuel_type, km_driven, created_at FROM ads WHERE {where} "
            f"ORDER BY created_at DESC LIMIT 5",
            *params,
        )
        return [dict(r) for r in rows]


async def check_catalogue_availability(
    pool: asyncpg.Pool,
    brand: str | None = None,
    model: str | None = None,
    year: int | None = None,
    body_type: str | None = None,
) -> dict:
    """Check if any active ads match the exact metadata filters."""
    conditions = ["is_active = TRUE"]
    params: list = []
    idx = 1
    if brand:
        conditions.append(f"LOWER(brand) = LOWER(${idx}::varchar)")
        params.append(brand)
        idx += 1
    if model:
        conditions.append(f"LOWER(model) = LOWER(${idx}::varchar)")
        params.append(model)
        idx += 1
    if year:
        conditions.append(f"year = ${idx}::integer")
        params.append(year)
        idx += 1
    if body_type:
        conditions.append(f"LOWER(body_type) = LOWER(${idx}::varchar)")
        params.append(body_type)
        idx += 1

    where = " AND ".join(conditions)
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            f"SELECT COUNT(*) FROM ads WHERE {where}", *params
        )
        rows = await conn.fetch(
            f"SELECT id, brand, model, year, price, body_type, city, condition, "
            f"transmission, fuel_type, km_driven FROM ads WHERE {where} LIMIT 5",
            *params,
        )
        return {"count": count, "ads": [dict(r) for r in rows]}


async def get_ad_images_by_ids(pool: asyncpg.Pool, ad_ids: List[UUID]) -> dict:
    if not ad_ids:
        return {}
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, ad_id, url, order_index FROM ad_images "
            "WHERE ad_id = ANY($1::uuid[]) ORDER BY order_index",
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
