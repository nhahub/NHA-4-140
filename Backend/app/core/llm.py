from langchain_groq import ChatGroq

from app.config import settings


def get_llm(streaming: bool = False, temperature: float = 0.2, max_tokens: int = 4096) -> ChatGroq:
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=temperature,
        streaming=streaming,
        max_tokens=max_tokens,
    )
