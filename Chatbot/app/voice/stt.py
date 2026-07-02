import io
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3-turbo"

SUPPORTED_FORMATS = {"webm", "wav", "mp3", "m4a", "ogg", "flac"}
MAX_FILE_SIZE = 25 * 1024 * 1024


class STTResult:
    text: str
    language: str
    confidence: float | None


async def _call_groq_stt(api_key: str, audio_data: bytes, ext: str) -> httpx.Response:
    files = {
        "file": (f"audio.{ext}", audio_data, f"audio/{ext}"),
    }
    data = {
        "model": GROQ_MODEL,
        "response_format": "verbose_json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await client.post(
            GROQ_STT_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files=files,
            data=data,
        )


async def transcribe_audio(audio_data: bytes, filename: str = "audio.webm") -> STTResult:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webm"
    if ext not in SUPPORTED_FORMATS:
        ext = "webm"

    if len(audio_data) > MAX_FILE_SIZE:
        raise ValueError(f"Audio file too large: {len(audio_data)} bytes (max {MAX_FILE_SIZE})")

    keys = [settings.groq_api_key]
    if settings.groq_api_key_fallback:
        keys.append(settings.groq_api_key_fallback)

    resp = None
    last_error = None
    for api_key in keys:
        try:
            resp = await _call_groq_stt(api_key, audio_data, ext)
            if resp.status_code == 200:
                break
            last_error = resp
            logger.warning("Groq STT failed with key ending ...%s: HTTP %d", api_key[-4:], resp.status_code)
        except Exception as e:
            last_error = e
            logger.warning("Groq STT error with key ending ...%s: %s", api_key[-4:], e)

    if resp is None or resp.status_code != 200:
        code = resp.status_code if resp else 0
        detail = resp.text[:500] if resp else str(last_error)
        logger.error("All Groq STT keys failed: HTTP %d - %s", code, detail)
        raise RuntimeError(f"STT service returned {code}")

    result = resp.json()
    text = (result.get("text") or "").strip()
    if not text:
        raise RuntimeError("STT returned empty transcription")

    language = result.get("language", "en")
    segments = result.get("segments", [])
    avg_confidence = None
    if segments:
        scores = [s.get("confidence", 0) for s in segments if s.get("confidence") is not None]
        if scores:
            avg_confidence = sum(scores) / len(scores)

    stt_result = STTResult()
    stt_result.text = text
    stt_result.language = language if language in ("ar", "en") else "en"
    stt_result.confidence = avg_confidence

    logger.info(
        "STT: lang=%s confidence=%.2f chars=%d",
        stt_result.language, stt_result.confidence or 0, len(text),
    )

    return stt_result
