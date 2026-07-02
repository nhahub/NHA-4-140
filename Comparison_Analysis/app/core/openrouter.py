from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models import BaseChatModel
from app.config import settings
import httpx
import json


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
                    from langchain_core.outputs import ChatResult, ChatGeneration
                    from langchain_core.messages import AIMessage
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


def get_openrouter_llm() -> OpenRouterChat:
    return OpenRouterChat(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        temperature=0.2,
        max_tokens=4096,
    )
