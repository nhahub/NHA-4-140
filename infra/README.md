# Cars Marketplace — Local Dev Setup

## Prerequisites

- Docker Desktop installed and running
- All secrets ready (Supabase, Qdrant Cloud, Groq, Tavily)
- The `infra/` folder sits alongside the 4 service folders

## Quick Start

### Using make (recommended)

```bash
cd infra
make setup       # creates .env from template
# edit .env and fill in all secrets
make build       # builds all images + starts containers
```

### Using docker compose directly

```bash
# 1. Create .env from template
copy .env.example .env

# 2. Edit .env and fill in all secrets

# 3. Build and start all services
docker compose up -d --build

# 4. Stop all services
docker compose down
```

Visit **http://localhost** — the full app should be live.

## Service URLs

| URL | Service |
|-----|---------|
| http://localhost | Next.js frontend (via nginx) |
| http://localhost:8000/docs | Backend Swagger UI |
| http://localhost:8001/docs | Chatbot Swagger UI |
| http://localhost:8002/docs | Comparison Swagger UI |

## Daily Commands

| Command | What it does |
|---------|-------------|
| `make up` | Start all services (already built) |
| `make down` | Stop all services |
| `make build` | Rebuild all images + start |
| `make rebuild svc=backend` | Rebuild + restart one service |
| `make restart svc=chatbot` | Restart one service |
| `make logs` | Tail logs for all services |
| `make logs svc=backend` | Tail logs for one service |
| `make ps` | Show container status |
| `make clean` | Stop + remove volumes |
| `make nuke` | Remove everything including images |

## Architecture

```
Browser ──> nginx (:80)
                │
        ┌───────┼───────────────┐
        │       │               │
    frontend  /api/*      SSE routes
    (:3000)    │               │
            backend      backend
            (:8000)     (chat/compare)
               │
        ┌──────┴──────┐
    chatbot     comparison
    (:8001)      (:8002)
```

- All internal traffic uses container names (`backend:8000`, `chatbot:8001`)
- Browser calls `http://localhost` — nginx routes to the right service
- SSE routes (`/api/v1/chat/`, `/api/v1/compare`) have `proxy_buffering off`
- Chat SSE timeout: 3600s. Compare SSE timeout: 180s.

## Architecture Diagrams

Open **`docs/multi-agent-architecture.html`** in a browser for interactive visualizations of:

- **Multi-Agent Graph** — LangGraph node flow with all edges (preference_extractor → router → specialist nodes → responder)
- **Node Details & Tool Calling** — every node's LLM calls, database queries, vector search calls, and web search usage
- **Tool Calling Matrix** — per-node tool usage table
- **LLM Fallback Chain** — 3-tier Groq → OpenRouter fallback architecture
- **Data Flow Diagram (DFD)** — end-to-end data flow from browser through backend, chatbot, vector DB, and external APIs
- **SSE Event Stream** — sequence diagram showing event order during a request

## Folder Structure Expected

```
cars-marketplace/
├── backend/
├── chatbot/
├── comparison-analysis/
├── frontend/
└── infra/              ← run all make commands from here
```

## Troubleshooting

**Service won't start**: `make logs svc=<name>` to see errors

**SSE not streaming**: verify `proxy_buffering off` and `X-Accel-Buffering: no` in nginx.conf

**Frontend can't reach API**: `NEXT_PUBLIC_API_URL` must be `http://localhost/api/v1` (through nginx)

**Hot reload not working**: Python services use `--reload` flag. Next.js HMR goes through `/_next/webpack-hmr` in nginx.
