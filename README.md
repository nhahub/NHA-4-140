# Deals — AI-Powered Car Marketplace for Egypt

Smart car buying & selling powered by artificial intelligence.

**Tech Stack:** Next.js 16 · FastAPI · LangGraph · Qdrant · Docker

---

## Solution Overview

Deals is a full-stack AI car marketplace with 3 microservices and a modern frontend, fully containerized. Buyers and sellers interact with an intelligent chatbot, search cars via semantic understanding, compare vehicles with AI analysis, and get market price insights — all in Arabic or English.

### Features

| Feature | Description |
|---|---|
| **🧠 AI Chat Assistant** | 10-node LangGraph conversational agent — searches, advises, compares, guides |
| **🔎 Semantic Search** | Hybrid BM25 + vector search on Qdrant with 11 field filters and quality evaluation |
| **⚖️ AI Comparison** | Head-to-head analysis with web research, 6-category scoring, and hallucination guard |
| **📊 Price Analysis** | AI-powered market price estimation from DuckDuckGo + Tavily research |
| **🗣️ Voice Assistant** | STT via Groq Whisper + TTS via edge-tts — Arabic & English |
| **📈 Observability** | Prometheus + Grafana + Loki — metrics, dashboards, and log aggregation |

---

## System Architecture

```
                   ┌──────────────┐
                   │  User Browser │
                   └──────┬───────┘
                          │
                   ┌──────┴───────┐
                   │    Nginx     │  :80 (Reverse Proxy)
                   │  Buffering   │
                   └──┬───────┬───┘
                      │       │
              ┌───────┘       └───────┐
              │                       │
      ┌───────┴───────┐      ┌───────┴───────┐
      │   Frontend    │      │  API Gateway  │
      │ Next.js 16    │      │ FastAPI :8000 │
      │ :3000         │      │ JWT Auth      │
      └───────────────┘      └───────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
          ┌─────────┴───┐  ┌────────┴──────┐  ┌──────┴──────────┐
          │   Chatbot   │  │  Comparison   │  │   Monitoring    │
          │ FastAPI     │  │ FastAPI :8002 │  │ Prometheus :9090│
          │ LangGraph   │  │ Tavily        │  │ Grafana :3001   │
          │ :8001       │  │ OpenRouter    │  │ Loki :3100      │
          └─────────────┘  └───────────────┘  └─────────────────┘
```

### External Services

- **Supabase PostgreSQL** — primary database
- **Qdrant Cloud** — vector database (384-dim, cosine)
- **Groq API** — fast LLM inference
- **OpenRouter** — fallback LLM provider + vision
- **Redis** — caching layer

---

## Key Features (Deep Dive)

### 🔎 Hybrid Semantic Search

Hybrid BM25 full-text + vector cosine search fused via RRF (Reciprocal Rank Fusion).

- **Model:** all-MiniLM-L6-v2 (384-dim)
- **Database:** Qdrant Cloud, collection `cars_ads`
- **Filters:** 11 payload indexes — brand, model, city, fuel, transmission, body_type, price range, year, km_driven, condition, is_active
- **Quality evaluation:** top_score > 0.65 AND avg_score > 0.5 → broader retry on low scores
- **Embedding text:** brand + model + year + body_type + fuel_type + transmission + condition + city + cc_range + description + special_conditions

### 🧠 LangGraph AI Assistant

A 10-node directed state machine with 5 specialist nodes:

1. **Preference Extractor** — analyzes message, extracts car preferences
2. **Router** — classifies intent, routes to one of 7 specialists
3. **Specialists:** Catalogue, Search, Recommend, Advisor, Seller, Guide, General
4. **Responder** — collects results, formats SSE stream, delivers response

Specialists call MCP tools via a centralized registry. Each tool call follows: Agent → MCP Client → MCP Server → external data → response back.

### 🛠️ MCP Architecture — 10 Tools, 2 Servers

**Car-Search Server** (5 tools): `search_cars`, `get_car_details`, `find_similar_cars`, `check_catalogue`, `get_car_images`

**Analysis Server** (5 tools): `analyze_market_price`, `web_search`, `get_website_guide`, `expand_brand_origins`, `expand_colloquial_terms`

All tools use in-process transport. If MCP fails, agents fall back to direct Qdrant/PostgreSQL queries.

### ⚖️ AI Comparison Engine

Pipeline: Select 2 cars → Load specs from DB → Web research (Tavily) → AI analyzes & scores → Hallucination guard → Stream report

**Scoring categories (0-10):** Value for Money, Reliability, Running Cost, Resale Value, Condition (via CV photo analysis), Overall (weighted)

**Hallucination Guard — 5 checks:**
- Claim trace-back to source data
- No unsupported accident claims
- No unsupported mechanical faults
- Confidence consistency
- Winner validity

### 📊 Price Analysis

1. User provides make + model + year
2. Redis cache check (1hr TTL)
3. 7 parallel DuckDuckGo queries → Tavily fallback
4. AI extracts low/average/high prices in EGP
5. Cache result → return to user

### 🗣️ Voice Assistant

Complete pipeline: User speaks → Browser captures audio (WebM/Opus, ≤25MB) → Sent to backend → Groq Whisper STT → AI Chat processes → edge-tts TTS → Response spoken

- **Arabic:** `ar-EG-SalmaNeural`
- **English:** `en-US-JennyNeural`
- Auto-detects language and responds in the same language

---

## LLM Fallback Chain

| Provider | Model | Use | Temp |
|---|---|---|---|
| Groq (Fast) | openai/gpt-oss-120b | Routing, extraction | 0.0 |
| Groq (Powerful) | qwen/qwen3.6-27b | Complex reasoning | 0.3 |
| OpenRouter (Fallback) | nvidia/nemotron-3-nano | Fallback complex | 0.3 |
| OpenRouter (Vision) | google/gemini-2.0-flash-exp | Image + comparison | 0.1-0.2 |
| Groq (Backend) | llama-3.3-70b-versatile | Comparison analysis | 0.2 |

Fallback logic: Primary → OpenRouter → Groq fast → RuntimeError. Timeouts: 25s / 60s streaming.

---

## Data Layer

### PostgreSQL (Supabase)

Core tables: `ads`, `users`, `ad_images`, `favorites`, `chat_messages`, `chat_sessions`, `user_preferences`, `ad_views`

Storage: logos, wallpapers, ad images (JPEG/WebP/PNG, ≤5MB)

### Qdrant Vector DB

- Collection: `cars_ads`, 384-dim, Cosine distance
- 11 payload indexes: bool (`is_active`), float (`price`), integer (`year`, `km_driven`), keyword (`brand`, `model`, `city`, `fuel`, `transmission`, `body_type`)
- BM25 text index for hybrid search

### Redis Caching

| Key Pattern | TTL |
|---|---|
| `cache:brand-counts` | 300s |
| `cache:compare-ai:{id1}:{id2}` | 1800s |
| `compare:{md5}:{lang}` | 3600s |
| `price:{make}:{model}:{year}` | 3600s |
| `llm_response_cache` | 120s |
| In-memory embedding cache | 7200s |

Graceful degradation: Redis unreachable → operation is a no-op → auto-reconnects and repopulates.

---

## Docker — 9 Containers

All services run on the `cars_net` bridge network via `infra/docker-compose.yml`:

| Service | Port | Image/Dockerfile |
|---|---|---|
| Frontend | :3000 | Frontend/Dockerfile |
| Nginx | :80 | nginx:alpine |
| Backend | :8000 | Backend/Dockerfile |
| Chatbot | :8001 | Chatbot/Dockerfile |
| Comparison | :8002 | Comparison_Analysis/Dockerfile |
| Redis | :6379 | redis:alpine |
| Prometheus | :9090 | prom/prometheus |
| Grafana | :3001 | grafana/grafana |
| Loki + Promtail | :3100 | grafana/loki, grafana/promtail |

### Makefile Commands

```
make setup     Create .env from template
make up        docker compose up -d
make build     Rebuild & start all
make logs      Follow service logs (svc=<name>)
make down      Stop all services
```

---

## Frontend

**Core:** Next.js 16 · TypeScript · Tailwind CSS 3 · Zustand · Framer Motion · Recharts · Lucide React · React Hook Form · Zod · next-intl

**i18n:** Full English + Arabic RTL (Inter + Cairo fonts)

**Pages:** `/` (hero), `/ads` (grid + filters), `/ads/[id]` (detail + AI advisor), `/chat` (full chat + voice), `/compare` (head-to-head), `/search` (results), `/profile` (settings)

**Stores:** `authStore` (JWT, auto-refresh), `chatStore` (SSE messages, sessions), `compareStore` (sessionStorage tray)

---

## Monitoring

- **Prometheus** scrapes all 3 services every 15s at `/metrics`
- **Grafana** — "FastAPI Service Overview" dashboard with 9 panels (Requests/sec, Duration p50/p95/p99, HTTP Error %, LLM Calls/sec, Token Usage, Latency, Cost/Hour, Fallback Rate, Search Quality)
- **Loki + Promtail** auto-discovers Docker containers and pushes logs

Key metrics tracked: `http_requests_total`, `llm_calls_total{service, task_type}`, `llm_tokens_total`, `llm_latency_seconds`, `llm_cost_total_usd`, `llm_fallback_total`, `comparison_requests_total`, `search_quality_total`

---

## Key Design Decisions

| Decision | Alternative Considered | Why This Won |
|---|---|---|
| **Hybrid BM25 + Vector (RRF)** | Pure vector search | Vector missed exact keyword matches (e.g., "520i"). BM25 + RRF captures both keyword precision and semantic intent. |
| **3-Tier LLM Fallback** | Single-provider (Groq only) | Groq is fast but limited. OpenRouter adds redundancy and access to vision/reasoning models. |
| **Hallucination Guard (5 checks)** | Trust LLM output directly | LLMs fabricate specs. The 5-check system prevents inaccurate data from reaching users. |
| **Graceful Degradation** (Redis, MCP, LLM) | Hard dependencies | Every layer has a fallback — no single point of failure. |

---

## Getting Started

```bash
# Prerequisites: Docker, git

# 1. Clone
git clone <repo-url>
cd genzcars-team

# 2. Create environment file
make setup

# 3. Edit .env with your API keys (see .env.template)

# 4. Start all services
make up
```

The app will be available at `http://localhost`.
