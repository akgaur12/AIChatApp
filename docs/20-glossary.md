# 20 — Glossary

[← Back to Index](index.md)

Key terms, acronyms, and project-specific concepts used throughout this codebase and documentation.

| Term | Definition |
|------|------------|
| **AIChatApp** | This project — a FastAPI backend for AI chat with web/image/news search and multi-provider LLM support. |
| **ASGI** | Asynchronous Server Gateway Interface. The async successor to WSGI; FastAPI is an ASGI app served by Uvicorn. |
| **bcrypt** | Adaptive password-hashing function used (directly) to hash and verify user passwords. |
| **BaseLLMProvider** | Abstract base class (`src/llms/base.py`) defining the `create_model(config, **kwargs)` contract all providers implement. |
| **Bedrock (AWS)** | AWS's managed LLM service, integrated via `ChatBedrockConverse`. |
| **CORS** | Cross-Origin Resource Sharing. Configured permissively (`allow_origins=["*"]`) in `main.py`. |
| **conversation / chat** | A thread of messages. Metadata stored in the `chats` collection; identified by `conversation_id` (a Mongo ObjectId string). |
| **ddgs** | The DuckDuckGo search library used for keyless web/image/news search in `search_node`. |
| **dictConfig** | `logging.config.dictConfig` — applies the dictionary (from `logging.yaml`) that configures Python logging. |
| **DTO** | Data Transfer Object — here, the Pydantic models in `src/schemas.py` that validate requests and shape responses. |
| **ExactLevelFilter** | Custom logging filter (`src/logger.py`) that passes only records of one exact level, enabling per-level log files. |
| **Factory (LLMFactory)** | Class that maps a provider name to its provider class (`src/llms/llm_factory.py`). |
| **Gunicorn** | Production process manager that runs multiple Uvicorn workers. |
| **HS256** | HMAC-SHA256, the symmetric JWT signing algorithm used (`ALGORITHM`). |
| **httpx** | Async HTTP client library (used by LangChain providers and available to tests). |
| **JWT** | JSON Web Token. Stateless bearer token carrying `sub` (email), `name`, `iat`, `exp`. |
| **LangChain** | Framework normalizing chat models across providers (`ainvoke`, `astream_events`, `AIMessage`/`HumanMessage`). |
| **LangGraph** | Graph/state-machine library built on LangChain; powers the routing pipeline (`StateGraph`). |
| **lifespan** | FastAPI startup/shutdown context manager (`src/lifespan.py`); currently a pass-through placeholder. |
| **llm_model** | The singleton LLM instance built at import (`src/clients/llm_client.py`) from the configured provider. |
| **Motor** | Async MongoDB driver (`AsyncIOMotorClient`) used for all DB access. |
| **node** | A function in the LangGraph pipeline (`select_tool_node`, `chat_node`, `search_node`, `self_node`). |
| **OAuth2PasswordBearer / OAuth2PasswordRequestForm** | FastAPI security utilities; the form flow powers `/auth/login` and Swagger's Authorize button. |
| **Ollama** | Local/cloud LLM server; the default provider (`ChatOllama`). |
| **OpenRouter** | Aggregator giving access to many models via one API (`ChatOpenRouter`). |
| **OTP** | One-Time Password — 6-digit code emailed for password reset; valid 5 minutes. |
| **parse_response** | Function (`src/llms/llm_parser.py`) normalizing provider outputs into a uniform `AIMessage`. |
| **pipeline** | The compiled LangGraph (`src/pipelines/builder.py`) that routes and answers a query. |
| **PipelineState** | TypedDict (`src/pipelines/pipeline_state.py`) holding the shared state passed between graph nodes. |
| **Pydantic** | Data-validation library (v2); defines request/response models. |
| **RBAC** | Role-Based Access Control — enforced by `RoleChecker`; roles `ROLE_USER`, `ROLE_ADMIN`. |
| **reasoning_effort** | Provider parameter (e.g. `low`) enabled only when `MODEL_TYPE == "reasoning"`. |
| **RoleChecker** | Parameterized FastAPI dependency (`src/deps.py`) enforcing required roles. |
| **SannaAI** | The assistant's self-identity persona (defined in `SELF_PROMPT`), "developed by Akash Gaur". |
| **seq** | Sequence number of a message turn within a conversation (`chat_messages.seq`). |
| **service_name** | The chosen mode for a query: `chat`, `web_search`, `thinking`, `image_search`, `news_search`, or `self`. |
| **SSE (Server-Sent Events)** | One-way streaming over HTTP (`text/event-stream`); used by `/chat/run_pipeline/stream` with `data: {json}` frames. |
| **StateGraph** | LangGraph construct that defines nodes and (conditional) edges; compiled into `pipeline`. |
| **turn** | One user→assistant exchange, stored as a single `chat_messages` document. |
| **uv** | Fast Python package/project manager (`uv.lock`, `uv run start`). |
| **Uvicorn** | ASGI server; runs the app directly in dev and as Gunicorn workers in prod. |
| **vLLM** | High-throughput inference server exposing an OpenAI-compatible API (used via `ChatOpenAI`). |

## Service routing keywords

| Pattern | Triggers service | Examples |
|---------|------------------|----------|
| `SELF_PATTERN` | `self` | "who are you", "what is your name", "tell me about you" |
| `SEARCH_PATTERN` | `web_search` | "current", "today", "latest", "news", "weather", "price", "stock", "score", "live", "who is" |

## Status code cheat sheet
| Code | Meaning in this app |
|------|---------------------|
| 200 | Success (read/update/delete/login) |
| 201 | Created (signup, conversation, pipeline turn) |
| 400 | Client validation error |
| 401 | Auth failure / bad token |
| 403 | Missing role (RBAC) |
| 404 | Not found |
| 422 | Pydantic body validation |
| 500 | Server error (e.g. email send) |

---

[← Back to Index](index.md)
