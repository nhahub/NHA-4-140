import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)

MODEL_PRICING = {
    "groq": {"input": 0.15, "output": 0.60},
    "openrouter": {"input": 0.20, "output": 0.80},
}

MODEL_ALIASES = {
    "openai/gpt-oss-120b": "groq",
}


def _detect_provider(model_name: str) -> str:
    for alias, provider in MODEL_ALIASES.items():
        if alias in model_name.lower():
            return provider
    if "openrouter" in model_name.lower():
        return "openrouter"
    return "groq"


def _estimate_cost(provider: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(provider, MODEL_PRICING["groq"])
    input_cost = (prompt_tokens / 1000) * pricing["input"]
    output_cost = (completion_tokens / 1000) * pricing["output"]
    return round(input_cost + output_cost, 6)


class UsageRecord:
    __slots__ = ("run_id", "task_type", "model", "provider", "prompt_tokens",
                 "completion_tokens", "total_tokens", "estimated_cost_usd",
                 "start_time", "end_time", "latency_ms")
    def __init__(self, run_id: str, task_type: str, model: str):
        self.run_id = run_id
        self.task_type = task_type
        self.model = model
        self.provider = _detect_provider(model)
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.estimated_cost_usd = 0.0
        self.start_time = datetime.now(timezone.utc)
        self.end_time: Optional[datetime] = None
        self.latency_ms = 0

    def finish(self, prompt_tokens: int, completion_tokens: int):
        self.end_time = datetime.now(timezone.utc)
        self.latency_ms = int((self.end_time - self.start_time).total_seconds() * 1000)
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.estimated_cost_usd = _estimate_cost(self.provider, prompt_tokens, completion_tokens)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "task_type": self.task_type,
            "model": self.model,
            "provider": self.provider,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "latency_ms": self.latency_ms,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class CostTracker(BaseCallbackHandler):
    """Tracks LLM token usage and estimated costs across all graph nodes.

    Integrates with LangSmith: each LLM call gets a run name matching the
    task type, so traces are grouped by node/agent in the LangSmith UI.
    """

    raise_error: bool = False

    def __init__(self):
        super().__init__()
        self._runs: dict[str, UsageRecord] = {}
        self._completed: list[dict] = []
        self._node_tag: str = ""

    def set_node_tag(self, node_name: str):
        self._node_tag = node_name

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        task_type = (metadata or {}).get("task_type", "unknown")
        if task_type == "unknown":
            task_type = (metadata or {}).get("langgraph_node", "") or "unknown"
        model_name = ""
        if serialized:
            model_name = serialized.get("kwargs", {}).get("model", "") or serialized.get("name", "")
        if not model_name:
            model_name = (metadata or {}).get("model_name", "unknown")
        record = UsageRecord(str(run_id), task_type, model_name)
        self._runs[str(run_id)] = record

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> Any:
        record = self._runs.pop(str(run_id), None)
        if record is None:
            return

        prompt_tokens = 0
        completion_tokens = 0
        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            prompt_tokens = usage.get("prompt_tokens", 0) or 0
            completion_tokens = usage.get("completion_tokens", 0) or 0
        elif response.generations:
            gen = response.generations[0][0]
            msg = getattr(gen, "message", None)
            if msg and hasattr(msg, "usage_metadata") and msg.usage_metadata:
                prompt_tokens = msg.usage_metadata.get("input_tokens", 0) or 0
                completion_tokens = msg.usage_metadata.get("output_tokens", 0) or 0

        record.finish(prompt_tokens, completion_tokens)
        self._log_usage(record)
        self._completed.append(record.to_dict())

    def _log_usage(self, record: UsageRecord):
        d = record.to_dict()
        node = f"[{self._node_tag}] " if self._node_tag else ""
        logger.info(
            "%s%s | tokens: %d input + %d output = %d | cost: $%.6f | latency: %dms",
            node, record.task_type,
            d["prompt_tokens"], d["completion_tokens"], d["total_tokens"],
            d["estimated_cost_usd"], d["latency_ms"],
        )

    def get_session_usage(self) -> list[dict]:
        return [r.to_dict() for r in self._runs.values()]

    def get_completed_usage(self) -> list[dict]:
        return list(self._completed)

    def summary(self) -> dict:
        total_prompt = sum(r["prompt_tokens"] for r in self._completed)
        total_completion = sum(r["completion_tokens"] for r in self._completed)
        total_cost = sum(r["estimated_cost_usd"] for r in self._completed)
        total_latency = sum(r["latency_ms"] for r in self._completed)
        calls = len(self._completed)
        return {
            "total_llm_calls": calls,
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "estimated_cost_usd": round(total_cost, 6),
            "total_latency_ms": total_latency,
            "avg_latency_ms": round(total_latency / calls, 1) if calls else 0,
            "calls": list(self._completed),
        }

    def reset(self):
        self._runs.clear()
        self._completed.clear()
        self._node_tag = ""
