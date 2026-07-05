import hashlib
from fastembed import TextEmbedding
from app.core.cache import embedding_cache


class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        full_name = f"sentence-transformers/{model_name}"
        self.model = TextEmbedding(model_name=full_name)

    def encode(self, text: str) -> list[float]:
        cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cached = embedding_cache.get(cache_key)
        if cached is not None:
            return cached
        vector = list(self.model.embed([text]))[0].tolist()
        embedding_cache.set(cache_key, vector)
        return vector
