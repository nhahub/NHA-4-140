from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List


class ImageResponse(BaseModel):
    id: str
    url: str
    order_index: int


class AdResponse(BaseModel):
    id: str
    user_id: str
    seller: dict | None = None
    brand: str
    model: str
    year: int
    price: float
    condition: str
    km_driven: int
    color: str | None = None
    body_type: str
    transmission: str
    fuel_type: str
    cc_range: str | None = None
    special_conditions: str | None = None
    description: str | None = None
    city: str
    cover_image_url: str | None = None
    images: List[ImageResponse] = []
    views_count: int = 0
    is_favorited: bool = False
    qdrant_synced: bool = False
    created_at: datetime
    updated_at: datetime


class AdListResponse(BaseModel):
    ads: List[AdResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class AdCreate(BaseModel):
    brand: str
    model: str
    year: int
    price: float
    condition: str
    km_driven: int

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        if v not in ("new", "used"):
            raise ValueError("condition must be 'new' or 'used'")
        return v
    color: str | None = None
    body_type: str
    transmission: str
    fuel_type: str
    cc_range: str | None = None
    special_conditions: str | None = None
    description: str | None = None
    city: str


class AdUpdate(BaseModel):
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    price: float | None = None
    condition: str | None = None
    km_driven: int | None = None

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str | None) -> str | None:
        if v is not None and v not in ("new", "used"):
            raise ValueError("condition must be 'new' or 'used'")
        return v
    color: str | None = None
    body_type: str | None = None
    transmission: str | None = None
    fuel_type: str | None = None
    cc_range: str | None = None
    special_conditions: str | None = None
    description: str | None = None
    city: str | None = None
