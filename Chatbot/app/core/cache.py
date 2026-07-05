import hashlib
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SemanticCache:
    """Lightweight in-memory semantic cache for LLM responses and embeddings.

    Caches by:
    - Exact prompt hash (for identical queries)
    - Configurable TTL per entry
    - LRU-style eviction when max size is reached
    """

    def __init__(self, max_size: int = 500, default_ttl: int = 3600):
        self._cache: dict[str, tuple[float, object]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl

    def _key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[object]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        timestamp, value = entry
        if time.time() - timestamp > self.default_ttl:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: object, ttl: Optional[int] = None) -> None:
        if len(self._cache) >= self.max_size:
            self._evict()
        self._cache[key] = (time.time(), value)

    def _evict(self) -> None:
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
        del self._cache[oldest_key]

    def get_or_compute(self, key: str, compute_fn, ttl: Optional[int] = None):
        cached = self.get(key)
        if cached is not None:
            return cached
        value = compute_fn()
        self.set(key, value, ttl)
        return value

    def clear(self) -> None:
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


# Singleton instances
embedding_cache = SemanticCache(max_size=1000, default_ttl=7200)
llm_response_cache = SemanticCache(max_size=300, default_ttl=1800)
