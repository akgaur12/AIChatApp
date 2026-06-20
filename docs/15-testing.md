# 15 — Testing Strategy & Coverage

[← Back to Index](index.md)

## Tooling

- **Runner:** `pytest` (`>=9.0.2`).
- **Async support:** `pytest-asyncio` (`@pytest.mark.asyncio`).
- **HTTP client:** Starlette `TestClient` (FastAPI's test client) for in-process requests.
- **Mocking:** `unittest.mock` (`MagicMock`, `AsyncMock`, `patch`).

Run the suite:
```bash
pytest -v
```

## Test layout

```text
tests/
├── conftest.py            # fixtures + DB mocking before app import
├── test_main.py           # app smoke tests
├── test_utils.py          # unit tests for utils.py
├── test_user_routes.py    # integration tests for /auth routes
└── test_chat_routes.py    # integration tests for /chat routes
```

## Key strategy: mock the DB at import time

The Motor driver is replaced with a `MagicMock` **before** `main` is imported, so no real MongoDB is needed:

```python
# conftest.py
sys.modules["motor.motor_asyncio"] = MagicMock()
sys.modules["motor.motor_asyncio"].AsyncIOMotorClient = MagicMock()
from main import app

@pytest.fixture(scope="module")
def test_client():
    client = TestClient(app)
    yield client
```

Per-test, the relevant collection is patched (e.g. `patch("src.api_router.user_router.users_collection")`) and given `AsyncMock` methods. Async cursors are simulated by setting `mock_cursor.__aiter__.return_value = [...]` and chaining `.sort.return_value = mock_cursor`.

## Auth dependency overriding

Protected routes are tested by overriding the auth dependency rather than minting real tokens:

```python
async def mock_get_current_user():
    return {"_id": ObjectId("507f1f77bcf86cd799439011"), "email": "test@example.com"}

app.dependency_overrides[get_current_user] = mock_get_current_user
# ... call endpoint ...
app.dependency_overrides = {}   # reset
```

## Coverage by file

### `test_main.py` — smoke
- `GET /docs` returns 200.
- App title is `"AIChatApp"`.

### `test_utils.py` — unit
| Test | Asserts |
|------|---------|
| `test_load_config` | config loads as dict, contains `FastAPI` |
| `test_hash_password` | hash ≠ plaintext; verify true/false correctly |
| `test_create_access_token` | token is a str; decodes with `sub`, `exp`, `iat` |
| `test_generate_otp` | 6-digit numeric string |
| `test_send_otp_email` | sends to `TEST_EMAIL` and returns True *(hits real SMTP — see caveat)* |
| `test_generate_chat_title` (async) | strips double/single quotes, passes through plain titles, falls back to `query[:30]` on exception |

### `test_user_routes.py` — integration (`/auth`)
- `signup` success (201) and duplicate email (400).
- `login-json` success (token returned) and invalid (401).
- `logout` (200, with dependency override).
- `reset-password` (200, with `verify_password` patched).
- `delete-user` cascade (200, all collections mocked).

### `test_chat_routes.py` — integration (`/chat`)
- `create_conversation` (201, title/message_count).
- `list_conversations` (200, sorted, count).
- `run_pipeline` new conversation (201; pipeline + title generation + DB inserts mocked; asserts `insert_one` called once each).
- `get_conversation_by_id` (200, messages populated).
- `rename_conversation` (200; `find_one` `side_effect` for ownership then updated doc).
- `delete_conversation` (200; asserts `delete_many` called with the string `chat_id`).

## What's tested vs. not

| Area | Covered |
|------|---------|
| utils (hashing, JWT, OTP, title) | ✅ unit |
| auth routes | ✅ happy + error paths |
| chat CRUD + non-streaming pipeline | ✅ integration (mocked) |
| RBAC (`RoleChecker`) | ❌ no dedicated test |
| streaming endpoint (`/run_pipeline/stream`) | ❌ not tested |
| LLM providers / factory | ❌ no tests |
| pipeline nodes (search/self routing) | ❌ no tests |
| OTP verify route | ❌ not tested |

## Caveats & gotchas
- **`test_send_otp_email` performs a real SMTP send** to `TEST_EMAIL` using `SENDER_EMAIL`/`SENDER_PASSWORD` from `.env`. It will fail (or send mail) depending on environment — consider mocking `smtplib.SMTP` to make it hermetic and offline-safe.
- Importing `main` builds the `llm_model` singleton (`llm_client.get_llm_model()`) at import. With the DB mocked but the LLM not, tests rely on the provider's `create_model` not making network calls at construction time. If a provider validates credentials eagerly, set a benign provider (e.g. `ollama`) for tests.
- `pytest-asyncio` mode: async tests are explicitly marked `@pytest.mark.asyncio`.

## Suggested additions
1. Mock SMTP in `test_send_otp_email`.
2. Add tests for `RoleChecker` (403 path) and the OTP verify flow.
3. Add a streaming test that asserts SSE `content`/`metadata` frames.
4. Unit-test `LLMFactory.get_provider` (valid + `ValueError` on unknown).
5. Unit-test `parse_response` branches (`openai`, `aws_bedrock`, passthrough).

---

Next: [16 — Build, Deployment & CI/CD →](16-build-deployment.md)
