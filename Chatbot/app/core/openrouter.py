import asyncio
import json
import logging
import httpx
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

logger = logging.getLogger(__name__)


class OpenRouterChat(BaseChatModel):
    model: str
    api_key: str
    temperature: float = 0.2
    max_tokens: int = 4096
    _http_client: httpx.AsyncClient | None = None

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise NotImplementedError("Use async only")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=120.0)
        return self._http_client

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        client = await self._get_client()
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
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                msg = AIMessage(
                    content=content,
                    usage_metadata={
                        "input_tokens": usage.get("prompt_tokens", 0),
                        "output_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                )
                return ChatResult(
                    generations=[ChatGeneration(message=msg)],
                    llm_output={"token_usage": usage} if usage else None,
                )
            except httpx.HTTPStatusError as e:
                last_error = e
                if 500 <= e.response.status_code < 600:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning("OpenRouter timeout (attempt %d/3): %s", attempt + 1, str(e)[:200])
                await asyncio.sleep(2 ** attempt)
                continue
        raise last_error or RuntimeError("OpenRouter request failed after 3 retries")

    async def astream(self, messages, stop=None, run_manager=None, **kwargs):
        client = await self._get_client()
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
            "stream": True,
        }

        last_error = None
        last_usage = {}
        for attempt in range(3):
            try:
                async with client.stream(
                    "POST",
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    content_parts = []
                    async for chunk in response.aiter_lines():
                        if chunk.startswith("data: "):
                            data_str = chunk[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                usage_chunk = data.get("usage")
                                if usage_chunk:
                                    last_usage = usage_chunk
                                choices = data.get("choices", [{}])
                                delta = choices[0].get("delta", {}) if choices else {}
                                content = delta.get("content", "")
                                if content:
                                    content_parts.append(content)
                                    yield AIMessage(content=content)
                            except json.JSONDecodeError:
                                continue
                full_content = "".join(content_parts)
                if full_content and last_usage:
                    yield AIMessage(
                        content="",
                        usage_metadata={
                            "input_tokens": last_usage.get("prompt_tokens", 0),
                            "output_tokens": last_usage.get("completion_tokens", 0),
                            "total_tokens": last_usage.get("total_tokens", 0),
                        },
                    )
                return
            except httpx.HTTPStatusError as e:
                last_error = e
                if 500 <= e.response.status_code < 600:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning("OpenRouter timeout (attempt %d/3): %s", attempt + 1, str(e)[:200])
                await asyncio.sleep(2 ** attempt)
                continue
            except Exception as e:
                last_error = e
                logger.warning("OpenRouter stream error (attempt %d/3): %s", attempt + 1, str(e)[:200])
                await asyncio.sleep(2 ** attempt)
                continue
        raise last_error or RuntimeError("OpenRouter stream failed after 3 retries")

    @property
    def _llm_type(self) -> str:
        return "openrouter"

    async def close(self):
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
