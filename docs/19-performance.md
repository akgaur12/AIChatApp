# 19 — Performance Considerations & Optimizations

[← Back to Index](index.md)

## What the architecture already does well

### Fully async I/O
Every I/O path is non-blocking:
- Routes are `async def`.
- DB access uses **Motor** (`AsyncIOMotorClient`) — `await collection.find_one(...)`, `async for ... in cursor`.
- LLM calls use `await llm_model.ainvoke(...)` and `pipeline.ainvoke(...)` / `astream_events(...)`.

This keeps the event loop free during the dominant cost (LLM latency), allowing high concurrency per worker.

### Singletons built once
`cfg`, the Motor `client`/collections, `llm_model`, and the compiled `pipeline` are constructed **at import time** and reused across requests — no per-request model construction or config re-parsing.

### Bounded context window
Conversation history loads only the **last 5 turns**:
```python
messages_collection.find({"chat_id": conversation_id}).sort("created_at", -1).limit(5)
```
This caps prompt size (and token cost/latency) regardless of how long a conversation grows.

### Streaming for perceived latency
`/chat/run_pipeline/stream` emits tokens as they're generated via `astream_events(version="v2")`, so users see output immediately instead of waiting for the full completion.

### Atomic counter updates
Conversation `message_count` is incremented with a single `find_one_and_update($inc)` call that also returns the updated document — one round trip, no read-modify-write race.

### Per-turn metrics captured
`input_tokens`, `output_tokens`, and `response_time` are recorded per turn (via `time.perf_counter()` in nodes and `usage_metadata` parsing), enabling cost/latency analysis from the `chat_messages` collection.

### Production process model
Gunicorn manages multiple Uvicorn workers (`WORKERS=2`) with a generous `TIMEOUT=240s` tuned for slow LLM calls and `GRACEFUL_TIMEOUT=60s` for clean restarts.

### Rotating logs
`RotatingFileHandler` (10 MB × 5 backups per level) bounds disk usage; noisy third-party loggers are pinned to WARNING/ERROR to reduce log volume.

## Bottlenecks & optimization opportunities

### 🔴 Missing MongoDB indexes
The hottest queries have no supporting indexes:
| Query | Frequency | Recommended index |
|-------|-----------|-------------------|
| `users.find_one({email})` | every authenticated request | unique `{email: 1}` |
| `chats.find({user_id}).sort(updated_at, -1)` | conversation list | `{user_id: 1, updated_at: -1}` |
| `chat_messages.find({chat_id}).sort(created_at, ±1)` | history load + thread view | `{chat_id: 1, created_at: 1}` |

Without these, queries become collection scans as data grows. Add indexes (e.g. in the `lifespan` startup hook).

### 🟠 Auth does a DB lookup per request
`get_current_user` runs `users.find_one({email})` on **every** protected call. With the email index this is cheap; consider a short-TTL cache only if profiling shows it matters.

### 🟠 `created_at` stored as ISO strings
Timestamps are stored as ISO-8601 **strings**, so `.sort("created_at", ...)` is a lexicographic sort. It works because ISO-8601 sorts lexicographically == chronologically, but native BSON dates would be more compact and index-friendly. The `seq` field provides a reliable secondary ordering key.

### 🟠 Synchronous title generation on first turn
For a new conversation, `generate_chat_title` makes an **extra blocking LLM call** before responding. This adds latency to the first turn. Consider generating the title in a background task (`asyncio.create_task` / FastAPI `BackgroundTasks`) and patching it in asynchronously.

### 🟠 Search adds an extra LLM round trip
`search_node` does: external search → build prompt → LLM call. Two network hops (DDGS + LLM). The result links are length-filtered (`<= 300`/`<= 200` chars) and capped (5/4 results) to keep prompts lean.

### 🟢 Per-request CRITICAL email
The `logger.critical("test error")` in `select_tool_node` sends an email per request — a severe latency and quota problem in addition to being noise. Remove it (also flagged in [13](13-logging-and-error-handling.md)/[18](18-troubleshooting.md)).

### 🟢 Worker count tuning
`WORKERS=2` is a static default. For CPU-bound local inference (llama.cpp) vs. I/O-bound cloud APIs the ideal count differs. For cloud-API providers, you can run more workers (I/O-bound); for local GPU inference, keep workers low to avoid GPU contention.

## Scaling guidance
- **Stateless app + JWT** ⇒ horizontally scalable: run N instances behind a load balancer; all state lives in MongoDB.
- **MongoDB** is the shared bottleneck — index it, and scale it (replica set / sharding) independently.
- **LLM provider** is the latency floor — choose provider/model per latency/cost target; the factory makes switching a config change.
- For high streaming concurrency, ensure the reverse proxy doesn't buffer SSE (the handler leaves a commented `X-Accel-Buffering: no` header for nginx — enable it if fronting with nginx).

## Quick wins (priority order)
1. Remove the per-request CRITICAL log line.
2. Add the three MongoDB indexes (+ unique email index).
3. Move first-turn title generation to a background task.
4. Tune `WORKERS`/`TIMEOUT` to the chosen provider.
5. Enable SSE-friendly proxy settings in production.

---

Next: [20 — Glossary →](20-glossary.md)
