# 17 — Development Workflow & Coding Standards

[← Back to Index](index.md)

## Setting up a dev environment

```bash
git clone https://github.com/akgaur12/AIChatApp.git
cd AIChatApp
uv sync                      # install deps from uv.lock
cp .env.example .env         # (create/populate secrets — no example committed; see docs/10)
# start MongoDB locally
uv run start dev             # hot-reload server
```

Open `http://localhost:45001/docs` for Swagger UI to exercise endpoints interactively.

## Coding standards

### Linting & formatting — Ruff
Configured in `pyproject.toml`:
```toml
[tool.ruff]
line-length = 200
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "B", "I", "UP", "C4", "SIM"]   # style, bugs, bugbear, imports, pyupgrade, comprehensions, simplify
fixable = ["ALL"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

Commands:
```bash
uv run ruff check .            # lint
uv run ruff check . --fix      # autofix
uv run ruff format .           # format (double quotes, spaces)
```

The git history shows a `chore: apply Ruff auto-fixes across codebase` commit — Ruff is the canonical quality gate.

### Conventions observed in the codebase
- **Python ≥3.12 idioms:** `X | None` unions, `datetime.UTC`, `tomllib`, built-in generics (`list[str]`).
- **Async everywhere** for I/O (routes, DB, LLM calls). Never block the event loop.
- **Type hints** on function signatures; Pydantic models for all request/response bodies.
- **Module-level singletons** for shared resources (`cfg`, DB collections, `llm_model`, `pipeline`).
- **Dependency injection** via FastAPI `Depends` (auth, RBAC) and explicit parameter injection to dodge circular imports (`generate_chat_title(..., llm_model, parse_response)`).
- **Imports ordered** stdlib → third-party → local (enforced by Ruff `I`).
- **Naming:** snake_case functions/vars, PascalCase classes, UPPER_SNAKE config keys.
- **Docstrings/section comments** at the top of modules and grouping route sections with `# ---- NAME ----` banners.

### Commit message style (from history)
Conventional-commits style: `feat:`, `refactor:`, `chore:`, `docs:`, `test:`, with optional scope, e.g.:
```
feat(auth/user): implement RBAC, switch to bcrypt, and enhance user deletion
refactor(logging): replace code-based logging setup with YAML config
```

## Utility scripts (`scripts/`)

| Script | Run | What it does |
|--------|-----|--------------|
| `lint_project.py` | `python scripts/lint_project.py` | Runs ruff → black → isort → mypy in sequence (requires those extra tools). |
| `clean_pycache.py` | `python scripts/clean_pycache.py` | Removes all `__pycache__` dirs and `.pyc` files. |
| `export_requirements.py` | `python scripts/export_requirements.py` | Dumps `pyproject.toml` deps to `artifacts/requirements.txt`. |
| `check_package_sizes.py` | `python scripts/check_package_sizes.py` | Reports installed package sizes (needs `tqdm`). |
| `generate_project_tree.py` | `python scripts/generate_project_tree.py` | Writes a tree to `artifacts/project_tree.txt`. |
| `generate_pipeline_graphs.py` | `python scripts/generate_pipeline_graphs.py` | Renders the LangGraph to `artifacts/main_pipeline.png` (Mermaid). |
| `pipeline_summary.py` | `python scripts/pipeline_summary.py` | Prints node/edge counts of the compiled pipeline. |
| `generate_arch_docs.py` | `python scripts/generate_arch_docs.py` | Builds `artifacts/ARCHITECTURE.md` from tree + graphs. |

> Some scripts depend on tools not in `pyproject.toml` (`black`, `isort`, `mypy`, `tqdm`). Install them in your dev env if you use those scripts.

## Typical workflows

### Add an API endpoint
1. Add request/response models to `src/schemas.py`.
2. Add the handler to the appropriate router (`chat_router.py` / `user_router.py`) with `Depends(get_current_user)` if protected.
3. Update [07 — API Reference](07-api-reference.md).
4. Add a test in `tests/` (mock the collection + override auth).

### Add an LLM provider
See the checklist in [11 — LLM Providers](11-llm-providers.md).

### Add a pipeline service/node
See [12 — Pipeline → Extending](12-pipeline.md#extending-the-pipeline).

### Contribution flow (from README)
1. Fork → feature branch (`feature/xyz`).
2. Implement + run `ruff` and `pytest`.
3. Commit using conventional style.
4. Open a Pull Request.

## Editor setup
A `.vscode/settings.json` is present. The `.gitattributes` and a comprehensive Python `.gitignore` are included. `.ruff_cache/` and `.pytest_cache/` are tool caches (ignored).

## Local debugging tips
- Use `uv run start dev` for autoreload; logs stream to console and `logs/`.
- Inspect per-level logs in `logs/{debug,info,warning,error}.log`.
- Use Swagger `/docs` "Authorize" with `/auth/login` to test protected routes.
- To visualize the pipeline, run `scripts/generate_pipeline_graphs.py`.

---

Next: [18 — Troubleshooting Guide →](18-troubleshooting.md)
