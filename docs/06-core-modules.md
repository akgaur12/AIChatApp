# 06 — Core Modules & Components

[← Back to Index](index.md)

This chapter is a code-level walkthrough of each core module in `src/`. Function signatures and behaviors are described exactly as implemented.

---

## `main.py` — application bootstrap

```python
setup_logging()                 # MUST run before modules that log at import time
cfg = load_config("config.yml")
app = FastAPI(title="AIChatApp", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(chat_router.router)
app.include_router(user_router.router)
```

- `GET /` → `RedirectResponse("/docs")`.
- `main_prod()` shells out to `gunicorn -w WORKERS -k uvicorn.workers.UvicornWorker --timeout … -b HOST:PORT main:app`.
- `main_dev()` shells out to `uvicorn main:app --host … --port … --reload --log-level …`.
- `main()` selects dev vs. prod based on `sys.argv[1] == "dev"`.

The console entry point `start = "main:main"` (`pyproject.toml`) makes `uv run start [dev]` work.

---

## `src/utils.py` — utilities & security primitives

| Function | Signature | Behavior |
|----------|-----------|----------|
| `load_config` | `(filename="config.yml") -> dict` | Reads `src/config/<filename>` with `yaml.safe_load`. |
| `hash_password` | `(password: str) -> str` | bcrypt: encodes UTF-8, generates salt, returns decoded hash. |
| `verify_password` | `(password, hashed) -> bool` | `bcrypt.checkpw` on encoded bytes. |
| `create_access_token` | `(data: dict, expires_delta=None) -> str` | Adds `exp` (default `ACCESS_TOKEN_EXPIRE_MINUTES`) and `iat`, encodes with `JWT_SECRET_KEY`/`ALGORITHM`. |
| `generate_otp` | `(length=6) -> str` | Random numeric string. |
| `send_otp_email` | `(to_email, otp) -> bool` | Sends via `smtplib` STARTTLS; returns success bool. |
| `generate_chat_title` | `async (user_query, llm_model, parse_response) -> str` | Prompts the LLM for a 3–5 word title, strips quotes, falls back to `user_query[:30]` on error. |

Module-level config resolution (env wins over `config.yml`):
```python
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or cfg["Security"]["JWT_SECRET_KEY"]
ALGORITHM = cfg["Security"]["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = cfg["Security"]["ACCESS_TOKEN_EXPIRE_MINUTES"]
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or cfg["Email"]["SENDER_EMAIL"]
```

> **Note:** `generate_chat_title` takes `llm_model` and `parse_response` as parameters via **dependency injection** specifically to avoid circular imports between `utils` and the LLM/pipeline modules.

---

## `src/database.py` — persistence handles

```python
client = AsyncIOMotorClient(MONGO_URL, tz_aware=True, tzinfo=UTC)
db = client[DB_NAME]
users_collection         = db[USER_COLLECTION]          # "users"
conversations_collection = db[CHAT_HISTORY_COLLECTION]  # "chats"
messages_collection      = db[MESSAGES_COLLECTION]      # "chat_messages"
```

- `tz_aware=True, tzinfo=UTC` ensures datetimes round-trip as UTC-aware.
- Connection is lazy (Motor connects on first operation); no explicit startup connect.

---

## `src/deps.py` — auth dependencies

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token = Depends(oauth2_scheme)):
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
    email = payload.get("sub")            # 401 if missing / JWTError
    user = await users_collection.find_one({"email": email})  # 404 if not found
    return user

class RoleChecker:
    def __init__(self, allowed_roles): ...
    def __call__(self, current_user = Depends(get_current_user)):
        # 403 unless any(role in allowed_roles for role in current_user["role"])
        return current_user
```

- `get_current_user` is a **static** dependency (always validates token → loads user).
- `RoleChecker` is a **parameterized** dependency (class instance used as `Depends(RoleChecker(["ROLE_ADMIN"]))`).

---

## `src/schemas.py` — Pydantic DTOs

Request/auth models: `UserCreate`, `UserLogin`, `Token`, `ResetPasswordRequest`, `UpdateUserNameRequest`, `ForgotPasswordRequest`, `ResetPasswordWithOTP`.

Conversation/message models: `Message`, `ConversationBase` (+ `ConversationCreate`/`ConversationUpdate`), `Conversation`.

Pipeline I/O: `UserInput` (`service_name="chat"`, `user_query`, optional `conversation_id`), `UserQueryResponse` (`conversation_id`, `message`).

Notable validation:
- `UserCreate.password` min length 6; `role` defaults to `["ROLE_USER"]`.
- `ConversationBase.title` 1–60 chars, with a `field_validator` that replaces `None` with `"New Chat"`.

Full details in [08 — Database Schema & Models](08-database-schema.md).

---

## `src/api_router/` — route handlers

### `user_router.py` (`/auth`)
`signup`, `login` (OAuth2 form), `login_json`, `logout`, `reset_password`, `update_user_name`, `delete_user` (cascade), `forget_password` (OTP), `verify_otp_reset_password`, `admin_only_route` (RBAC). See [07](07-api-reference.md) and [09](09-authentication.md).

### `chat_router.py` (`/chat`)
- Helpers: `get_current_timestamp()` (UTC ISO string), `serialize_conversation()` (Mongo doc → `Conversation`).
- `execute_user_query` (`POST /run_pipeline`) — non-streaming.
- `execute_user_query_streaming` (`POST /run_pipeline/stream`) — SSE.
- Conversation CRUD: create, list, get-by-id, update, delete, delete-all, rename.

---

## `src/clients/llm_client.py` — model singleton

```python
def get_llm_model():
    inference_type = cfg["LLM"]["Provider"].lower()
    provider = LLMFactory.get_provider(inference_type)
    kwargs = {"aws_key": ..., "aws_secret": ..., "api_key": <first matching env key>}
    return provider.create_model(cfg["LLM"][inference_type], **kwargs)

llm_model = get_llm_model()   # built once at import
```

The `api_key` falls back through several env vars (`<PROVIDER>_API_KEY`, then HuggingFace/NVIDIA/Google/Groq/OpenRouter). See [11](11-llm-providers.md) for the caveat about this fallback.

---

## `src/pipelines/` — orchestration

- `pipeline_state.py` — `PipelineState` TypedDict: `service_name`, `user_input`, `llm_messages`, `llm_response`, `input_tokens`, `output_tokens`, `response_time`.
- `nodes.py` — the four async node functions and the two routing regexes.
- `builder.py` — wires nodes into a `StateGraph` and compiles `pipeline`.

Deep dive in [12 — AI Pipeline](12-pipeline.md).

---

## `src/prompts/prompts.py` — prompt templates

LangChain `PromptTemplate`s: `WEB_SEARCH_PROMPT`, `IMAGE_SEARCH_PROMPT`, `NEWS_SEARCH_PROMPT`, and `SELF_PROMPT` (identity — the assistant introduces itself as **SannaAI**, created by Akash Gaur).

---

## `src/logger.py` — logging setup

- `ExactLevelFilter(level)` — passes only records whose `levelno` equals `level` (used to split DEBUG/INFO/WARNING/CRITICAL into separate files).
- `setup_logging(config_path="src/config/logging.yaml")` — ensures `logs/` exists, loads the YAML, **injects SMTP credentials from env** into the email handler, and applies `logging.config.dictConfig`. See [13](13-logging-and-error-handling.md).

---

Next: [07 — API Reference →](07-api-reference.md)
