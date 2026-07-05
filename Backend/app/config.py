from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: str

    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection: str = "cars_ads"

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    gemini_api_key: str
    tavily_api_key: str
    groq_api_key: str = ""
 
 
    openrouter_api_key: str = ""
    openrouter_vision_model: str = "google/gemini-2.0-flash-exp:free"

    supabase_storage_bucket: str = "car-images"
    supabase_brand_images_bucket: str = "brand-images"
    supabase_site_assets_bucket: str = "site-assets"

    comparison_service_url: str = "http://comparison:8002"

    redis_url: str | None = None

    chatbot_url: str = "http://chatbot:8001"

    environment: str = "development"
    allowed_origins: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
