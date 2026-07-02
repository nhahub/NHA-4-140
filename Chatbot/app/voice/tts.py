import io
import logging
import edge_tts

logger = logging.getLogger(__name__)

VOICE_MAP = {
    "ar": "ar-EG-SalmaNeural",
    "en": "en-US-JennyNeural",
}

MAX_TEXT_LENGTH = 2000


async def synthesize_speech(text: str, language: str = "en") -> bytes:
    if not text or not text.strip():
        raise ValueError("Empty text for TTS")

    text = text.strip()[:MAX_TEXT_LENGTH]
    voice = VOICE_MAP.get(language, VOICE_MAP["en"])

    communicate = edge_tts.Communicate(text, voice)
    audio_chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    if not audio_chunks:
        raise RuntimeError("TTS produced no audio output")

    audio_bytes = b"".join(audio_chunks)
    logger.info("TTS: lang=%s voice=%s text_chars=%d audio_bytes=%d", language, voice, len(text), len(audio_bytes))

    return audio_bytes
