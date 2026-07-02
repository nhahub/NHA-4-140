import asyncio
import logging
from langchain_groq import ChatGroq
from app.config import settings

logger = logging.getLogger(__name__)


class FallbackLLM:
    def __init__(self, streaming: bool = False):
        self._groq = None
        self._groq_alt = None
        self._groq_alt2 = None
        self.streaming = streaming

    @property
    def primary(self):
        if self._groq is None:
            self._groq = ChatGroq(
                model=settings.groq_model,
                api_key=settings.groq_api_key,
                temperature=0 if not self.streaming else 0.3,
                streaming=self.streaming,
                max_tokens=2048,
            )
        return self._groq

    @property
    def secondary(self):
        if self._groq_alt is None and settings.groq_api_key_fallback:
            self._groq_alt = ChatGroq(
                model=settings.groq_model,
                api_key=settings.groq_api_key_fallback,
                temperature=0 if not self.streaming else 0.3,
                streaming=self.streaming,
                max_tokens=2048,
            )
        return self._groq_alt

    @property
    def secondary2(self):
        if self._groq_alt2 is None and settings.groq_api_key_fallback2:
            self._groq_alt2 = ChatGroq(
                model=settings.groq_model_fallback,
                api_key=settings.groq_api_key_fallback2,
                temperature=0 if not self.streaming else 0.3,
                streaming=self.streaming,
                max_tokens=2048,
            )
        return self._groq_alt2

    async def _try_ainvoke(self, provider, name, messages, **kwargs):
        try:
            return await asyncio.wait_for(provider.ainvoke(messages, **kwargs), timeout=15.0)
        except asyncio.TimeoutError:
            logger.warning("%s timed out after 15s", name)
            raise

    async def _try_astream(self, provider, name, messages, **kwargs):
        chunks = []
        async for chunk in provider.astream(messages, **kwargs):
            chunks.append(chunk)
        return chunks

    async def ainvoke(self, messages, **kwargs):
        providers = [("Groq", self.primary), ("Groq (alt key)", self.secondary), ("Groq (alt key 2)", self.secondary2)]
        for name, provider in providers:
            if provider is None:
                continue
            try:
                return await self._try_ainvoke(provider, name, messages, **kwargs)
            except Exception as e:
                logger.warning("%s failed (%s: %s)", name, type(e).__name__, str(e)[:200])
        raise RuntimeError("All LLM providers unavailable. Please try again later.")

    async def astream(self, messages, **kwargs):
        providers = [("Groq", self.primary), ("Groq (alt key)", self.secondary), ("Groq (alt key 2)", self.secondary2)]
        for name, provider in providers:
            if provider is None:
                continue
            try:
                chunks = await asyncio.wait_for(self._try_astream(provider, name, messages, **kwargs), timeout=25.0)
                for chunk in chunks:
                    yield chunk
                return
            except Exception as e:
                logger.warning("%s streaming failed (%s: %s)", name, type(e).__name__, str(e)[:200])
        raise RuntimeError("All LLM providers unavailable. Please try again later.")


def get_llm(streaming: bool = False) -> FallbackLLM:
    return FallbackLLM(streaming=streaming)
