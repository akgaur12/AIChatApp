# 01 — Project Overview & Objectives

[← Back to Index](index.md)

## What is AIChatApp?

**AIChatApp** is the backend service for an AI chat product. It exposes a REST/JSON (and Server-Sent-Events streaming) API that lets authenticated users:

- Hold multi-turn conversations with a Large Language Model (LLM).
- Get answers augmented with **live web, image, and news search** (via DuckDuckGo).
- Persist conversations and individual message turns in **MongoDB**.
- Manage their account (signup, login, password reset via OTP, account deletion).

The application is **provider-agnostic**: the same chat logic runs against Ollama, vLLM, AWS Bedrock, Groq, NVIDIA, Google Gemini, Hugging Face, llama.cpp, or OpenRouter — selected purely through configuration.

## Objectives & design goals

| Goal | How it is achieved in the code |
|------|--------------------------------|
| **Provider flexibility** | A `LLMFactory` + `BaseLLMProvider` abstraction (`src/llms/`) selects the concrete provider at startup from `config.yml`. |
| **Asynchronous, high-concurrency I/O** | FastAPI + `async`/`await` everywhere; MongoDB accessed via the async **Motor** driver. |
| **Composable AI logic** | A **LangGraph** state machine (`src/pipelines/`) routes a query to the right "service" (chat / web_search / image_search / news_search / self). |
| **Stateful conversations** | Dual-collection MongoDB design: `chats` (conversation metadata) + `chat_messages` (turns). |
| **Secure access** | JWT bearer auth (OAuth2 password flow), bcrypt password hashing, role-based access control (RBAC). |
| **Observability** | YAML-driven logging with per-level rotating files and CRITICAL-level email alerts; per-turn token + latency tracking. |
| **Operational flexibility** | One entry point (`main.py`) drives both dev (Uvicorn `--reload`) and prod (Gunicorn-managed Uvicorn workers). |

## Key features

- 🤖 **Multi-turn chat** with conversation history (last 5 turns loaded as LLM context).
- 🔍 **Tool routing** — a regex-based router decides whether a query needs web search or an identity ("self") response.
- 🌐 **Web / Image / News search** grounding via the `ddgs` (DuckDuckGo) library.
- 📡 **Streaming responses** over Server-Sent Events (`/chat/run_pipeline/stream`).
- 🧠 **9 LLM providers** behind a single interface.
- 🔐 **Full auth suite**: signup, OAuth2 login, JSON login, logout, password reset, forgot-password OTP via email, RBAC admin route, account deletion (with cascade).
- 💬 **Auto-generated chat titles** from the first user query.
- 📊 **Per-turn metrics**: input tokens, output tokens, response time.

## High-level capabilities map

```
            ┌──────────────────────────────────────────────┐
            │                  AIChatApp                     │
            ├───────────────┬───────────────┬───────────────┤
            │   Auth/User   │     Chat      │   AI Pipeline  │
            │   (RBAC,JWT)  │  (CRUD+stream)│  (LangGraph)   │
            └───────┬───────┴───────┬───────┴───────┬────────┘
                    │               │               │
              ┌─────▼─────┐   ┌─────▼─────┐   ┌──────▼───────┐
              │  MongoDB  │   │  MongoDB  │   │  LLM Factory │
              │  users    │   │chats/msgs │   │ (9 providers)│
              └───────────┘   └───────────┘   └──────┬───────┘
                                                      │
                                              ┌───────▼────────┐
                                              │ DuckDuckGo (ddgs)│
                                              │  web/img/news    │
                                              └──────────────────┘
```

## Intended audience

- **Backend developers** maintaining or extending the API and pipeline.
- **Frontend / mobile developers** consuming the API.
- **ML / LLM engineers** adding providers or tuning prompts.
- **DevOps / operators** deploying and monitoring the service.

## Project metadata

| Field | Value |
|-------|-------|
| Package name | `aichatapp` (`pyproject.toml`) |
| Version | `0.1.0` |
| Python | `>=3.12` |
| License | MIT |
| Author | Akash Gaur |
| FastAPI app title/version | `AIChatApp` / `1.0.0` (`main.py`) |

> ℹ️ **Doc vs. code note:** The `README.md` references docs at `http://localhost:8000/docs`, but the default port in `src/config/config.yml` is **45001**. Use the port from your active config.

---

Next: [02 — High-Level Architecture →](02-architecture.md)
