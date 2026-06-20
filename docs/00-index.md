# AIChatApp — Technical Documentation

> A production-oriented **AI chat backend** built with **FastAPI**, **LangGraph**, **MongoDB (Motor)** and a pluggable **multi-provider LLM layer**.

This documentation is a complete reference book for the AIChatApp codebase. It is written so that a developer with **no prior knowledge** of the project can become productive quickly, while remaining a long-term reference for experienced contributors.

All content here is derived from the **actual implementation** in this repository (not assumptions). Where the code and the top-level `README.md` disagree, this documentation describes what the code actually does and calls out the discrepancy.

---

## 📚 Table of Contents

| # | Document | What it covers |
|---|----------|----------------|
| 01 | [Project Overview & Objectives](01-overview.md) | What the app is, goals, key features, capabilities |
| 02 | [High-Level Architecture](02-architecture.md) | Layered architecture, component map, request lifecycle |
| 03 | [System Design & Data Flow](03-system-design-and-data-flow.md) | Sequence diagrams, chat/streaming/auth flows |
| 04 | [Technology Stack & Dependencies](04-tech-stack.md) | Frameworks, libraries, why each is used |
| 05 | [Directory & File Structure](05-project-structure.md) | Every directory and file explained |
| 06 | [Core Modules & Components](06-core-modules.md) | Deep dive into each `src/` module |
| 07 | [API Reference (Endpoints & Contracts)](07-api-reference.md) | Every route, request/response schema, status codes |
| 08 | [Database Schema & Models](08-database-schema.md) | Collections, document shapes, Pydantic models |
| 09 | [Authentication & Authorization](09-authentication.md) | JWT, OAuth2, RBAC, password reset/OTP |
| 10 | [Configuration & Environment Variables](10-configuration.md) | `config.yml`, `.env`, `logging.yaml` |
| 11 | [LLM Provider Layer & Integrations](11-llm-providers.md) | Factory pattern, all 9 providers, response parsing |
| 12 | [AI Pipeline (LangGraph)](12-pipeline.md) | Graph nodes, routing, web/image/news search |
| 13 | [Error Handling & Logging](13-logging-and-error-handling.md) | Logging config, level-split files, email alerts |
| 14 | [Security Considerations](14-security.md) | Threat surface, hardening recommendations |
| 15 | [Testing Strategy & Coverage](15-testing.md) | pytest suite, fixtures, mocking strategy |
| 16 | [Build, Deployment & CI/CD](16-build-deployment.md) | uv, Docker, Gunicorn/Uvicorn, run modes |
| 17 | [Development Workflow & Coding Standards](17-development-workflow.md) | Ruff, utility scripts, conventions |
| 18 | [Troubleshooting Guide](18-troubleshooting.md) | Common errors and fixes |
| 19 | [Performance Considerations](19-performance.md) | Async I/O, token tracking, optimizations |
| 20 | [Glossary](20-glossary.md) | Key terms and concepts |

---

## ⚡ Quick Start (TL;DR)

```bash
# 1. Install dependencies (uv recommended)
uv sync

# 2. Ensure MongoDB is running locally (mongodb://localhost:27017)

# 3. Configure secrets in .env (JWT_SECRET_KEY, provider API keys, email)
# 4. Pick an LLM provider in src/config/config.yml -> LLM.Provider

# 5a. Development (hot reload)
uv run start dev

# 5b. Production (Gunicorn + Uvicorn workers)
uv run start
```

The server binds to `HOST:PORT` from `config.yml` (default `0.0.0.0:45001`). Interactive API docs are served at `/docs` (Swagger UI) and `/redoc`.

---

## 🗺️ How to read this book

- **New to the project?** Read 01 → 02 → 05 → 06, then 07 and 12.
- **Integrating a frontend?** Read 07 (API), 09 (auth), and 03 (data flow / streaming).
- **Adding an LLM provider?** Read 11, then 12.
- **Operating / deploying?** Read 10, 13, 16, 18, 19.
- **Hardening for production?** Read 09 and 14.

---

*Last reviewed against commit history up to `feat: expand LLM support with open router`.*
