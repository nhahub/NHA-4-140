from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile, Form
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
import asyncpg
import httpx
import json
import logging
import secrets

from app.dependencies import get_db, get_optional_user
from app.schemas.chat import ChatSessionRequest
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])
CHATBOT_URL = settings.chatbot_url


class MessageRequest(BaseModel):
    session_token: str
    message: str
    context_ad_id: str | None = None


@router.post("/session")
async def create_session(
    body: ChatSessionRequest,
    pool: asyncpg.Pool = Depends(get_db),
    user_id: UUID | None = Depends(get_optional_user),
):
    if user_id:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT session_token FROM chat_sessions "
                "WHERE user_id = $1 AND last_active > NOW() - INTERVAL '24 hours' "
                "ORDER BY last_active DESC LIMIT 1",
                user_id,
            )
            if row:
                return {"session_token": row["session_token"], "is_new": False}

    session_token = secrets.token_urlsafe(48)
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO chat_sessions (user_id, session_token, context_ad_id) "
            "VALUES ($1, $2, $3)",
            user_id, session_token, body.context_ad_id,
        )
    return {"session_token": session_token, "is_new": True}


@router.post("/message")
async def send_message(
    body: MessageRequest,
    pool: asyncpg.Pool = Depends(get_db),
    user_id: UUID | None = Depends(get_optional_user),
):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, user_id FROM chat_sessions WHERE session_token = $1",
            body.session_token,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        if user_id is not None and row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Session does not belong to this user")
        await conn.execute(
            "UPDATE chat_sessions SET last_active = NOW() WHERE session_token = $1",
            body.session_token,
        )

    payload = {
        "session_token": body.session_token,
        "message": body.message,
        "context_ad_id": body.context_ad_id,
        "user_id": str(user_id) if user_id else None,
    }

    async def stream_from_chatbot():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{CHATBOT_URL}/message",
                    json=payload,
                ) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except httpx.RemoteProtocolError as e:
            logger.warning("Chatbot stream closed early: %s", e)
            yield b'data: {"type": "done", "content": null}\n\n'
        except httpx.ConnectError:
            yield b'data: {"type": "error", "content": "Chatbot service unavailable"}\n\n'
            yield b'data: {"type": "done", "content": null}\n\n'
        except Exception as e:
            logger.error("Stream proxy error: %s", e, exc_info=True)
            yield b'data: {"type": "error", "content": "Something went wrong"}\n\n'
            yield b'data: {"type": "done", "content": null}\n\n'

    return StreamingResponse(
        stream_from_chatbot(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/stt")
async def proxy_stt(audio: UploadFile = File(...)):
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{CHATBOT_URL}/voice/stt",
            files={"audio": (audio.filename or "audio.webm", await audio.read(), audio.content_type or "audio/webm")},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text[:500])
        return resp.json()


@router.post("/tts")
async def proxy_tts(request: Request):
    body = await request.json()
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{CHATBOT_URL}/voice/tts",
            json=body,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text[:500])
        return Response(
            content=resp.content,
            media_type=resp.headers.get("content-type", "audio/mpeg"),
            headers={"X-Voice-Language": resp.headers.get("x-voice-language", "en")},
        )


@router.get("/history/{session_token}")
async def get_history(
    session_token: str,
    pool: asyncpg.Pool = Depends(get_db),
    user_id: UUID | None = Depends(get_optional_user),
):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, user_id FROM chat_sessions WHERE session_token = $1",
            session_token,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        if user_id is not None and row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Session does not belong to this user")

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CHATBOT_URL}/history/{session_token}")
        resp.raise_for_status()
        return resp.json()
