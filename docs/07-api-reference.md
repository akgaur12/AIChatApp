# 07 — API Reference (Endpoints & Contracts)

[← Back to Index](index.md)

Base URL: `http://<HOST>:<PORT>` (default `http://0.0.0.0:45001`). Interactive docs at `/docs` (Swagger) and `/redoc`.

All `/chat/*` routes and most `/auth/*` mutation routes require a **Bearer JWT** in `Authorization: Bearer <token>`. Obtain a token via `/auth/login` or `/auth/login-json`.

| Tag | Prefix | Router |
|-----|--------|--------|
| Auth | `/auth` | `src/api_router/user_router.py` |
| Chat | `/chat` | `src/api_router/chat_router.py` |
| — | `/` | `main.py` (redirect to `/docs`) |

---

## Root

### `GET /`
Redirects (`RedirectResponse`) to `/docs`. No auth.

---

## Auth endpoints (`/auth`)

### `POST /auth/signup` — 201
Create a new user.

**Body** (`UserCreate`):
```json
{ "name": "Jane", "email": "jane@example.com", "password": "secret1", "role": ["ROLE_USER"] }
```
- `name`: 1–20 chars, default `"New User"`.
- `password`: min 6 chars.
- `role`: list; if it contains `ROLE_ADMIN`, the stored roles become `["ROLE_USER","ROLE_ADMIN"]`.

**Responses:** `201 {"message":"User created successfully"}` · `400 {"detail":"Email already registered"}`.

---

### `POST /auth/login` — 200 (OAuth2 form)
OAuth2 password flow used by Swagger's Authorize button. Consumes `application/x-www-form-urlencoded` with `username` (the email) and `password`.

**Response** (`Token`): `{"access_token":"<jwt>","token_type":"bearer"}` · `401` invalid credentials.

---

### `POST /auth/login-json` — 200 (frontend)
JSON login for SPA/mobile clients.

**Body** (`UserLogin`): `{"email":"jane@example.com","password":"secret1"}`
**Response:** `{"access_token":"<jwt>"}` (note: this handler omits `token_type`) · `401` invalid.

---

### `POST /auth/logout` — 200 🔒
Requires auth. Returns `{"message":"Logged out successfully"}`. **Stateless** — the server does not invalidate the token (JWTs remain valid until expiry).

---

### `PUT /auth/reset-password` — 200 🔒
Change password while logged in.
**Body** (`ResetPasswordRequest`): `{"old_password":"...","new_password":"..."}` (each min 6).
`400` if old password incorrect.

---

### `PUT /auth/update-user-name` — 200 🔒
**Body** (`UpdateUserNameRequest`): `{"new_name":"New Name"}` (1–20 chars).

---

### `DELETE /auth/delete-user` — 200 🔒
Cascade delete: removes the user, all their `chats`, and all `chat_messages` for those chats. Returns `{"message":"User and all associated data deleted successfully"}`.

---

### `POST /auth/forget-password` — 200
Request a password-reset OTP by email.
**Body** (`ForgotPasswordRequest`): `{"email":"jane@example.com"}`.
Generates a 6-digit OTP, stores `otp` + `otp_expiry` (now + 5 min) on the user, emails it.
`404` user not found · `500` email send failure.

---

### `POST /auth/verify-otp-reset-password` — 200
Complete reset with the OTP.
**Body** (`ResetPasswordWithOTP`): `{"email":"...","otp":"123456","new_password":"..."}`.
Validates OTP presence, match, and expiry; sets the new hash and unsets `otp`/`otp_expiry`.
`400` for "OTP not requested" / "Invalid OTP" / "OTP expired" · `404` user not found.

---

### `GET /auth/admin-only` — 200 🔒 (RBAC)
Requires `ROLE_ADMIN` via `Depends(RoleChecker(["ROLE_ADMIN"]))`. Returns a greeting. `403` if the user lacks the role.

---

## Chat endpoints (`/chat`)

All require auth (`Depends(get_current_user)`).

### `POST /chat/run_pipeline` — 201 (non-streaming)
Run the AI pipeline and persist the turn.

**Body** (`UserInput`):
```json
{ "service_name": "chat", "user_query": "Explain async IO", "conversation_id": null }
```
- `service_name` must be one of `SUPPORTED_SERVICES` = `["chat","web_search","thinking","image_search","news_search"]` → else `400`.
- `conversation_id` optional. If present it must be a valid ObjectId (`400`) owned by the user (`404`).

**Behavior:** loads last 5 turns as context (if continuing), invokes the pipeline, creates or updates the conversation, inserts the message turn.

**Response** (`UserQueryResponse`): `{"conversation_id":"<id>","message":"<assistant text>"}`.

---

### `POST /chat/run_pipeline/stream` — 200 (SSE)
Same inputs/validation as above, but returns `text/event-stream`. Emits `data: {json}\n\n` frames of `type` `content` | `metadata` | `error`. The final `metadata` frame carries the `conversation_id`. See [03 — Data Flow §2](03-system-design-and-data-flow.md#2-streaming-chat-request-server-sent-events).

Response headers: `Cache-Control: no-cache`, `Connection: keep-alive`.

---

### `POST /chat/conversations` — 201
Create an empty conversation.
**Body** (`ConversationCreate`): `{"title":"My chat"}` (1–60 chars; `None` → `"New Chat"`).
**Response** (`Conversation`): full conversation document with `message_count: 0`.

---

### `GET /chat/conversations` — 200
List the current user's conversations, sorted by `updated_at` descending. Returns `list[Conversation]` (without messages populated).

---

### `GET /chat/conversations/{conversation_id}` — 200
Fetch one conversation **with all message turns** (sorted by `created_at` ascending). `400` invalid id · `404` not found / not owned.

---

### `PUT /chat/conversations/{conversation_id}` — 200
Update conversation fields (currently `title`). Uses `exclude_unset` and refreshes `updated_at`. `400`/`404` as above.

---

### `PUT /chat/conversations/{conversation_id}/rename` — 200
Rename via `{"title":"..."}`. Trims and rejects empty titles (`400`). `404` if not owned.

---

### `DELETE /chat/conversations/{conversation_id}` — 200
Delete one conversation and its messages. `404` if `deleted_count == 0`.

---

### `DELETE /chat/conversations` — 200
Delete **all** of the user's conversations and their messages. Returns `{"message":"<n> conversations and all associated messages deleted successfully"}`.

---

## Status code conventions

| Code | When |
|------|------|
| 200 | Successful read/update/delete/login |
| 201 | Resource created (signup, conversation create, pipeline turn) |
| 400 | Validation error (bad id, unsupported service, wrong old password, duplicate email, OTP errors) |
| 401 | Missing/invalid/expired token, or bad login |
| 403 | RBAC — missing required role |
| 404 | User/conversation not found |
| 422 | Pydantic body validation failure (automatic from FastAPI) |
| 500 | Email send failure |

## Error response shape

FastAPI `HTTPException`s serialize to:
```json
{ "detail": "Human-readable message" }
```
`422` validation errors use FastAPI's structured `detail` array (field locations + messages).

## Authentication header

```
Authorization: Bearer eyJhbGciOiJIUzI1NiІ...
```
The JWT payload contains `sub` (email), `name`, `iat`, and `exp`. Token lifetime is `ACCESS_TOKEN_EXPIRE_MINUTES` (default 360 = 6 hours).

---

Next: [08 — Database Schema & Models →](08-database-schema.md)
