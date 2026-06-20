# 16 — Build, Deployment & CI/CD

[← Back to Index](index.md)

## Build system

- **Build backend:** Hatchling (`[build-system]` in `pyproject.toml`).
- **Wheel packaging:** `packages = ["src"]` — only `src/` is bundled.
- **Dependency manager:** `uv` with a committed `uv.lock` for reproducible installs.
- **Console script:** `start = "main:main"` → `uv run start [dev]`.

### Install
```bash
# With uv (recommended — uses uv.lock)
uv sync

# Or pip + pyproject
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Run modes (`main.py`)

A single entry point switches between development and production based on `sys.argv`.

### Development
```bash
python main.py dev        # or: uv run start dev
```
Runs:
```
uvicorn main:app --host <HOST> --port <PORT> --reload --log-level <LOG_LEVEL>
```
Hot reload on code changes; single process.

### Production
```bash
python main.py            # or: uv run start
```
Runs:
```
gunicorn -w <WORKERS> -k uvicorn.workers.UvicornWorker \
         --timeout <TIMEOUT> --graceful-timeout <GRACEFUL_TIMEOUT> \
         -b <HOST>:<PORT> main:app
```
- `WORKERS=2`, `TIMEOUT=240s` (accommodates slow LLM calls), `GRACEFUL_TIMEOUT=60s` — all from `config.yml`.
- Gunicorn manages multiple Uvicorn workers for concurrency and resilience.

All values (`HOST`, `PORT`, `WORKERS`, `TIMEOUT`, `GRACEFUL_TIMEOUT`, `LOG_LEVEL`) are read from `config.yml` `FastAPI` block.

## Prerequisites
- Python 3.12+
- A reachable **MongoDB** (default `mongodb://localhost:27017`)
- A configured LLM provider (local server like Ollama, or API keys for a cloud provider)
- `.env` with the required secrets

## Containerized deployment

Deployment assets live in `artifacts/` (`Dockerfile`, `docker-compose.yml`). Copy them to the project root to build.

### Dockerfile (summary)
```dockerfile
FROM python:3.12-slim
WORKDIR /aichatapp
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md .env ./
RUN uv sync --frozen --no-install-project --no-dev   # cached deps layer
COPY src ./src
COPY main.py ./
RUN uv sync --frozen --no-dev                         # install project
EXPOSE 45001
ENV PYTHONUNBUFFERED=1
ENV PATH="/aichatapp/.venv/bin:$PATH"
CMD ["uv", "run", "--no-sync", "start"]               # production mode
```
Notes:
- Two-stage `uv sync` (deps first, then project) maximizes Docker layer caching.
- `--frozen` enforces the lockfile; `--no-dev` excludes Ruff.
- Default `CMD` runs **production** (Gunicorn). The exposed port (45001) must match `config.yml` `PORT`.
- `COPY ... .env` bakes secrets into the image — prefer runtime env injection / secrets for real deployments (remove `.env` from the COPY).

### docker-compose (summary)
```yaml
services:
  app:
    build: .
    ports: ["45001:45001"]
    environment:
      - MONGO_URL=mongodb://mongodb:27017
    depends_on: [mongodb]
  mongodb:
    image: mongo:latest
    ports: ["27018:27017"]
    volumes: [mongodb_data:/data/db]
volumes:
  mongodb_data:
```
- The compose file sets `MONGO_URL` via env, but the app reads `MONGO_URL` from `config.yml`, **not** from the environment (the code does not call `os.getenv("MONGO_URL")`). To make the compose override effective, either set `MongoDB.MONGO_URL: "mongodb://mongodb:27017"` in `config.yml`, or modify `database.py` to read `os.getenv("MONGO_URL")`.
- MongoDB is published on host port **27018** to avoid clashing with a local Mongo on 27017.

```bash
docker compose up --build
```

## CI/CD

There is **no CI/CD pipeline configured** in the repository (no `.github/workflows`, GitLab CI, etc.). Recommended baseline pipeline:

```yaml
# Suggested .github/workflows/ci.yml (not present — example)
steps:
  - uv sync --frozen
  - uv run ruff check .
  - uv run ruff format --check .
  - uv run pytest -v
  - docker build -t aichatapp .   # on main
```

Quality gates already available locally to wire into CI:
- `ruff check .` / `ruff format --check .` (configured in `pyproject.toml`).
- `pytest -v`.
- `scripts/export_requirements.py`, `scripts/generate_arch_docs.py` for artifact generation.

## Deployment checklist
1. Provision MongoDB; set `MONGO_URL`/`DB_NAME`.
2. Set production secrets via environment (not committed `.env`).
3. Choose provider + model in `config.yml`; ensure keys present.
4. Set `WORKERS` to match CPU; keep `TIMEOUT` ≥ slowest expected LLM latency.
5. Put a TLS-terminating reverse proxy in front; restrict CORS.
6. Remove the `logger.critical("test error")` debug line to stop per-request emails.
7. Ensure `logs/` is writable (or switch handlers to stdout-only for container log capture).

---

Next: [17 — Development Workflow & Coding Standards →](17-development-workflow.md)
