# 18 — Troubleshooting Guide

[← Back to Index](index.md)

A catalog of common issues, their likely causes, and fixes. Symptoms reference actual code paths.

## Startup / import errors

### `KeyError` building the LLM model at startup
**Symptom:** App fails immediately with a `KeyError: 'MODEL'` (or similar) traced to a provider's `create_model`.
**Cause:** Provider `create_model` reads config with `config["KEY"]` (not `.get`). A missing key in the active provider block in `config.yml` raises `KeyError`.
**Fix:** Ensure the active `LLM.<provider>` block contains every key that provider reads (see [11](11-llm-providers.md) table).

### `ValueError: Unsupported LLM provider: <x>`
**Cause:** `LLM.Provider` doesn't match a key in `LLMFactory._providers`.
**Fix:** Use one of `ollama, vllm, aws_bedrock, groq, nvidia, google, huggingface, llamacpp, open_router`.

### `ValueError: LLM Provider not specified in configuration.`
**Cause:** `LLM.Provider` is empty/missing.
**Fix:** Set `LLM.Provider` in `config.yml`.

### `NameError: name 'effort' is not defined` (OpenRouter)
**Cause:** Bug in `open_router.py` — `effort` is only set when `MODEL_TYPE == "reasoning"`, but the `reasoning_config` referencing it is built unconditionally.
**Fix:** Set `open_router.MODEL_TYPE: "reasoning"`, or patch the provider to default `effort` (see [11](11-llm-providers.md)).

### `FileNotFoundError: src/config/logging.yaml` / `config.yml`
**Cause:** App must be launched from the **project root** — config paths are relative (`open("src/config/" + filename)`).
**Fix:** Run from the repo root (where `main.py` lives).

### Logging email handler errors at startup
**Cause:** `setup_logging` injects `SENDER_EMAIL`/`SENDER_PASSWORD`/`TEST_EMAIL` from env into the SMTP handler. Missing values can cause SMTP handler issues when a CRITICAL record fires.
**Fix:** Set those env vars, or temporarily remove the `email` handler from `logging.yaml` `root.handlers` in environments without mail.

## Runtime issues

### Getting an email on every chat request
**Cause:** `select_tool_node` calls `logger.critical("test error")`, and the `email` handler sends CRITICAL records via SMTP.
**Fix:** Remove that line in `src/pipelines/nodes.py`. (Also see [13](13-logging-and-error-handling.md).)

### `401 Invalid or expired token`
**Causes:** Token expired (default 6h), wrong/rotated `JWT_SECRET_KEY`, or malformed `Authorization` header.
**Fix:** Re-login; ensure the same `JWT_SECRET_KEY` across processes; send `Authorization: Bearer <token>`.

### `404 User not found` on a valid token
**Cause:** The user referenced by the token's `sub` was deleted (e.g. via `/auth/delete-user`).
**Fix:** Re-register / login as an existing user.

### `400 Service '<x>' not supported`
**Cause:** `service_name` not in `SUPPORTED_SERVICES`.
**Fix:** Use `chat`, `web_search`, `thinking`, `image_search`, or `news_search`.

### `400 Invalid conversation ID`
**Cause:** `conversation_id` is not a valid Mongo ObjectId (`ObjectId.is_valid` check).
**Fix:** Pass the exact `conversation_id` returned by a create/run call.

### Chat works but no history is used
**Cause:** Only the **last 5 turns** are loaded as context (`.sort("created_at", -1).limit(5)`), and only when `conversation_id` is supplied.
**Fix:** Pass `conversation_id` to continue a thread; expect a 5-turn context window by design.

### Web search returns a generic answer / no sources
**Causes:** `DDGS().text(...)` returned no results (rate-limited / network), so the node fell back to a plain LLM answer; or links exceeded the length filter (`len(l) <= 300`).
**Fix:** Retry; check outbound network; inspect `logs/warning.log` ("No web search results found") and `logs/error.log` ("Search node failed").

### Streaming: client never receives source links
**Cause:** Links are appended after streaming and sent as a reconciled trailing `content` frame; a client that stops reading at the first idle won't see it.
**Fix:** Read the stream until the `metadata` frame arrives.

### MongoDB connection errors / hangs
**Cause:** `MONGO_URL` unreachable; Motor connects lazily so failures appear on first query, not startup.
**Fix:** Verify MongoDB is running and `MONGO_URL`/`DB_NAME` are correct. In Docker, remember the app reads `MONGO_URL` from `config.yml`, not the compose `environment` (see [16](16-build-deployment.md)).

### Long LLM calls killed by the worker
**Cause:** Gunicorn worker `--timeout` (default 240s) exceeded.
**Fix:** Increase `FastAPI.TIMEOUT` in `config.yml`, or use the streaming endpoint to keep the connection active.

## Provider-specific

### Ollama: connection refused
**Cause:** Ollama server not running at `LLM.ollama.BASE_URL` (default `http://0.0.0.0:11434`).
**Fix:** Start Ollama and pull the configured model, or change `BASE_URL`/`MODEL`.

### llama.cpp: model file not found
**Cause:** `LLM.llamacpp.MODEL` path (default `artifacts/qwen2.5-1.5b-instruct-q4_k_m.gguf`) is missing.
**Fix:** Place the GGUF file at that path or update the config.

### Cloud providers: 401/403 from the API
**Cause:** Missing/incorrect API key, or the key env var doesn't match the lookup in `llm_client.py`.
**Fix:** Set the right env var; note OpenRouter uses `OPEN_ROUTER_API_KEY` (see the naming caveat in [10](10-configuration.md)).

## Tests

### `test_send_otp_email` fails
**Cause:** It performs a **real** SMTP send using `.env` creds and `TEST_EMAIL`.
**Fix:** Provide valid email env vars, or mock `smtplib.SMTP` (recommended — see [15](15-testing.md)).

### Tests can't import / DB calls hit real Mongo
**Cause:** Import order — `conftest.py` must mock `motor.motor_asyncio` before importing `main`.
**Fix:** Keep the mock setup at the top of `conftest.py` (as shipped); don't import app modules earlier.

## Diagnostics quick reference
| Where to look | For |
|---------------|-----|
| `logs/error.log` | exceptions, search failures, DB save errors |
| `logs/warning.log` | "no results" and degraded paths |
| `logs/info.log` | provider selection, mode start |
| console output | everything (DEBUG+) |
| Swagger `/docs` | reproduce requests with exact payloads |

---

Next: [19 — Performance Considerations →](19-performance.md)
