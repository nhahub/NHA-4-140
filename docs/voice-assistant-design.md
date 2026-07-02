# Voice Assistant — Technical Design Document

## Overview

Add a voice layer to the existing LangGraph chatbot that lets users speak in Arabic/English and get spoken responses + trigger client-side navigation. Voice flows through the existing SSE streaming architecture with minimal new infrastructure.

---

## 1. ARCHITECTURE — Voice I/O Flow

### Recommended: Server-side STT + TTS (hybrid)

| Component | Where | Tool | Rationale |
|---|---|---|---|
| **Audio capture** | **Browser** | `MediaRecorder` API + `AnalyserNode` (VAD) | Zero bundle cost; native browser API |
| **STT** | **Chatbot service** (server) | **Groq hosted Whisper** (`whisper-large-v3-turbo`) | Accurate bilingual Arabic/English; Groq is free/fast; consistent across all browsers |
| **TTS** | **Chatbot service** (server) | **edge-tts** (Python library) | Free; excellent Arabic voice support (`ar-EG-SalmaNeural`, `ar-SA-ZariyahNeural`); natural prosody; no API keys |

### Flow diagram

```
┌── Browser ──────────────────────────────────┐     ┌── Chatbot (FastAPI :8001) ──────────────────────┐
│                                              │     │                                                   │
│  [Mic] → MediaRecorder → Audio Blob           │────▶│  POST /stt  →  Groq Whisper  →  transcribed text │
│                                              │     │                      │                            │
│  [ChatInput shows transcript, user confirms]  │     │                      ▼                            │
│                                              │     │  POST /message (existing)                         │
│  [useChat] → SSE connection                    │◀────│  ← SSE stream (token, cars, status, done)        │
│                                              │     │                      │                            │
│  [on SSE "done"] →                           │     │                      ▼                            │
│    fetch /tts with full response text         │────▶│  POST /tts  →  edge-tts  →  audio bytes          │
│                                              │◀────│                                                    │
│  [AudioContext/HTMLAudioElement] → playback    │     │                                                   │
│                                              │     │                                                   │
└──────────────────────────────────────────────┘     └───────────────────────────────────────────────────┘
```

### Latency budget (estimated)

| Step | Time |
|---|---|
| VAD (silence detection after utterance) | ~300ms |
| Audio upload (small, ~50-200KB) | ~100ms |
| Groq Whisper inference | ~300-600ms |
| LangGraph agent processing | ~800ms-4s (dominates) |
| edge-tts generation | ~200-400ms |
| Audio download + playback start | ~200ms |
| **Total** | **~2-5s** — acceptable for turn-taking conversation |

The main bottleneck is **LangGraph**, not STT/TTS. This is fine — the user already experiences this latency via text. Voice doesn't make it worse.

### Why not client-side STT/TTS?

- **Web Speech API `SpeechRecognition`**: Arabic support is unreliable / only works in Chrome/Edge; no control over model quality.
- **Web Speech API `SpeechSynthesis`**: Arabic voices are robotic, OS-dependent; can't customize.
- **Server-side Whisper** gives us production-grade bilingual accuracy (Groq's `whisper-large-v3-turbo` is purpose-built for this).
- **edge-tts** is free and produces near-human Arabic speech — worth the network round-trip.

### Where to add new endpoints

All in the **Chatbot service** (port 8001), keeping the Backend API Gateway (port 8000) as thin proxy:

- `POST /stt` — accepts multipart audio, returns `{ "text": "...", "language": "ar|en" }`
- `POST /tts` — accepts `{ "text": "...", "language": "ar|en" }`, returns `audio/mpeg` stream

The Backend gateway adds transparent proxy routes: `/api/v1/chat/stt` → `POST /stt`, `/api/v1/chat/tts` → `POST /tts`.

---

## 2. INTENT SEPARATION — Navigation vs Chat vs Mixed

### Current router output

The existing LangGraph router classifies into: `search_node | advisor_node | seller_node | guide_node | general_node`.

### Recommended: Extended router node (single-stage)

Rather than adding a separate pre-classifier, extend the existing `router` node to also emit navigation actions alongside its node selection. This minimizes graph changes and reuses the existing LLM call.

The router prompt gets an additional output field:

```
If the user wants to navigate or perform an action on the website,
include a navigation_action in your response.

Examples:
- "take me to SUVs" → search_node + navigate to /search?body_type=suv
- "open my saved listings" → general_node + navigate to /profile/favorites
- "go to compare page" → general_node + navigate to /compare
- "find me sedans and show them" → search_node + navigate to /search?body_type=sedan

Respond with JSON:
{"next_node": "search_node|...", "navigation_action": {"type": "navigate|open_ad|open_compare|filter", "target": "...", "params": {...}} | null}
```

### State changes

```python
class CarsChatState(TypedDict):
    # ... existing fields ...
    navigation_action: dict | None          # {"type": "navigate", "target": "..."} | None
    current_page: str | None                # e.g., "/search", "/ads/123"
    voice_language: str | None              # "ar" | "en"
```

**`current_page`** is sent by the frontend with every message (added to `ChatRequest`). The agent uses this to resolve relative navigation ("go back" → previous page).

**`voice_language`** lets the agent respond in the same language the user spoke.

### How the graph routes

| Pre-classifier result | Action |
|---|---|
| Navigation only (no chat) | Bypass LangGraph entirely; emit SSE `action` event immediately, then `done` |
| Chat only (no navigation) | Normal flow through existing graph (preference_extractor → router → node → responder) |
| Mixed (both) | Inject `navigation_action` into state; run through graph; `responder_node` emits both text/events + `action` event |

### Navigation intent taxonomy

| Intent | Action type | Example targets |
|---|---|---|
| Navigate to page | `navigate` | `/search?body_type=suv`, `/compare`, `/profile/saved`, `/ads/new` |
| Open specific ad | `open_ad` | `/ads/123` |
| Open compare with cars | `open_compare` | `/compare?ids=1,2,3` |
| Apply filter on current page | `filter` | `{ filter: "body_type", value: "suv" }` |
| Open chat (if voice trigger from elsewhere) | `open_chat` | N/A |
| Scroll to section | `scroll_to` | `#search-results` |

---

## 3. NAVIGATION EXECUTION — Backend to Frontend

### Recommended: Structured JSON action via new SSE event type

**New SSE event**:

```json
{"type": "action", "content": {"action": "navigate", "target": "/listings?body_type=suv", "replace": false}}
{"type": "action", "content": {"action": "open_ad", "id": "123"}}
{"type": "action", "content": {"action": "open_compare", "ids": ["1", "2", "3"]}}
```

This integrates seamlessly with the **existing SSE architecture**:

- The `SSEParser` already handles generic `{ type, content }` events via `onEvent`
- The `useChat` hook adds a `case 'action':` in its event switch
- The action handler uses **Next.js `useRouter()`** from `next/navigation`

### Frontend handler pattern

```typescript
// New hook: useVoiceNavigation.ts
'use client'
import { useRouter } from 'next/navigation'

export function useVoiceNavigation() {
  const router = useRouter()

  const handleAction = (action: VoiceAction) => {
    switch (action.type) {
      case 'navigate':
        action.replace ? router.replace(action.target) : router.push(action.target)
        break
      case 'open_ad':
        router.push(`/ads/${action.adId}`)
        break
      case 'open_compare':
        router.push(`/compare?ids=${action.adIds?.join(',')}`)
        break
      case 'filter':
        const params = new URLSearchParams(window.location.search)
        params.set(action.filter!, action.value!)
        router.push(`${window.location.pathname}?${params.toString()}`)
        break
    }
  }

  return { handleAction }
}
```

### Integration into `useChat.ts`

```typescript
// In the onEvent callback:
case 'action':
  handleAction(event.content)
  break
```

### TTS playback

```typescript
const playTTS = async (text: string, lang: string) => {
  const res = await fetch('/api/v1/chat/tts', {
    method: 'POST',
    body: JSON.stringify({ text, language: lang }),
  })
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const audio = new Audio(url)
  audio.onended = () => { URL.revokeObjectURL(url) }
  return audio.play()
}
```

---

## 4. STATE / CONTEXT

### Recommendation: Reuse existing LangGraph state

The current `CarsChatState` already handles multi-turn perfectly:

| Field | Role in voice flow |
|---|---|
| `messages` | Full conversation history (text + transcribed voice) |
| `preferences` | Accumulated preferences across turns ("sedans... under 300k" updates budget_max) |
| `intent_history` | Track what user has been doing |
| `context_ad_id` | Which ad they're viewing (important for "open this one") |

No separate session layer needed. The existing `MemorySaver` checkpointing + Postgres persistence handles everything.

### Multi-turn scenario walkthrough

```
User: "show me sedans"
→ STT → agent: search_node → SSE: cars + token "Here are available sedans..."
→ Frontend shows cars, speaks response

User: "actually make that under 300k"
→ STT → agent: search_node again, prefs.budget_max=300000, re-queries Qdrant with updated filter
→ SSE: cars + token "Here are sedans under 300k..."

User: "open the first one"
→ STT → agent: navigation_action={type:"open_ad", adId: first car's id}
→ SSE: action event → Frontend router.push("/ads/123")
```

This works because `preferences` are accumulated via the existing `preference_extractor` node + `upsert_user_preferences`, and `retrieved_ads` persists across turns.

---

## 5. FRONTEND IMPLEMENTATION — Mic Capture & Playback

### Recommended: Minimal, no heavy dependencies

**Mic capture** (in `ChatInput.tsx` or a new `VoiceInput` component):

```typescript
// No new npm dependencies — all native APIs
const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
const chunks: Blob[] = []
mediaRecorder.ondataavailable = (e) => chunks.push(e.data)
mediaRecorder.onstop = async () => {
  const audioBlob = new Blob(chunks, { type: 'audio/webm' })
  const formData = new FormData()
  formData.append('audio', audioBlob)
  const { text, language } = await fetch('/api/v1/chat/stt', { method: 'POST', body: formData }).then(r => r.json())
  sendMessage(text) // uses existing useChat.sendMessage
}
```

**VAD (Voice Activity Detection)** — optional, Phase 2:
- Use `@ricky0123/vad-web` (~75KB gzipped wasm) for automatic speech end detection
- Or simpler: silence-based with `AnalyserNode` (no dependency)

**Bundle impact**: ~0KB from third-party audio libraries (Phase 1). Only native APIs.

### Web Speech API fallback (progressive enhancement)

```typescript
const fallbackSTT = async (): Promise<string> => {
  return new Promise((resolve, reject) => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)()
    recognition.lang = 'ar-EG'
    recognition.onresult = (e) => resolve(e.results[0][0].transcript)
    recognition.onerror = () => reject('Speech recognition failed')
    recognition.start()
  })
}
```

Used when:
1. The dedicated `/stt` endpoint fails (network error, server error)
2. Or as an optimistic alternative — try `/stt` first, if it's slow/offline, fall back to Web Speech

---

## 6. UX CONSIDERATIONS

### Activation

**Phase 1**: **Push-to-talk** — a mic button next to the text input. Press and hold to record, release to send. This is the most reliable, simplest UX.

```
[ChatInput]
┌──────────────────────────────────────┬──────┬──────────┐
│                                      │  🎤  │  📤      │
│  This is the text input area...      │ (hold│ (send)   │
│                                      │  to  │          │
│                                      │ talk)│          │
└──────────────────────────────────────┴──────┴──────────┘
```

**Phase 2**: **Toggle mode** — tap mic to start listening continuously with VAD. Tap again to stop.

### Barge-in / Interruption

When the user speaks while the assistant is responding:

```
1. VAD detects new speech
2. Frontend: audio.pause() / audio.src = '' (stop TTS playback)
3. If SSE is still streaming: useSSE.stop() (AbortController.abort())
4. State: the partial assistant message is kept in chat (committed)
5. New STT request starts immediately
6. User's new speech is transcribed and sent as next message
```

### Fallback

| Failure mode | Behavior |
|---|---|
| Mic permission denied | Hide mic button; text-only chat works unchanged |
| STT endpoint down | Toast error + fall back to Web Speech API if available |
| Both STT fail | Show input for manual typing with pre-filled transcription attempt if any |
| TTS endpoint down | Text-only response (existing behavior) — no error shown |
| Browser doesn't support MediaRecorder | Hide mic button (detected via `typeof MediaRecorder === 'undefined'`) |

### Language handling

- `POST /stt` returns `{ text, language: "ar" | "en" }` — Whisper auto-detects
- The transcribed text is displayed in a user message bubble as-is
- `POST /tts` uses the detected language to select the appropriate voice (`ar-EG-SalmaNeural` or `en-US-JennyNeural`)
- The LLM is already prompted to respond in the same language as the user (existing behavior in `RESPONSE_SYSTEM` prompts)

---

## 7. PHASING — Rollout Plan

### Phase 1: Push-to-Talk Voice Chat (1 PR)

**Scope**: End-to-end voice I/O for chat only (no navigation yet)

**Backend changes** (`Chatbot/`):
- Add `POST /stt` endpoint using Groq Whisper
- Add `POST /tts` endpoint using edge-tts
- Add Python dependencies: `openai` (for Groq Whisper API), `edge-tts`
- Proxy routes in `Backend/` (`/api/v1/chat/stt`, `/api/v1/chat/tts`)

**Frontend changes** (`Frontend/`):
- Add `VoiceInput` component with mic button in `ChatInput.tsx`
- Add `useVoice.ts` hook (mic capture → STT → fill text input)
- Add `useTTS.ts` hook (after SSE `done` → fetch TTS → play audio)
- Add voice language to `ChatRequest` schema (auto-detected from STT)
- Handle Web Speech API fallback

**No changes to LangGraph, state, or SSE** — text goes into the same pipeline.

**Verification**: Speak Arabic → hear Arabic response. Speak English → hear English response. Text chat still works identically.

---

### Phase 2: Voice Navigation (1 PR)

**Scope**: Navigational intents trigger frontend routing

**Backend changes** (`Chatbot/`):
- Add `navigation_action` field to `CarsChatState`
- Modify `router` node prompt to output `navigation_action` alongside the node selection (JSON output)
- Update `responder_node` to emit new SSE event type `action` when `navigation_action` is set
- Add `current_page` to `ChatRequest` schema (sent from frontend on every message)
- Add a `navigation_node` to the graph for handling pure navigation-only intents (bypasses LLM generation)

**Frontend changes** (`Frontend/`):
- Add `useVoiceNavigation` hook (wraps `useRouter`)
- Add `case 'action':` to `useChat` SSE event handler
- Send `current_pathname` with every `POST /chat/message`
- Test each navigation intent: "go to SUVs", "open saved", "compare page", "open first car"

---

### Phase 3: UX Polish (1 PR)

**Scope**: Hands-free VAD, barge-in, Web Speech fallback polish

- Add `@ricky0123/vad-web` for automatic VAD (toggle mode)
- Implement barge-in logic in `useChat` + TTS coordination
- Add `voice_language` persistence per session (auto-detect once, remember)
- Add mic level indicator (AudioContext AnalyserNode, ~20 lines)
- Keyboard shortcut for push-to-talk (Space to hold, release to send)
- `useSSE` improvements — allow reconnection / abort coordination

---

### Phase 4: Production (1 PR)

**Scope**: Caching, analytics, robustness

- Cache common TTS responses (keyed by `text+language`) in Redis or disk
- User voice settings (preferred voice, rate, pitch) — persist to Supabase user_prefs
- Analytics: STT confidence scores, voice vs text usage breakdown, language distribution
- Arabic dialect handling: STT normalization for Egyptian vs Gulf Arabic
- Rate limiting on `/stt` and `/tts`
- Load testing / latency monitoring

---

## Key Tradeoffs Summary

| Decision | Chosen | Rejected | Reason |
|---|---|---|---|
| STT location | Server (Groq Whisper) | Client (Web Speech) | Arabic accuracy, browser consistency |
| TTS location | Server (edge-tts) | Client (SpeechSynthesis) | Voice quality, Arabic support |
| Audio format | WebM/opus → WAV for STT | Raw PCM | Standard browser output; server converts if needed |
| Intent separation | Extended router node | Separate pre-classifier | Minimizes graph changes; leverages existing LLM call |
| Navigation action | New `action` SSE event | Response header / separate endpoint | Integrates with existing SSE consumer pattern |
| State reuse | Extend `CarsChatState` fields | New session layer | Multi-turn already works; minimal additions needed |
| VAD / wake word | Push-to-talk first | Always-listening | Simplest reliable UX; VAD added in Phase 3 |
| Bundle impact | Zero third-party audio libs | MediaRecorder polyfills | All modern browsers support MediaRecorder |
