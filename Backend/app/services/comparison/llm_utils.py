import json
import logging

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)


async def parse_llm_json(llm: ChatGroq, system: str, human: str) -> dict:
    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=human),
    ])
    content = response.content.strip()

    result = _try_parse_json(content)
    if result is not None:
        return result

    logger.warning("LLM JSON parse failed on first attempt, retrying with stricter prompt")
    retry_response = await llm.ainvoke([
        SystemMessage(content=system + "\nYour previous response was not valid JSON. Return ONLY the JSON object, nothing else, no markdown formatting."),
        HumanMessage(content=human),
    ])
    retry_content = retry_response.content.strip()
    result = _try_parse_json(retry_content)
    if result is not None:
        return result

    raise ValueError("LLM failed to return valid JSON after retry")


def _try_parse_json(content: str) -> dict | None:
    cleaned = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
