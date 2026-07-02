import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import Response
from pydantic import BaseModel

from app.voice.stt import transcribe_audio
from app.voice.tts import synthesize_speech

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


class STTResponse(BaseModel):
    text: str
    language: str
    confidence: float | None = None


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(audio: UploadFile = File(...)):
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")

    contents = await audio.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        result = await transcribe_audio(contents, audio.filename)
        return STTResponse(
            text=result.text,
            language=result.language,
            confidence=result.confidence,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error("STT failed: %s", e)
        raise HTTPException(status_code=502, detail="Speech recognition failed")
    except Exception as e:
        logger.error("STT unexpected error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error during speech recognition")


@router.post("/tts")
async def text_to_speech(body: TTSRequest):
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="No text provided")

    try:
        audio_bytes = await synthesize_speech(body.text, body.language)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline",
                "Content-Length": str(len(audio_bytes)),
                "X-Voice-Language": body.language,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error("TTS failed: %s", e)
        raise HTTPException(status_code=502, detail="Speech synthesis failed")
    except Exception as e:
        logger.error("TTS unexpected error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error during speech synthesis")
