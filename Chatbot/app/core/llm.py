import logging
import httpx
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from app.config import settings

logger = logging.getLogger(__name__)


class OpenRouterChat(BaseChatModel):
    model: str
    api_key: str
    temperature: float = 0.2
    max_tokens: int = 4096

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise NotImplementedError("Use async only")

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system" if isinstance(m, SystemMessage) else "user", "content": m.content}
                for m in messages
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        last_error = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
            except httpx.HTTPStatusError as e:
                last_error = e
                if 500 <= e.response.status_code < 600:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        raise last_error

    @property
    def _llm_type(self) -> str:
        return "openrouter"


class FallbackLLM:
    def __init__(self, streaming: bool = False):
        self.primary = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0 if not streaming else 0.3,
            streaming=streaming,
            max_tokens=2048,
        )
        self._openrouter = None
        self.streaming = streaming

    @property
    def fallback(self):
        if self._openrouter is None:
            self._openrouter = OpenRouterChat(
                model=settings.openrouter_model,
                api_key=settings.openrouter_api_key,
                temperature=0 if not self.streaming else 0.3,
                max_tokens=2048,
            )
        return self._openrouter

    async def ainvoke(self, messages, **kwargs):
        try:
            return await self.primary.ainvoke(messages, **kwargs)
        except Exception as e:
            logger.warning("Groq failed (%s: %s), falling back to OpenRouter", type(e).__name__, str(e)[:200])
            return await self.fallback.ainvoke(messages, **kwargs)


def get_llm(streaming: bool = False) -> FallbackLLM:
    return FallbackLLM(streaming=streaming)
