# 04 — Technology Stack & Dependencies

[← Back to Index](index.md)

## Overview

| Concern | Technology |
|---------|------------|
| Language | Python `>=3.12` |
| Web framework | FastAPI |
| ASGI server (dev) | Uvicorn (`--reload`) |
| Process manager (prod) | Gunicorn + `uvicorn.workers.UvicornWorker` |
| Database | MongoDB via **Motor** (async driver) |
| AI orchestration | LangChain + LangGraph |
| Search | `ddgs` (DuckDuckGo search) |
| Auth | `python-jose` (JWT), `bcrypt` (hashing), `python-multipart` (OAuth2 form) |
| Validation | Pydantic v2 (`pydantic[email]`) |
| Config | PyYAML + `python-dotenv` |
| Dependency/Project manager | **uv** (with `uv.lock`) |
| Build backend | Hatchling |
| Linter/formatter | Ruff |
| Testing | pytest + pytest-asyncio |

## Full dependency list (`pyproject.toml`)

### Runtime dependencies
```toml
dependencies = [
    "ddgs>=9.10.0",                         # DuckDuckGo web/image/news search
    "dotenv>=0.9.9",                        # load .env
    "fastapi>=0.127.0",                     # web framework
    "gunicorn>=23.0.0",                     # production process manager
    "httpx>=0.28.1",                        # async HTTP (used by providers/tests)
    "langchain>=1.2.0",                     # LLM framework core
    "langchain-aws>=1.1.1",                 # AWS Bedrock chat models
    "langchain-community>=0.4.1",           # ChatLlamaCpp and community integrations
    "langchain-experimental>=0.4.1",
    "langchain-google-genai>=3.2.0",        # Google Gemini
    "langchain-groq>=1.1.1",                # Groq
    "langchain-huggingface>=1.2.0",         # HuggingFace endpoints
    "langchain-nvidia-ai-endpoints>=1.0.1", # NVIDIA
    "langchain-ollama>=1.0.1",              # Ollama
    "langchain-openai>=1.1.6",              # OpenAI-compatible (used by vLLM)
    "langgraph>=1.0.5",                     # stateful graph orchestration
    "llama-cpp-python>=0.3.16",             # local GGUF inference
    "motor>=3.7.1",                         # async MongoDB driver
    "openai>=2.14.0",                       # OpenAI SDK
    "bcrypt>=4.2.0",                        # password hashing
    "pydantic[email]>=2.12.5",              # schemas + EmailStr
    "pyppeteer>=2.0.0",                     # headless browser (available; not core path)
    "pytest>=9.0.2",                        # test runner
    "python-jose>=3.5.0",                   # JWT encode/decode
    "python-multipart>=0.0.21",             # form parsing for OAuth2 login
    "pyyaml>=6.0.3",                        # YAML config + logging config
    "uvicorn>=0.40.0",                      # ASGI server
    "pytest-asyncio>=1.3.0",                # async test support
    "langchain-openrouter>=0.2.1",          # OpenRouter provider
]
```

### Dev dependencies
```toml
[dependency-groups]
dev = ["ruff>=0.15.0"]
```

> Note: the linter helper script `scripts/lint_project.py` references `black`, `isort`, and `mypy`, and `scripts/check_package_sizes.py` imports `tqdm`. These are **not** declared in `pyproject.toml`; install them separately if you intend to run those scripts.

## Why each major dependency

- **FastAPI** — async-native, automatic OpenAPI/Swagger, Pydantic-based validation, first-class dependency injection (used heavily for auth).
- **LangChain + LangGraph** — LangChain normalizes chat models across providers (`ainvoke`, `astream_events`, `AIMessage`/`HumanMessage`); LangGraph adds a typed state machine for routing and supports event streaming (`astream_events(version="v2")`) that powers SSE.
- **Motor** — non-blocking MongoDB access so DB calls don't stall the event loop.
- **ddgs** — keyless web/image/news search to ground answers in fresh content.
- **python-jose + bcrypt** — JWT issuance/verification and secure password hashing.
- **uv** — fast, reproducible dependency resolution (`uv.lock`) and the `start` script entry point.
- **Ruff** — single fast tool for linting + formatting (replaces flake8/isort/black for the configured rules).

## LangChain provider packages → providers

| Provider (`config.yml` key) | LangChain class | Package |
|------------------------------|-----------------|---------|
| `ollama` | `ChatOllama` | `langchain-ollama` |
| `vllm` | `ChatOpenAI` | `langchain-openai` |
| `aws_bedrock` | `ChatBedrockConverse` | `langchain-aws` |
| `groq` | `ChatGroq` | `langchain-groq` |
| `nvidia` | `ChatNVIDIA` | `langchain-nvidia-ai-endpoints` |
| `google` | `ChatGoogleGenerativeAI` | `langchain-google-genai` |
| `huggingface` | `ChatHuggingFace` + `HuggingFaceEndpoint` | `langchain-huggingface` |
| `llamacpp` | `ChatLlamaCpp` | `langchain-community` (+ `llama-cpp-python`) |
| `open_router` | `ChatOpenRouter` | `langchain-openrouter` |

See [11 — LLM Provider Layer](11-llm-providers.md) for details.

## Python version & lockfile

- `.python-version` pins `3.12`.
- `requires-python = ">=3.12"` (uses 3.12 features such as `datetime.UTC`, `X | None` unions, and `tomllib`).
- `uv.lock` (~495 KB) records the fully resolved dependency graph for reproducible installs.

---

Next: [05 — Directory & File Structure →](05-project-structure.md)
