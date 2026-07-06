from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    groq_api_key_fallback: str = ""
    groq_api_key_fallback2: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_model_fallback: str = "qwen/qwen3.6-27b"

    # OpenRouter for powerful LLM fallback / complex tasks
    openrouter_api_key: str = ""
    openrouter_api_key_fallback: str = ""
    openrouter_model: str = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
    openrouter_vision_model: str = "google/gemini-2.0-flash-exp:free"

    database_url: str

    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection: str = "cars_ads"

    environment: str = "development"
    chatbot_port: int = 8001

    # LangSmith tracing configuration
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = ""
    langchain_endpoint: str = "https://api.smith.langchain.com"

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def langsmith_project(self) -> str:
        if self.langchain_project:
            return self.langchain_project
        suffix = "prod" if self.environment == "production" else "dev"
        return f"deals-chatbot-{suffix}"


settings = Settings()
