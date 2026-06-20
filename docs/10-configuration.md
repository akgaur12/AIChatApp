# 10 — Configuration & Environment Variables

[← Back to Index](index.md)

Configuration comes from three sources, layered:

1. **`src/config/config.yml`** — non-secret application settings (server, DB, security policy, LLM choice/params, services).
2. **`.env`** (loaded by `python-dotenv`) — secrets (API keys, JWT secret, email credentials).
3. **`src/config/logging.yaml`** — logging `dictConfig`.

**Precedence:** for sensitive values, the code prefers environment variables and falls back to `config.yml`, e.g.:
```python
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or cfg["Security"]["JWT_SECRET_KEY"]
SENDER_EMAIL   = os.getenv("SENDER_EMAIL")   or cfg["Email"]["SENDER_EMAIL"]
```

Config is read at **import time** (`load_config()` in `src/utils.py`), so changes require a process restart.

---

## `config.yml` reference

### `FastAPI` — server/runtime
| Key | Default | Used by |
|-----|---------|---------|
| `HOST` | `0.0.0.0` | `main.py` bind address |
| `PORT` | `45001` | bind port (string) |
| `WORKERS` | `2` | Gunicorn `-w` |
| `LOG_LEVEL` | `info` | Uvicorn `--log-level` (dev) |
| `TIMEOUT` | `240` | Gunicorn `--timeout` (long LLM calls) |
| `GRACEFUL_TIMEOUT` | `60` | Gunicorn `--graceful-timeout` |

### `MongoDB`
| Key | Default |
|-----|---------|
| `MONGO_URL` | `mongodb://localhost:27017` |
| `DB_NAME` | `ai_chat_app` |
| `USER_COLLECTION` | `users` |
| `CHAT_HISTORY_COLLECTION` | `chats` |
| `MESSAGES_COLLECTION` | `chat_messages` |

### `Security`
| Key | Default | Notes |
|-----|---------|-------|
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `360` | 6 hours |
| `JWT_SECRET_KEY` | *(env only)* | **Not present in committed `config.yml`** → must come from `.env` |

### `Email`
| Key | Default |
|-----|---------|
| `SMTP_SERVER` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SENDER_EMAIL` / `SENDER_PASSWORD` | from `.env` |

### `Logging`
Holds log dir, level, filenames, rotation sizes (`MAX_FILE_SIZE: 5 MB`, `MAX_FILE_COUNT: 10`), a format string, and a `NOISY_LOGGERS` list. *(Note: the active logging behavior is driven by `logging.yaml`, not this block — see [13](13-logging-and-error-handling.md).)*

### `Services`
| Key | Value |
|-----|-------|
| `SUPPORTED_SERVICES` | `["chat","web_search","thinking","image_search","news_search"]` |
| `SUPPORTED_MODEL_TYPE` | `["instruct","chat","reasoning"]` |
| `SUPPORTED_LLM_PROVIDER` | `["ollama","vllm","aws_bedrock","groq","nvidia","openai","llamacpp","google","huggingface","open_router"]` |

`SUPPORTED_SERVICES` gates the `service_name` accepted by `/chat/run_pipeline*`.

### `LLM`
- `Provider` — the **active** provider key (e.g. `ollama`, `groq`, `open_router`).
- One sub-block per provider with model id and parameters.

```yaml
LLM:
  Provider: "ollama"
  ollama:
    BASE_URL: "http://0.0.0.0:11434"
    MODEL: "gpt-oss:20b-cloud"
    MAX_TOKENS: 4096
    TEMPERATURE: 0.5
    REASONING_EFFORT: "low"
    MODEL_TYPE: "instruct"     # reasoning -> enables reasoning_effort
  groq:
    MODEL: "openai/gpt-oss-20b"
    TEMPERATURE: 0.5
    REASONING_EFFORT: "low"
    MODEL_TYPE: "instruct"
  open_router:
    BASE_URL: "https://openrouter.ai/api/v1"
    MODEL: "openai/gpt-oss-20b:free"
    MAX_TOKENS: 4096
    TEMPERATURE: 0.1
    MAX_RETRIES: 2
    MODEL_TYPE: "reasoning"
  # ... vllm, aws_bedrock, nvidia, google, huggingface, llamacpp
```

Common per-provider keys: `MODEL`, `TEMPERATURE`, `MAX_TOKENS`, `REASONING_EFFORT`, `MODEL_TYPE`. The exact keys consumed vary by provider — see [11 — LLM Providers](11-llm-providers.md). `MODEL_TYPE == "reasoning"` activates `reasoning_effort` where the provider supports it.

> ⚠️ Each provider's `create_model` reads its config keys with `config[...]` (not `.get`), so **missing keys raise `KeyError`**. Keep each provider block complete.

---

## `.env` reference

```env
# Auth
JWT_SECRET_KEY = "your-32-character-secret-key"

# AWS Bedrock
AWS_ACCESS_KEY_ID = "..."
AWS_SECRET_ACCESS_KEY = "..."

# Provider API keys
GROQ_API_KEY = "..."
NVIDIA_API_KEY = "..."
GOOGLE_API_KEY = "..."
HUGGINGFACEHUB_API_TOKEN = "..."
OPEN_ROUTER_API_KEY = "..."

# Email (Gmail app password)
SENDER_EMAIL = "you@gmail.com"
SENDER_PASSWORD = "16-char-app-password"
TEST_EMAIL = "recipient@example.com"   # used by logging email handler + test_send_otp_email
```

### How API keys are resolved (`llm_client.py`)
```python
"api_key": os.getenv(f"{inference_type.upper()}_API_KEY")
           or os.getenv("HUGGINGFACEHUB_API_TOKEN")
           or os.getenv("NVIDIA_API_KEY")
           or os.getenv("GOOGLE_API_KEY")
           or os.getenv("GROQ_API_KEY")
           or os.getenv("OPENROUTER_API_KEY")
```

> ⚠️ **Two naming mismatches to be aware of:**
> 1. For OpenRouter, the `.env` uses `OPEN_ROUTER_API_KEY` but `llm_client.py` first tries `OPEN_ROUTER_API_KEY` (`{provider}_API_KEY` where provider=`open_router`) — that matches. However the fallback list checks `OPENROUTER_API_KEY` (no underscore). Prefer `OPEN_ROUTER_API_KEY` to match the primary lookup.
> 2. The `{PROVIDER}_API_KEY` pattern yields e.g. `OLLAMA_API_KEY`, `VLLM_API_KEY` which don't exist for keyless local providers — that's fine because those providers ignore `api_key`.

### Variables consumed where
| Variable | Read in |
|----------|---------|
| `JWT_SECRET_KEY` | `src/utils.py` |
| `SENDER_EMAIL`, `SENDER_PASSWORD` | `src/utils.py` (OTP email), `src/logger.py` (email handler) |
| `TEST_EMAIL` | `src/logger.py` (alert recipient), `tests/test_utils.py` |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | `src/clients/llm_client.py` → bedrock |
| `*_API_KEY` / `HUGGINGFACEHUB_API_TOKEN` | `src/clients/llm_client.py` |

---

## `logging.yaml`
Covered in detail in [13 — Error Handling & Logging](13-logging-and-error-handling.md). Key points: `version: 1`, per-level rotating file handlers with `ExactLevelFilter`, a console handler, and an SMTP handler for `CRITICAL` records (credentials injected at runtime from env).

---

## Switching providers — quick recipe
1. Put the provider's key in `.env` (e.g. `GROQ_API_KEY`).
2. Set `LLM.Provider: "groq"` in `config.yml`.
3. Ensure the `groq:` block has `MODEL`, `TEMPERATURE`, `REASONING_EFFORT`, `MODEL_TYPE`.
4. Restart the server.

---

Next: [11 — LLM Provider Layer & Integrations →](11-llm-providers.md)
