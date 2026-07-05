# Architecture Walkthrough & Bug Analysis

## Current Architecture

### Full Node List & Routing Triggers

The LangGraph has **10 nodes** with this exact flow:

```
preference_extractor  (always runs first, extracts preferences from last message)
       ↓
    router  (classifies intent via LLM)
       ↓  (conditional on state["next_node"])
    ┌─── catalogue_node ──────────────────────────────────┐
    │   "find cars, browse, show me, recommend, offers"   │
    │   (conditional: search_node or recommendation_node)  │
    ├─── advisor_node ─────────────────────────────────────┤
    │   "is this a good deal? should I buy?" (specific car)│
    ├─── seller_node ──────────────────────────────────────┤
    │   "I want to sell, price my car"                     │
    ├─── guide_node ───────────────────────────────────────┤
    │   "how do I use the website?"                        │
    └─── general_node ─────────────────────────────────────┤
       ↓
   responder_node  (streams tokens, emits ads/cards, persists to DB)
       ↓
      END
```

**Edges:**
- `preference_extractor → router` (static, always runs)
- `router → (catalogue_node | advisor_node | seller_node | guide_node | general_node)` (conditional on `state["next_node"]`)
- `catalogue_node → (search_node | recommendation_node)` (conditional, via `route_after_catalogue` reading `state["next_node"]`)
- `search_node → responder_node` (static)
- `recommendation_node → responder_node` (static)
- `advisor_node → responder_node` (static)
- `seller_node → responder_node` (static)
- `guide_node → responder_node` (static)
- `general_node → responder_node` (static)
- `responder_node → END` (static)

### Router Triggers

From `router.py` — the LLM classifies into exactly one of five targets:

| Route | Trigger Keywords |
|---|---|
| `catalogue_node` | find, browse, filter, recommendations, specs, budget, brand, condition, "show me cars", "recommend", "suggest", "what should I buy", "best car", "help me choose", "offer me" (buying context) |
| `advisor_node` | Question about a SPECIFIC car already in results or on the car detail page. "Is this a good deal?", "what are the problems?", "should I buy it?" |
| `seller_node` | "I want to sell", "I'm offering my car", pricing/listing advice |
| `guide_node` | How to use the website: post ad, filter, compare, favorites, contact seller |
| `general_node` | General car knowledge, reliability, maintenance, insurance, news, greetings, unclear intent |

**Context variables injected:** `{message_history}`, `{has_context}` (is `context_ad_id` set?), `{is_seller}`, `{preferences_summary}`, `{latest_message}`.

### Models Per Node

| Node | Task name | Provider | Model |
|---|---|---|---|
| preference_extractor | `preference_extractor` | Groq (fast) | `openai/gpt-oss-120b` |
| router | `router` | Groq (fast) | `openai/gpt-oss-120b` |
| catalogue_node | `catalogue_check` | Groq (fast) | `openai/gpt-oss-120b` |
| search_node (query builder) | `search` | Groq (powerful) → OpenRouter → Groq (fast) | `qwen/qwen3.6-27b` → `nvidia/nemotron-...` → `openai/gpt-oss-120b` |
| search_node (response stream) | `search` | same chain | same |
| recommendation_node | `recommendation` | same chain | same |
| advisor_node | `advisor` | same chain | same |
| seller_node | `seller` | same chain | same |
| guide_node | `guide_topic` / `guide` | Groq (fast) / same chain | `openai/gpt-oss-120b` / chain |
| general_node | `search_decision` / `general` | Groq (fast) / same chain | same |
| responder_node | *(no LLM call)* | — | — |

**Task classification** (`llm.py`):

```python
SIMPLE_TASKS  = {"router", "preference_extractor", "guide_topic", "search_decision", "catalogue_check"}
COMPLEX_TASKS = {"advisor", "seller", "search", "recommendation", "general", "comparison"}
```

- Simple tasks use `ChatGroq(model=settings.groq_model, temperature=0, streaming=False, max_tokens=1024)` — no fallback chain, single attempt with 25s timeout.
- Complex tasks use fallback chain: `[powerful Groq, powerful_alt OpenRouter, fast Groq]` with 25s timeout per attempt.

### Conversation Memory & State Persistence

**Mechanism:** PostgreSQL `INSERT ... ON CONFLICT (session_token) DO UPDATE SET` — full row replacement per turn.

**Per-turn data flow:**

1. **Load** (`chat.py:42-73`): At request start, `get_chat_history()` fetches all past messages ordered by `created_at`, reconstructs them as LangChain `HumanMessage`/`AIMessage` objects. `get_preferences()` fetches the full `user_preferences` row for the `session_token`.

2. **Run graph**: The graph mutates state — `preference_extractor` updates `preferences`, specialist nodes set `node_response` and `retrieved_ads`, etc.

3. **Save** (`responder_node.py:86-118`): Three fire-and-forget DB writes:
   - `insert_chat_message` — one row for user message, one for assistant response
   - `upsert_user_preferences` — **full replace** of the entire preference row

**Preferences ARE cumulative** across turns. The `preference_extractor` merge logic appends to lists and overwrites scalars each turn against the loaded previous preferences.

**What's NOT persisted between turns:** `retrieved_ads`, `similar_ads`, `node_response`, `catalogue_check`, `recommendations` — ephemeral per-turn state.

### `CarsChatState` Fields

```python
messages:           Annotated[list, add_messages]
next_node:          str
intent:             str
session_token:      str
user_id:            str | None
context_ad_id:      str | None
preferences:        UserPreferences  # 18 sub-fields
retrieved_ads:      list[dict]
similar_ads:        list[dict]
price_analysis:     dict | None
node_response:      str
catalogue_check:    dict | None
recommendations:    list[dict]
turn_count:         int
intent_history:     list[str]
```

### `UserPreferences` Sub-schema

```python
budget_min:            float | None
budget_max:            float | None
preferred_brands:      list[str]
preferred_body_types:  list[str]
preferred_fuel_types:  list[str]
preferred_transmission: str | None
preferred_cities:      list[str]
max_km_driven:         int | None
year_min:              int | None
year_max:              int | None
use_case:              str | None
is_seller:             bool
seller_car_brand:      str | None
seller_car_model:      str | None
seller_car_year:       int | None
seller_asking_price:   float | None
seller_intent:         str | None
```

**Notable absence:** Zero fields for negative/excluded preferences. No `excluded_body_types`, `excluded_brands`, `disliked_models`, etc.

## Bug 3 — Comparison requests are not fulfilled

### Root cause

**"comparison" is a stub in the task-type system but was never wired as a graph node.**

Evidence:

- `llm.py:13` includes `"comparison"` in `COMPLEX_TASKS` — if a comparison task were ever invoked, it would route to the powerful LLM.
- But `builder.py` has **no `comparison_node`** added to the graph. A glob for `**/comparison_node*` returns **0 files**.
- The router prompt (`router.py:6-40`) lists only 5 routing targets. `"comparison"` is **not among them**.
- When a user says "make a comparison", the router classifies it as `catalogue_node` (most likely — "browse/compare cars"). The `catalogue_node` runs a catalogue check and routes to `search_node`, which does a vector search — not a comparison.
- The only comparison-related code in the Chatbot service is in `guide_node` (explaining the website's "Add to Compare" UI feature) and `general_node`'s general knowledge prompt (mentioning "fuel economy comparisons").
- A separate `Comparison_Analysis` service exists in the repo (port 8002) with its own API, but the chatbot graph never calls it.

### Impact

Any request containing "comparison", "compare", or "مقارنة" triggers a standard catalogue search with generic filler text. No car-to-car comparison is ever performed.

## Bug 4 — Preference extractor misses implicit/need-based signals

### Root cause

**The `EXTRACT_SYSTEM_PROMPT` does literal keyword extraction only. It has zero instructions for semantic need inference.**

The prompt lists exact JSON fields and says "use null if not mentioned." For "I have a family and want a big car for travel":

- No body-type keyword like "SUV" appears → `preferred_body_types` stays unchanged/empty.
- `use_case` might capture `"family car for travel"`, but **`use_case` is never consumed** by any downstream node.
- The `search_node`'s `QUERY_BUILDER_SYSTEM` doesn't read `use_case`.
- The `RESPONSE_SYSTEM` and `ADVISOR_SYSTEM` don't evaluate result fit against `use_case` or any preference.
- The only "inference" in the prompt is the country→brand mapping (`format_brand_origins_prompt()`).

### Impact

A user can state their need in rich natural language ("family", "travel", "big", "comfortable") and the system treats it as if nothing was said. A sedan and an SUV both score similarly on the semantic vector and get returned without discrimination.

## Bug 5 — No persistent preference memory for rejections

### Root cause

**The `UserPreferences` state schema has no field for negative/excluded preferences.**

When the user says "sedan is not what I want":

- The `preference_extractor` prompt has nowhere to put "not sedan" — no `excluded_body_types`, `disliked_models`, etc.
- The merge logic (`preference_extractor.py:79-96`) only **appends** to lists and **overwrites** scalars. It never removes values:

```python
for key, val in extracted.items():
    if val is None:
        continue          # null = skip (no change)
    if isinstance(val, list):
        existing = merged.get(key, [])
        for item in val:
            if item not in existing:
                existing.append(item)   # only APPENDS
        merged[key] = existing
    else:
        merged[key] = val               # overwrites
```

- Even if the LLM returned `{"preferred_body_types": []}` (empty list meaning "clear the sedan preference"), the merge doesn't have a "clear list" semantic — it would set to `[]` which is treated the same as "no filter" downstream.
- Since `retrieved_ads` is ephemeral (not persisted between turns), a scenario like "SUV" → "not Corolla" → "jeep" → "big family car" loses the rejection of sedan at every turn boundary.

### Impact

A rejected body type (sedan) can resurface on any subsequent search because the vector database has sedan-shaped embeddings that match whatever search query the LLM constructs. There is no accumulated negative signal to exclude them.
