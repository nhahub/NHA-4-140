import asyncio
import hashlib
import logging
from typing import Any, Optional
from langchain_groq import ChatGroq
from app.config import settings
from app.core.openrouter import OpenRouterChat
from app.core.cache import llm_response_cache

logger = logging.getLogger(__name__)

SIMPLE_TASKS = {"router", "preference_extractor", "guide_topic", "search_decision", "catalogue_check"}
COMPLEX_TASKS = {"advisor", "seller", "search", "recommendation", "general", "comparison"}

_CACHEABLE_SIMPLE = {"router", "guide_topic", "search_decision"}


class MultiLLM:
    """Multi-provider LLM with task-based routing and automatic fallback.

    - Simple tasks (routing, extraction): cheap/fast Groq model, low tokens, no stream
    - Complex tasks (advisor, seller, analysis): powerful model with streaming, higher tokens
    """

    def __init__(self):
        self._fast_groq: ChatGroq | None = None
        self._powerful_groq: ChatGroq | None = None
        self._powerful_openrouter: OpenRouterChat | None = None

    # ── Fast / cheap model for routing & extraction ──

    @property
    def fast(self) -> ChatGroq:
        if self._fast_groq is None:
            self._fast_groq = ChatGroq(
                model=settings.groq_model,
                api_key=settings.groq_api_key,
                temperature=0,
                streaming=False,
                max_tokens=1024,
            )
        return self._fast_groq

    # ── Powerful model for complex reasoning ──

    @property
    def powerful(self) -> ChatGroq | None:
        if self._powerful_groq is None and settings.groq_api_key_fallback:
            self._powerful_groq = ChatGroq(
                model=settings.groq_model_fallback or settings.groq_model,
                api_key=settings.groq_api_key_fallback,
                temperature=0.3,
                streaming=True,
                max_tokens=4096,
            )
        return self._powerful_groq

    @property
    def powerful_alt(self) -> OpenRouterChat | None:
        if self._powerful_openrouter is None and settings.openrouter_api_key:
            self._powerful_openrouter = OpenRouterChat(
                model=settings.openrouter_model,
                api_key=settings.openrouter_api_key,
                temperature=0.3,
                max_tokens=4096,
            )
        return self._powerful_openrouter

    # ── Task-based routing ──

    def get_for_task(self, task_type: str, streaming: bool = False):
        if task_type in SIMPLE_TASKS:
            return self.fast
        return self.powerful or self.fast

    # ── Non-streaming invocation with automatic fallback ──

    async def ainvoke_task(
        self,
        task_type: str,
        messages,
        **kwargs,
    ):
        llm = self.get_for_task(task_type, streaming=False)

        if task_type in SIMPLE_TASKS:
            fallbacks = [self.fast]
        else:
            fallbacks = [p for p in (self.powerful, self.powerful_alt, self.fast) if p is not None]

        if task_type in _CACHEABLE_SIMPLE:
            prompt_text = "||".join(m.content if hasattr(m, "content") else str(m) for m in messages)
            cache_key = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
            cached = llm_response_cache.get(cache_key)
            if cached is not None:
                logger.info("LLM cache hit for '%s'", task_type)
                return cached

        errors = []
        for i, provider in enumerate(fallbacks):
            try:
                result = await asyncio.wait_for(
                    provider.ainvoke(messages, **kwargs),
                    timeout=25.0,
                )
                if task_type in _CACHEABLE_SIMPLE:
                    prompt_text = "||".join(m.content if hasattr(m, "content") else str(m) for m in messages)
                    cache_key = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
                    llm_response_cache.set(cache_key, result, ttl=120)
                return result
            except asyncio.TimeoutError:
                logger.warning("%s (attempt %d/%d) timed out", task_type, i + 1, len(fallbacks))
                errors.append("timeout")
            except Exception as e:
                logger.warning("%s (attempt %d/%d) failed: %s", task_type, i + 1, len(fallbacks), str(e)[:200])
                errors.append(str(e)[:100])

        logger.error("All %d LLM providers failed for '%s': %s", len(fallbacks), task_type, "; ".join(errors))
        raise RuntimeError(f"Service temporarily unavailable. Please try again later.")

    # ── Streaming invocation with automatic fallback ──

    async def astream_task(
        self,
        task_type: str,
        messages,
        **kwargs,
    ):
        llm = self.get_for_task(task_type, streaming=True)

        if task_type in SIMPLE_TASKS:
            fallbacks = [self.fast]
        else:
            fallbacks = [p for p in (self.powerful, self.powerful_alt, self.fast) if p is not None]

        errors = []
        for i, provider in enumerate(fallbacks):
            if provider is None:
                continue
            try:
                async for chunk in provider.astream(messages, **kwargs):
                    yield chunk
                return
            except asyncio.TimeoutError:
                logger.warning("%s stream (attempt %d/%d) timed out", task_type, i + 1, len(fallbacks))
                errors.append("timeout")
            except Exception as e:
                logger.warning("%s stream (attempt %d/%d) failed: %s", task_type, i + 1, len(fallbacks), str(e)[:200])
                errors.append(str(e)[:100])

        logger.error("All %d LLM providers failed for '%s' streaming", len(fallbacks), task_type)
        raise RuntimeError(f"Service temporarily unavailable. Please try again later.")


# Singleton
llm_router = MultiLLM()
