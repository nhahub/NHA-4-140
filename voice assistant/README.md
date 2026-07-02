# Voice Assistant

Voice layer for the Cars Marketplace chatbot built on Groq Whisper (STT) + edge-tts (TTS).

## Architecture

```
Frontend (Next.js)              Backend API (port 8000)         Chatbot Service (port 8001)
┌──────────────┐               ┌────────────────────┐          ┌─────────────────────────────┐
│ useVoice     │── POST /stt ──▶│ proxy →            │── HTTP ──▶│ /voice/stt  → Groq Whisper  │
│ (mic capture)│  multipart    │ /api/v1/chat/stt   │          │                             │
└──────────────┘               └────────────────────┘          │ /voice/tts → edge-tts      │
┌──────────────┐               ┌────────────────────┐          └─────────────────────────────┘
│ useChat      │── SSE ────────▶│ proxy →            │── SSE ───│ /message → LangGraph        │
│ (text + TTS) │               │ /api/v1/chat/message│          └─────────────────────────────┘
└──────────────┘               └────────────────────┘
┌──────────────┐               ┌────────────────────┐
│ useTTS       │── POST /tts ──▶│ proxy →            │── HTTP ──▶ /voice/tts → audio bytes
│ (playback)   │               │ /api/v1/chat/tts   │
└──────────────┘               └────────────────────┘
```

## Files

### Backend (Chatbot service)
| File | Purpose |
|---|---|
| `Chatbot/app/voice/stt.py` | Groq Whisper integration (transcribe_audio) |
| `Chatbot/app/voice/tts.py` | edge-tts integration (synthesize_speech) |
| `Chatbot/app/voice/router.py` | FastAPI routes: POST /voice/stt, POST /voice/tts |
| `Chatbot/app/voice/__init__.py` | Package init |
| `Chatbot/app/main.py` | Registers voice router |

### Backend (API Gateway)
| File | Purpose |
|---|---|
| `Backend/app/routers/chat.py` | Proxy routes: POST /api/v1/chat/stt, POST /api/v1/chat/tts |

### Frontend
| File | Purpose |
|---|---|
| `Frontend/hooks/useVoice.ts` | Mic capture → MediaRecorder → STT → text |
| `Frontend/hooks/useTTS.ts` | TTS fetch → Audio playback |
| `Frontend/hooks/useChat.ts` | Integrated TTS on SSE stream done |
| `Frontend/components/chat/ChatInput.tsx` | Mic button (push-to-talk) |

## Phase 1 Flow

1. User taps mic button in ChatInput
2. `useVoice` starts MediaRecorder (webm opus)
3. User speaks, taps mic again to stop
4. Audio blob sent to POST /api/v1/chat/stt → Groq Whisper
5. Transcribed text returned: `{ text, language }`
6. Text sent through existing SSE chat pipeline
7. On SSE `done` event, full response text sent to POST /api/v1/chat/tts
8. edge-tts returns MP3 audio → played via HTMLAudioElement

## Requirements

- Groq API key (for Whisper) — already configured in `.env` as `GROQ_API_KEY`
- edge-tts Python package — added to `Chatbot/requirements.txt`
- Browser with MediaRecorder + getUserMedia support

## Next Phases

See `docs/voice-assistant-design.md` for Phase 2 (navigation) and Phase 3 (VAD/barge-in).
