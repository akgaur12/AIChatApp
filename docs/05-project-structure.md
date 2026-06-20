# 05 — Directory & File Structure

[← Back to Index](index.md)

## Top-level tree

```text
AIChatApp/
├── main.py                  # Application entry point (FastAPI app + dev/prod launchers)
├── pyproject.toml           # Project metadata, dependencies, Ruff config, `start` script
├── uv.lock                  # Resolved dependency lockfile (uv)
├── .python-version          # Pins Python 3.12
├── .env                     # Secrets (JWT, provider API keys, email) — not committed in real setups
├── .gitignore / .gitattributes
├── LICENSE                  # MIT
├── README.md                # Quick-start & overview
├── logs/                    # Rotating log files (created at runtime)
├── scripts/                 # Developer/maintenance utilities
├── tests/                   # pytest suite
├── artifacts/               # Generated docs, sample outputs, Docker assets, GGUF model
├── docs/                    # ← This documentation book
└── src/                     # Application source
```

## `src/` — application source

```text
src/
├── __init__.py
├── lifespan.py              # FastAPI lifespan context manager (currently pass-through)
├── database.py              # Motor client + collection handles (users, chats, chat_messages)
├── schemas.py               # Pydantic request/response models (DTOs)
├── deps.py                  # FastAPI dependencies: get_current_user, RoleChecker (RBAC)
├── utils.py                 # config loading, bcrypt, JWT, OTP, email, chat-title generation
├── logger.py                # setup_logging() + ExactLevelFilter
│
├── api_router/
│   ├── __init__.py          # (stub; logger only)
│   ├── user_router.py       # /auth routes — signup, login, reset, OTP, RBAC, delete
│   └── chat_router.py       # /chat routes — pipeline (stream/non-stream), conversation CRUD
│
├── clients/
│   ├── __init__.py
│   └── llm_client.py        # Builds the `llm_model` singleton via LLMFactory
│
├── llms/                    # Provider abstraction + implementations
│   ├── __init__.py          # Re-exports all providers, factory, parser
│   ├── base.py              # BaseLLMProvider (ABC) with create_model()
│   ├── llm_factory.py       # LLMFactory: name -> provider class
│   ├── llm_parser.py        # parse_response(): normalize provider outputs to AIMessage
│   ├── ollama.py            # ChatOllama
│   ├── vllm.py              # ChatOpenAI (OpenAI-compatible endpoint)
│   ├── aws_bedrock.py       # ChatBedrockConverse
│   ├── groq.py              # ChatGroq
│   ├── nvidia.py            # ChatNVIDIA
│   ├── google.py            # ChatGoogleGenerativeAI
│   ├── huggingface.py       # ChatHuggingFace + HuggingFaceEndpoint
│   ├── llamacpp.py          # ChatLlamaCpp (local GGUF)
│   └── open_router.py       # ChatOpenRouter
│
├── pipelines/               # LangGraph orchestration
│   ├── __init__.py
│   ├── pipeline_state.py    # PipelineState TypedDict (shared graph state)
│   ├── nodes.py             # select_tool_node, chat_node, search_node, self_node
│   └── builder.py           # Builds & compiles the StateGraph -> `pipeline`
│
├── prompts/
│   └── prompts.py           # PromptTemplates: web/image/news search, self/identity
│
└── config/
    ├── __init__.py
    ├── config.yml           # App config: FastAPI, MongoDB, Security, Email, Logging, Services, LLM
    └── logging.yaml         # dictConfig for logging (handlers, filters, formatters)
```

## File-by-file responsibilities

### Entry & lifecycle
| File | Responsibility |
|------|----------------|
| `main.py` | Initializes logging, loads config, builds the FastAPI app, adds CORS, includes routers, defines `/` redirect, and provides `main()/main_dev()/main_prod()` launchers (the `start` console script → `main:main`). |
| `src/lifespan.py` | Async context manager passed to `FastAPI(lifespan=...)`; placeholder for startup/shutdown hooks. |

### Core domain & infra
| File | Responsibility |
|------|----------------|
| `src/database.py` | Single Motor client; exposes `users_collection`, `conversations_collection`, `messages_collection`. |
| `src/schemas.py` | Pydantic DTOs (`UserCreate`, `UserLogin`, `Token`, conversation/message models, pipeline I/O). |
| `src/deps.py` | `get_current_user` (JWT decode + user lookup), `RoleChecker` (RBAC dependency factory). |
| `src/utils.py` | `load_config`, `hash_password`, `verify_password`, `create_access_token`, `generate_otp`, `send_otp_email`, `generate_chat_title`; loads `.env` and security/email settings. |
| `src/logger.py` | `setup_logging()` reads `logging.yaml`, injects SMTP creds from env, applies `dictConfig`; `ExactLevelFilter` for per-level files. |

### API
| File | Responsibility |
|------|----------------|
| `src/api_router/user_router.py` | Auth & account endpoints under `/auth`. |
| `src/api_router/chat_router.py` | Chat pipeline + conversation CRUD under `/chat`. |

### AI / integration
| File | Responsibility |
|------|----------------|
| `src/clients/llm_client.py` | Resolves provider from config and constructs the `llm_model` singleton. |
| `src/llms/*` | Provider abstraction, factory, parser, and 9 concrete providers. |
| `src/pipelines/*` | LangGraph state, nodes, and compiled `pipeline`. |
| `src/prompts/prompts.py` | Prompt templates for search and identity responses. |

## Supporting directories

### `scripts/` — developer utilities
| Script | Purpose |
|--------|---------|
| `lint_project.py` | Runs ruff/black/isort/mypy in sequence (extra tools required). |
| `clean_pycache.py` | Recursively removes `__pycache__` dirs and `.pyc` files. |
| `export_requirements.py` | Extracts deps from `pyproject.toml` → `artifacts/requirements.txt`. |
| `check_package_sizes.py` | Reports installed package sizes (uses `tqdm`). |
| `generate_project_tree.py` | Writes a directory tree to `artifacts/project_tree.txt`. |
| `generate_pipeline_graphs.py` | Renders the LangGraph to a Mermaid PNG (`artifacts/main_pipeline.png`). |
| `pipeline_summary.py` | Prints node/edge counts of the compiled pipeline. |
| `generate_arch_docs.py` | Generates `artifacts/ARCHITECTURE.md` from the tree + pipeline graphs. |

### `tests/` — see [15 — Testing](15-testing.md)
`conftest.py`, `test_main.py`, `test_utils.py`, `test_user_routes.py`, `test_chat_routes.py`.

### `artifacts/` — generated & sample assets
Contains generated docs (`ARCHITECTURE.md`, `project_tree.txt`), the pipeline diagram (`main_pipeline.png`), sample outputs, a local GGUF model (`qwen2.5-1.5b-instruct-q4_k_m.gguf`) used by the llama.cpp provider, and **deployment assets** (`Dockerfile`, `docker-compose.yml`) plus exploratory test scripts. These are not part of the import path.

### `logs/` — runtime output
Per-level rotating log files (`debug.log`, `info.log`, `warning.log`, `error.log`, plus legacy `aichatapp-*.log`). Created automatically by `setup_logging()`.

---

Next: [06 — Core Modules & Components →](06-core-modules.md)
