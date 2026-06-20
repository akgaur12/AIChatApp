# 03 — System Design & Data Flow

[← Back to Index](index.md)

This document traces how data moves through the system for the major use cases, with sequence diagrams (Mermaid) and flow diagrams.

---

## 1. Non-streaming chat request

Endpoint: `POST /chat/run_pipeline` → handler `execute_user_query` (`src/api_router/chat_router.py`).

```mermaid
sequenceDiagram
    participant C as Client
    participant API as chat_router.execute_user_query
    participant Auth as deps.get_current_user
    participant DB as MongoDB (Motor)
    participant PIPE as LangGraph pipeline
    participant LLM as llm_model

    C->>API: POST /chat/run_pipeline {service_name, user_query, conversation_id?}
    API->>Auth: Depends(get_current_user)
    Auth->>DB: users.find_one({email from JWT})
    DB-->>Auth: user doc
    Auth-->>API: current_user

    API->>API: validate service_name in SUPPORTED_SERVICES
    alt conversation_id provided
        API->>DB: chats.find_one({_id, user_id})  (ownership check)
        API->>DB: chat_messages.find(...).sort(created_at,-1).limit(5)
        DB-->>API: last 5 turns
        API->>API: build llm_messages [Human, AI, ...]
    end
    API->>API: append HumanMessage(user_query)

    API->>PIPE: pipeline.ainvoke({service_name, user_input, llm_messages})
    PIPE->>LLM: ainvoke(messages / prompt)
    LLM-->>PIPE: AIMessage
    PIPE-->>API: state {llm_response, input_tokens, output_tokens, response_time}

    alt new conversation
        API->>LLM: generate_chat_title(user_query)
        API->>DB: chats.insert_one(metadata)
    else existing
        API->>DB: chats.find_one_and_update($inc message_count, $set updated_at)
    end
    API->>DB: chat_messages.insert_one(turn_doc)
    API-->>C: 201 {conversation_id, message}
```

### Step-by-step
1. **Auth** — `get_current_user` decodes the JWT, extracts `sub` (email), and loads the user from MongoDB.
2. **Service validation** — `service_name` must be in `cfg["Services"]["SUPPORTED_SERVICES"]` (`chat`, `web_search`, `thinking`, `image_search`, `news_search`).
3. **History load** — if `conversation_id` is supplied, ownership is verified, then the **last 5 turns** are fetched (newest-first, then reversed to chronological) and expanded into alternating `HumanMessage` / `AIMessage` objects.
4. **Pipeline invocation** — `pipeline.ainvoke(...)` runs the LangGraph (see [12 — Pipeline](12-pipeline.md)).
5. **Persistence** — new conversations get an LLM-generated title and a `chats` document; existing ones are atomically updated (`message_count++`, `updated_at`). The turn is written to `chat_messages` with token/latency metrics and a `seq` number.
6. **Response** — `{conversation_id, message}`.

---

## 2. Streaming chat request (Server-Sent Events)

Endpoint: `POST /chat/run_pipeline/stream` → handler `execute_user_query_streaming`.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as chat_router.streaming
    participant PIPE as pipeline.astream_events(v2)
    participant LLM as llm_model
    participant DB as MongoDB

    C->>API: POST /chat/run_pipeline/stream
    API->>API: auth + validate + load history (same as non-streaming)
    API-->>C: 200 text/event-stream (begins)
    loop pipeline events
        PIPE->>LLM: stream tokens
        alt event == on_chat_model_stream
            API-->>C: data: {type:"content", content:"<chunk>"}
        else event == on_chat_model_end
            API->>API: capture usage_metadata (tokens)
        else event == on_chain_end
            API->>API: capture final llm_response
        end
    end
    API->>API: reconcile streamed vs full_response (emit diff, e.g. source links)
    API->>DB: chats insert/update + chat_messages.insert_one
    API-->>C: data: {type:"metadata", conversation_id}
```

### SSE event protocol
The stream emits newline-delimited `data: <json>` frames. Frame `type` values:

| `type` | Payload | Meaning |
|--------|---------|---------|
| `content` | `{type, content}` | An incremental token/chunk of the answer |
| `metadata` | `{type, conversation_id}` | Final frame after the turn is persisted |
| `error` | `{type, detail}` | An error during streaming or DB save |

**Reconciliation detail:** search nodes append a `**Sources:**` link block to `llm_response` that is *not* streamed token-by-token. After streaming ends, the handler compares `full_response` (from `on_chain_end`) with `streamed_response` and emits the trailing **diff** as one final `content` frame so the client receives the links.

---

## 3. Authentication & login flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as user_router
    participant DB as MongoDB users
    participant U as utils

    C->>API: POST /auth/signup {name,email,password,role}
    API->>DB: users.find_one({email})
    alt exists
        API-->>C: 400 Email already registered
    else
        API->>U: hash_password(password)  (bcrypt)
        API->>DB: users.insert_one(...)
        API-->>C: 201 User created
    end

    C->>API: POST /auth/login (OAuth2 form) or /auth/login-json
    API->>DB: users.find_one({email})
    API->>U: verify_password(password, hash)
    alt invalid
        API-->>C: 401 Invalid email or password
    else valid
        API->>U: create_access_token({sub:email, name})
        API-->>C: {access_token, token_type:"bearer"}
    end
```

See [09 — Authentication & Authorization](09-authentication.md) for OTP password reset and RBAC.

---

## 4. Tool-routing decision flow (inside the pipeline)

```mermaid
flowchart TD
    START([START]) --> ST[select_tool_node]
    ST -->|service already web/image/news_search| ROUTE
    ST -->|query matches SELF_PATTERN| SELF[service = self]
    ST -->|query matches SEARCH_PATTERN| WS[service = web_search]
    ST -->|otherwise| KEEP[service unchanged e.g. chat]
    SELF --> ROUTE{conditional edge on service_name}
    WS --> ROUTE
    KEEP --> ROUTE
    ROUTE -->|self| SN[self_node_]
    ROUTE -->|chat / thinking| CN[chat_node]
    ROUTE -->|web_search / image_search / news_search| SRCH[search_node]
    SN --> END([END])
    CN --> END
    SRCH --> END
```

- `SELF_PATTERN` matches identity questions ("who are you", "what is your name", …) → `self_node` answers as **SannaAI**.
- `SEARCH_PATTERN` matches time-sensitive keywords ("current", "today", "latest", "news", "weather", "price", "stock", "score", "live", "who is") → upgrades the service to `web_search`.
- Otherwise the request flows to `chat_node` (plain LLM call with full message history).

---

## 5. End-to-end data lifecycle of a conversation

```
signup ──> login (JWT) ──> POST /chat/run_pipeline (no conversation_id)
                               │
                               ├─ pipeline answers
                               ├─ chats.insert_one  (title auto-generated)
                               └─ chat_messages.insert_one (seq=1)
                                       │
            POST /chat/run_pipeline (conversation_id) ──► loads last 5 turns
                                       │                    chats.$inc message_count
                                       └─ chat_messages.insert_one (seq=N)
                                       │
            GET /chat/conversations            ──► list (sorted by updated_at desc)
            GET /chat/conversations/{id}        ──► full thread (messages sorted asc)
            PUT /chat/conversations/{id}/rename ──► change title
            DELETE /chat/conversations/{id}     ──► delete chat + its messages
            DELETE /auth/delete-user            ──► cascade delete user+chats+messages
```

---

Next: [04 — Technology Stack & Dependencies →](04-tech-stack.md)
