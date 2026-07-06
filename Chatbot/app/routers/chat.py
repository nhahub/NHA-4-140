import json
import asyncio
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from app.config import settings
from app.core.cost_tracker import CostTracker

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    session_token: str
    message: str
    user_id: str | None = None
    context_ad_id: str | None = None


@router.post("/message")
async def chat_message(request: ChatRequest, req: Request):
    app = req.app

    async def event_stream():
        session_token = request.session_token
        queue = asyncio.Queue()
        app.state.sse_queues[session_token] = queue

        cost_tracker = CostTracker()

        try:
            # Guardrail: input validation
            from app.core.guardrails import validate_input
            is_valid, error_msg = validate_input(request.message)
            if not is_valid:
                yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'content': None})}\n\n"
                return
            # --- History reload ---
            messages_history = []
            preferences = {}
            turn_count = 0
            intent_history = []
            pool = getattr(app.state, "pool", None)
            if pool and session_token:
                try:
                    from app.db.queries import get_chat_history, get_preferences
                    db_msgs = await get_chat_history(pool, session_token)
                    for m in db_msgs:
                        if m["role"] == "user":
                            messages_history.append(HumanMessage(content=m["content"]))
                        elif m["role"] == "assistant":
                            messages_history.append(AIMessage(content=m["content"]))
                    prefs_row = await get_preferences(pool, session_token)
                    if prefs_row:
                        pref_keys = [
                            "budget_min", "budget_max", "preferred_brands",
                            "preferred_body_types", "preferred_fuel_types",
                            "preferred_transmission", "preferred_cities",
                            "max_km_driven", "year_min", "year_max",
                            "use_case", "is_seller", "seller_car_brand",
                            "seller_car_model", "seller_car_year",
                            "seller_asking_price", "seller_intent",
                            "inferred_body_types", "inferred_min_seats",
                            "inferred_use_case",
                            "excluded_body_types", "excluded_brands",
                            "excluded_models",
                        ]
                        preferences = {k: prefs_row.get(k) for k in pref_keys if k in prefs_row}
                        intent_history = prefs_row.get("intent_history", [])
                        turn_count = prefs_row.get("turn_count", 0)
                except Exception as e:
                    logger.warning("History/preference reload failed: %s: %s", type(e).__name__, str(e)[:200])
            # --- End history reload ---

            config = {
                "callbacks": [cost_tracker],
                "run_name": f"deals-chatbot-{settings.environment}",
                "metadata": {
                    "session_id": session_token,
                    "user_id": request.user_id,
                    "conversation_id": session_token,
                    "environment": settings.environment,
                },
                "tags": ["langgraph", "chat", f"env:{settings.environment}"],
                "configurable": {
                    "thread_id": request.session_token,
                    "llm_router": getattr(app.state, "llm_router", None),
                    "llm_fast": app.state.llm_fast,
                    "llm_stream": app.state.llm_stream,
                    "cost_tracker": cost_tracker,
                    "embedder": app.state.embedder,
                    "qdrant_search": app.state.qdrant_search,
                    "db_pool": pool,
                    "sse_queue": queue,
                    "session_start": getattr(app.state, "session_start", None),
                    "web_search": getattr(app.state, "web_search", None),
                    "mcp_registry": getattr(app.state, "mcp_registry", None),
                }
            }

            input_state = {
                "messages": messages_history + [HumanMessage(content=request.message)],
                "session_token": request.session_token,
                "user_id": request.user_id,
                "context_ad_id": request.context_ad_id,
                "preferences": preferences,
                "next_node": "",
                "intent": "",
                "node_response": "",
                "retrieved_ads": [],
                "similar_ads": [],
                "price_analysis": None,
                "catalogue_check": None,
                "recommendations": [],
                "turn_count": turn_count,
                "intent_history": intent_history,
            }

            graph = app.state.graph

            async def run_graph():
                try:
                    async for _ in graph.astream(input_state, config=config, stream_mode="updates"):
                        pass
                except Exception as e:
                    logger.error("Graph stream error: %s", e, exc_info=True)
                    queue.put_nowait({"type": "error", "content": f"Graph error: {e}"})
                    queue.put_nowait({"type": "done", "content": None})

            run_task = asyncio.ensure_future(run_graph())

            done_count = 0
            while True:
                # Check for client disconnect
                if await req.is_disconnected():
                    logger.info("Client disconnected for session %s, cancelling graph", session_token)
                    run_task.cancel()
                    try:
                        await run_task
                    except asyncio.CancelledError:
                        pass
                    break

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=45.0)
                    if event.get("type") == "done":
                        done_count += 1
                        if done_count >= 1:
                            yield f"data: {json.dumps(event)}\n\n"
                            break
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'error', 'content': 'Request timed out after 45 seconds. Please try a simpler question.'})}\n\n"
                    break

            if not run_task.done():
                run_task.cancel()
                try:
                    await run_task
                except asyncio.CancelledError:
                    pass
            else:
                await run_task

            usage_summary = cost_tracker.summary()
            if usage_summary["total_llm_calls"] > 0:
                yield f"data: {json.dumps({'type': 'usage_summary', 'content': usage_summary})}\n\n"
                logger.info(
                    "Session %s | %d LLM calls | %d tokens (in: %d, out: %d) | cost: $%.6f | avg lat: %.0fms",
                    session_token[:12],
                    usage_summary["total_llm_calls"],
                    usage_summary["total_tokens"],
                    usage_summary["total_prompt_tokens"],
                    usage_summary["total_completion_tokens"],
                    usage_summary["estimated_cost_usd"],
                    usage_summary["avg_latency_ms"],
                )

        finally:
            app.state.sse_queues.pop(session_token, None)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_token}")
async def get_history(session_token: str, req: Request):
    from app.db.queries import get_chat_history, get_preferences

    pool = req.app.state.pool
    messages = await get_chat_history(pool, session_token)
    prefs = await get_preferences(pool, session_token)
    return {
        "session_token": session_token,
        "messages": [
            {
                "role": m["role"],
                "content": m["content"],
                "node_used": m.get("node_used"),
                "created_at": m["created_at"].isoformat() if m.get("created_at") else None,
            }
            for m in messages
        ],
        "preferences": dict(prefs) if prefs else {},
        "turn_count": dict(prefs).get("turn_count", 0) if prefs else 0,
    }
