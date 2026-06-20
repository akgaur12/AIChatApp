# 14 — Security Considerations

[← Back to Index](index.md)

This chapter documents the security posture **as implemented** and lists concrete hardening recommendations. Items marked ⚠️ are things to address before a production deployment.

## What's already in place

- **Password hashing** with bcrypt + per-password salt (`hash_password` / `verify_password`).
- **Stateless JWT** auth (HS256) with `exp` and `iat` claims; 6-hour expiry.
- **Secrets via environment** — `JWT_SECRET_KEY` and provider keys are read from `.env` (env overrides `config.yml`).
- **RBAC** for admin-restricted routes (`RoleChecker`).
- **Ownership checks** — chat routes always scope queries by `user_id`/owner before reading or mutating.
- **Cascade deletes** — deleting a user/conversation removes dependent messages, avoiding orphaned data.
- **Input validation** via Pydantic (email format, length limits) and explicit `ObjectId.is_valid` checks.
- **SMTP credentials injected at runtime** into the logging config rather than stored in YAML.

## Threat surface & findings

### ⚠️ 1. Anyone can self-register as admin
`signup` honors a client-supplied `role`: if it contains `ROLE_ADMIN`, the user is stored as admin.
```python
"role": ["ROLE_USER", "ROLE_ADMIN"] if "ROLE_ADMIN" in user.role else user.role
```
**Fix:** ignore client-supplied roles at signup (always `["ROLE_USER"]`); grant admin only through a trusted, authenticated admin path.

### ⚠️ 2. Permissive CORS
```python
allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
```
`allow_origins=["*"]` together with `allow_credentials=True` is broadly permissive. **Fix:** enumerate trusted origins for production.

### ⚠️ 3. Secrets committed to the repo
A populated `.env` exists in the working tree. **Fix:** ensure `.env` is git-ignored and rotate any leaked keys (JWT secret, AWS, Groq, NVIDIA, Google, HuggingFace, OpenRouter, Gmail app password). Use a secrets manager in production.

### ⚠️ 4. No rate limiting
Login, signup, forgot-password, and verify-OTP have no throttling — exposed to brute force and OTP guessing (OTP is only 6 digits, 5-minute window, plaintext-stored, unlimited attempts). **Fix:** add rate limiting (e.g. a reverse-proxy limit or `slowapi`), cap OTP attempts, and hash the stored OTP.

### ⚠️ 5. Logout doesn't revoke tokens
JWTs remain valid until expiry. **Fix (if needed):** short-lived access tokens + refresh tokens, or a server-side denylist.

### ⚠️ 6. `select_tool_node` logs CRITICAL on every request
This triggers an **email alert per request** through the SMTP log handler (`logging.yaml`). It is noise, a potential mail-quota/DoS issue, and may leak operational details. **Fix:** remove the `logger.critical("test error")` line.

### ⚠️ 7. No unique index on `users.email`
Duplicate detection is a read-then-write check, which is racy under concurrency. **Fix:** add a unique index on `email`.

### 8. SSRF / content-trust in search node
`search_node` feeds third-party web/news/image content directly into the LLM prompt. This is inherent to RAG but means **prompt-injection** from web content is possible. Treat answers as untrusted; consider sanitization/guardrails if the output drives actions.

### 9. JWT secret fallback to config
`JWT_SECRET_KEY` falls back to `config.yml["Security"]["JWT_SECRET_KEY"]`. The committed `config.yml` does **not** define it (so it must come from env) — but ensure no weak default is ever added there.

### 10. `python-jose` algorithm pinning
`jwt.decode(..., algorithms=[ALGORITHM])` correctly pins `HS256`, preventing `alg=none` / algorithm-confusion attacks. ✅

## Recommended hardening checklist

| Priority | Action |
|----------|--------|
| 🔴 High | Strip client role on signup; admin grant via trusted path |
| 🔴 High | Rotate & externalize all secrets; verify `.env` is git-ignored |
| 🔴 High | Remove `logger.critical("test error")` debug line |
| 🟠 Med | Restrict CORS origins for production |
| 🟠 Med | Add rate limiting on auth/OTP endpoints; cap & hash OTP |
| 🟠 Med | Add unique index on `users.email` |
| 🟢 Low | Add a global exception handler that avoids leaking internals |
| 🟢 Low | Consider refresh tokens + revocation for real logout |
| 🟢 Low | Add HTTPS/TLS termination and security headers at the proxy |

## Data protection notes
- Passwords are never stored or logged in plaintext.
- Conversation content is stored unencrypted in MongoDB — apply DB-level encryption-at-rest and access controls as required by your data policy.
- Token payloads contain `email` and `name` — these are visible to anyone holding the token (JWT payloads are base64, not encrypted).

---

Next: [15 — Testing Strategy & Coverage →](15-testing.md)
