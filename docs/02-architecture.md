# 02 — High-Level Architecture

[← Back to Index](index.md)

## Architectural style

AIChatApp follows a **layered, modular monolith** architecture. Concerns are separated into clearly bounded modules under `src/`, and cross-cutting infrastructure (config, logging, DB client, auth dependencies) is centralized.

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP / SSE clients                         │
└───────────────────────────────┬───────────────────────────────────┘
                                 │
┌───────────────────────────────▼───────────────────────────────────┐
│  Presentation layer  (main.py)                                      │
│  • FastAPI app, CORS middleware, router registration, "/" redirect  │
└───────────┬───────────────────────────────────────┬────────────────┘
            │                                         │
┌───────────▼────────────┐               ┌────────────▼───────────────┐
│  API layer             │               │  API layer                  │
│  src/api_router/        │               │  src/api_router/            │
│   user_router.py (auth) │               │   chat_router.py (chat/CRUD)│
└───────────┬────────────┘               └────────────┬───────────────┘
            │                                          │
┌───────────▼──────────────────────────────────────────▼─────────────┐
│  Cross-cutting / Domain services                                     │
│  src/deps.py (auth deps, RBAC)   src/utils.py (jwt, bcrypt, otp,...) │
│  src/schemas.py (Pydantic DTOs)                                      │
└───────────┬───────────────────────────────────┬────────────────────┘
            │                                     │
┌───────────▼───────────┐          ┌──────────────▼────────────────────┐
│  AI orchestration      │          │  Persistence                       │
│  src/pipelines/        │          │  src/database.py (Motor client)    │
│   builder · nodes ·     │          │   users · chats · chat_messages    │
│   pipeline_state        │          └────────────────────────────────────┘
└───────────┬───────────┘
            │
┌───────────▼───────────────────────────────────────────────────────┐
│  Integration layer                                                  │
│  src/clients/llm_client.py  →  src/llms/ (Factory + 9 providers)    │
│  src/prompts/prompts.py     ·  ddgs (DuckDuckGo search)             │
└─────────────────────────────────────────────────────────────────────┘
```

## Layers explained

### 1. Presentation (`main.py`)
- Initializes logging **first** (`setup_logging()` before any other import that logs).
- Loads `config.yml`, constructs the `FastAPI(title="AIChatApp", version="1.0.0", lifespan=lifespan)` app.
- Adds permissive **CORS** middleware (`allow_origins=["*"]`).
- Registers the chat and user routers.
- Defines `GET /` → redirect to `/docs`.
- Provides `main_dev()` / `main_prod()` process launchers.

### 2. API layer (`src/api_router/`)
- `user_router.py` — prefix `/auth`, tag `Auth`. Authentication & account management.
- `chat_router.py` — prefix `/chat`, tag `Chat`. Conversation CRUD + pipeline execution (streaming and non-streaming).
- Each route declares its dependencies (e.g. `Depends(get_current_user)`) and Pydantic request/response models.

### 3. Cross-cutting / domain services
- `src/deps.py` — `get_current_user` (JWT validation) and `RoleChecker` (RBAC) FastAPI dependencies.
- `src/utils.py` — config loading, password hashing/verification (bcrypt), JWT creation, OTP generation, email sending, chat-title generation.
- `src/schemas.py` — Pydantic models that validate inbound requests and shape outbound responses.

### 4. AI orchestration (`src/pipelines/`)
- A **LangGraph `StateGraph`** that routes a request through nodes:
  `select_tool_node → {self_node | chat_node | search_node} → END`.
- `pipeline_state.py` defines the shared `PipelineState` TypedDict.

### 5. Persistence (`src/database.py`)
- A single module-level **Motor** `AsyncIOMotorClient` and three collection handles (`users`, `chats`, `chat_messages`).

### 6. Integration (`src/clients/`, `src/llms/`, `src/prompts/`)
- `llm_client.py` builds **one** `llm_model` singleton at import time via the factory.
- `src/llms/` contains the provider abstraction and concrete implementations.
- `src/prompts/prompts.py` holds reusable LangChain `PromptTemplate`s.
- DuckDuckGo (`ddgs`) provides external search inside `search_node`.

## Key architectural decisions (ADRs in brief)

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **Factory + ABC for LLMs** | Add providers without touching call sites; one config switch | Slight indirection; all providers must conform to `create_model` |
| **Singleton `llm_model` at import** | Model/clients built once, reused across requests | Provider/config changes require process restart; import-time failure if a key is missing |
| **LangGraph state machine** | Declarative routing; easy to add nodes/services; supports `astream_events` for streaming | Extra dependency; routing is currently regex-based, not LLM-based |
| **Dual MongoDB collections** | Decouples conversation metadata from potentially large message lists; cheap listing | Application must maintain referential integrity (no DB-level FKs) |
| **YAML-driven logging** | Ops can tune logging without code changes | Requires `logging.yaml` present and well-formed at startup |
| **bcrypt directly (not passlib)** | Avoids passlib/bcrypt version friction (see commented-out `CryptContext`) | Manual byte encoding in `utils.py` |
| **Stateless JWT** | Horizontal scalability; no server session store | Logout is a no-op server-side; tokens valid until expiry |

## Component interaction (runtime singletons)

These objects are created **once at import time** and shared:

- `cfg` — parsed `config.yml` (loaded in several modules via `load_config()`).
- `client` / `db` / `*_collection` — Motor client and collections (`src/database.py`).
- `llm_model` — the active LLM instance (`src/clients/llm_client.py`).
- `pipeline` — the compiled LangGraph (`src/pipelines/builder.py`).

Because these are import-time singletons, **the process must be restarted** to pick up changes to `config.yml`, `.env`, or the selected provider.

## Application lifecycle

`src/lifespan.py` defines an `asynccontextmanager` `lifespan`. Currently it is a **pass-through** (no startup/shutdown work) — a deliberate placeholder where DB connection warmup or graceful shutdown hooks would go. DB connections are lazy via Motor, so no explicit startup connect is required.

---

Next: [03 — System Design & Data Flow →](03-system-design-and-data-flow.md)
