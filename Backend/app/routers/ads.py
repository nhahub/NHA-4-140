from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, Request, HTTPException
from typing import List, Optional
import asyncpg
import io

from app.schemas.ads import AdResponse, AdListResponse, AdUpdate
from app.schemas.common import ErrorResponse
from app.dependencies import get_db, get_current_user, get_optional_user, get_qdrant, get_embedder
from app.db.queries import ads as ads_queries
from app.db.queries import views as views_queries
from app.services.ads_service import get_ad_response, batch_ad_response
from app.services.storage_service import upload_file, delete_file
from app.services.indexing_pipeline import index_ad, delete_ad_from_qdrant
from app.core.exceptions import NotFoundException, ForbiddenException, UnsupportedMediaTypeException, FileTooLargeException, StorageUploadException
from app.services.storage_service import StorageUploadError
from app.config import settings

router = APIRouter(prefix="/ads", tags=["ads"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/webp", "image/png"}
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_FILES = 10


@router.get("", response_model=AdListResponse)
async def list_ads(
    page: int = 1,
    limit: int = 12,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    condition: Optional[str] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
    body_type: Optional[str] = None,
    city: Optional[str] = None,
    sort: str = "newest",
    pool: asyncpg.Pool = Depends(get_db),
    current_user: UUID | None = Depends(get_optional_user),
):
    if limit > 50:
        limit = 50
    result = await ads_queries.list_ads(
        pool, page=page, limit=limit, brand=brand, model=model,
        year_min=year_min, year_max=year_max, price_min=price_min,
        price_max=price_max, condition=condition, fuel_type=fuel_type,
        transmission=transmission, body_type=body_type, city=city, sort=sort,
    )
    result["ads"] = await batch_ad_response(pool, result["ads"], current_user)
    return result


@router.get("/brand-counts")
async def brand_counts(
    pool: asyncpg.Pool = Depends(get_db),
):
    brands = await ads_queries.get_brand_counts(pool)
    supabase_url = settings.supabase_url.rstrip("/")
    bucket = settings.supabase_brand_images_bucket
    result = []
    for b in brands:
        brand_name = b["brand"]
        filename = brand_name.replace(" ", "_") + ".png"
        logo_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{filename}"
        result.append({
            "brand": brand_name,
            "count": b["count"],
            "logo_url": logo_url,
        })
    return {"brands": result}


@router.get("/{ad_id}", response_model=AdResponse)
async def get_ad(
    ad_id: UUID,
    background_tasks: BackgroundTasks,
    pool: asyncpg.Pool = Depends(get_db),
    current_user: UUID | None = Depends(get_optional_user),
    request: Request = None,
):
    ad = await ads_queries.get_ad_by_id(pool, ad_id)
    if not ad or not ad["is_active"]:
        raise NotFoundException("Ad not found or has been removed")
    if current_user is None or current_user != ad["user_id"]:
        viewer_ip = request.client.host if request.client else "0.0.0.0"
        if not await views_queries.has_recent_view(pool, ad_id, current_user, viewer_ip):
            background_tasks.add_task(
                views_queries.increment_views_count, pool, ad_id
            )
            background_tasks.add_task(
                views_queries.insert_ad_view, pool, ad_id, current_user, viewer_ip
            )
    return await get_ad_response(pool, ad, current_user)


@router.post("", status_code=201, response_model=AdResponse)
async def create_ad(
    background_tasks: BackgroundTasks,
    brand: str = Form(...),
    model: str = Form(...),
    year: int = Form(...),
    price: float = Form(...),
    condition: str = Form(...),
    km_driven: int = Form(...),
    color: Optional[str] = Form(None),
    body_type: str = Form(...),
    transmission: str = Form(...),
    fuel_type: str = Form(...),
    cc_range: Optional[str] = Form(None),
    special_conditions: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    city: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    pool: asyncpg.Pool = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    request: Request = None,
):
    if condition not in ("new", "used"):
        raise HTTPException(status_code=422, detail="condition must be 'new' or 'used'")
    if len(files) > MAX_FILES:
        raise FileTooLargeException("Maximum 10 images allowed")
    idempotency_key = request.headers.get("x-idempotency-key")
    if idempotency_key:
        existing = await ads_queries.get_ad_by_idempotency_key(pool, idempotency_key)
        if existing:
            return await get_ad_response(pool, existing, user_id)
    ad = await ads_queries.insert_ad(
        pool, user_id, brand, model, year, price, condition, km_driven,
        color, body_type, transmission, fuel_type, cc_range,
        special_conditions, description, city, idempotency_key,
    )
    ad_id = ad["id"]

    supabase = request.app.state.supabase
    uploaded_images = []
    for idx, f in enumerate(files):
        if idx >= MAX_FILES:
            break
        if f.content_type not in ALLOWED_IMAGE_TYPES:
            continue
        contents = await f.read()
        if len(contents) > MAX_FILE_SIZE:
            continue
        path = f"ads/{ad_id}/{idx}.jpg"
        try:
            url = upload_file(supabase, settings.supabase_storage_bucket, path, contents, f.content_type)
        except StorageUploadError:
            raise StorageUploadException(f"Failed to upload image {f.filename}")
        uploaded_images.append({"url": url, "order_index": idx})

    if uploaded_images:
        await ads_queries.insert_ad_images(pool, ad_id, uploaded_images)

    cover_url = uploaded_images[0]["url"] if uploaded_images else None

    background_tasks.add_task(
        index_ad, pool, request.app.state.qdrant, request.app.state.embedder,
        ad_id, ad, cover_url,
    )

    return await get_ad_response(pool, ad, user_id)


@router.patch("/{ad_id}", response_model=AdResponse)
async def update_ad(
    ad_id: UUID,
    body: AdUpdate,
    background_tasks: BackgroundTasks,
    pool: asyncpg.Pool = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    request: Request = None,
):
    ad = await ads_queries.get_ad_by_id(pool, ad_id)
    if not ad:
        raise NotFoundException("Ad not found")
    if ad["user_id"] != user_id:
        raise ForbiddenException("You do not own this ad")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        return await get_ad_response(pool, ad, user_id)

    updated = await ads_queries.update_ad(pool, ad_id, **update_data)
    if not updated:
        raise NotFoundException("Ad not found")

    indexed_fields = {"brand", "model", "year", "price", "description", "city",
                      "condition", "fuel_type", "transmission", "body_type",
                      "cc_range", "special_conditions"}
    if indexed_fields & set(update_data.keys()):
        images = await ads_queries.get_ad_images(pool, ad_id)
        cover_url = images[0]["url"] if images else None
        background_tasks.add_task(
            index_ad, pool, request.app.state.qdrant, request.app.state.embedder,
            ad_id, updated, cover_url,
        )

    return await get_ad_response(pool, updated, user_id)


@router.delete("/{ad_id}")
async def delete_ad(
    ad_id: UUID,
    background_tasks: BackgroundTasks,
    pool: asyncpg.Pool = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    request: Request = None,
):
    ad = await ads_queries.get_ad_by_id(pool, ad_id)
    if not ad:
        raise NotFoundException("Ad not found")
    if ad["user_id"] != user_id:
        raise ForbiddenException("You do not own this ad")

    await ads_queries.soft_delete_ad(pool, ad_id)

    background_tasks.add_task(
        delete_ad_from_qdrant, pool, request.app.state.qdrant, ad_id
    )

    return {"message": "ad deleted"}


@router.post("/{ad_id}/images")
async def add_images(
    ad_id: UUID,
    files: List[UploadFile] = File(...),
    pool: asyncpg.Pool = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    request: Request = None,
):
    ad = await ads_queries.get_ad_by_id(pool, ad_id)
    if not ad:
        raise NotFoundException("Ad not found")
    if ad["user_id"] != user_id:
        raise ForbiddenException("You do not own this ad")

    existing = await ads_queries.get_ad_images(pool, ad_id)
    next_idx = max((img["order_index"] for img in existing), default=-1) + 1

    supabase = request.app.state.supabase
    uploaded = []
    for f in files[:MAX_FILES]:
        if f.content_type not in ALLOWED_IMAGE_TYPES:
            continue
        contents = await f.read()
        if len(contents) > MAX_FILE_SIZE:
            continue
        path = f"ads/{ad_id}/{next_idx}.jpg"
        try:
            url = upload_file(supabase, settings.supabase_storage_bucket, path, contents, f.content_type)
        except StorageUploadError:
            raise StorageUploadException(f"Failed to upload image {f.filename}")
        uploaded.append({"url": url, "order_index": next_idx})
        next_idx += 1

    images = await ads_queries.insert_ad_images(pool, ad_id, uploaded)
    return {"images": images}


@router.delete("/{ad_id}/images/{image_id}")
async def delete_image(
    ad_id: UUID,
    image_id: UUID,
    pool: asyncpg.Pool = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    request: Request = None,
):
    ad = await ads_queries.get_ad_by_id(pool, ad_id)
    if not ad:
        raise NotFoundException("Ad not found")
    if ad["user_id"] != user_id:
        raise ForbiddenException("You do not own this ad")

    result = await ads_queries.delete_ad_image(pool, image_id)
    if not result:
        raise NotFoundException("Image not found")

    supabase = request.app.state.supabase
    path = result["url"].split(f"{settings.supabase_storage_bucket}/")[-1]
    delete_file(supabase, settings.supabase_storage_bucket, path)

    return {"message": "image deleted"}
