# Architecture Diagrams

**AIChatApp** is a production-ready AI chat backend built with FastAPI, LangGraph, and MongoDB. It
exposes REST + SSE endpoints for real-time chat and web search, authenticates users via JWT,
persists conversation history in MongoDB, and routes requests through a LangGraph state-machine
pipeline that dispatches to any of nine configurable LLM providers (Ollama, vLLM, Groq, AWS
Bedrock, Google Gemini, NVIDIA, HuggingFace, llama.cpp, OpenRouter) or DuckDuckGo search.

---

## Contents

1. [System Architecture](#1-system-architecture)
2. [Component Layering and Dependency Direction](#2-component-layering-and-dependency-direction)
3. [Authentication Flow](#3-authentication-flow)
4. [Chat Request Flow (Non-Streaming)](#4-chat-request-flow-non-streaming)
5. [Streaming Chat Flow (SSE)](#5-streaming-chat-flow-sse)
6. [LangGraph Pipeline Flowchart](#6-langgraph-pipeline-flowchart)
7. [LLM Provider Factory Pattern](#7-llm-provider-factory-pattern)
8. [Data Model (MongoDB Collections)](#8-data-model-mongodb-collections)
9. [Deployment Topology](#9-deployment-topology)

---

## 1. System Architecture

Shows the top-level containers: the FastAPI backend, MongoDB database, and every external service
the app talks to (LLM providers, DuckDuckGo search, Gmail SMTP).

![System Architecture](diagrams/01-system-architecture.png)

```mermaid
graph TB
    Client["Client (Browser / Mobile App)"]

    subgraph AIChatApp["AIChatApp — FastAPI Backend"]
        direction TB
        Entry["main.py\nEntry Point"]
        CORS["CORS Middleware"]
        AuthRouter["user_router.py\nPREFIX: /auth"]
        ChatRouter["chat_router.py\nPREFIX: /chat"]
        Deps["deps.py\nJWT Auth Dependency"]
        Utils["utils.py\nJWT / OTP / Email / bcrypt"]
        Pipeline["LangGraph Pipeline\npipelines/builder.py"]
        LLMClient["clients/llm_client.py\nLLMFactory singleton"]
    end

    subgraph LLMProviders["LLM Providers (configured via config.yml)"]
        Ollama["Ollama\n(local)"]
        VLLM["vLLM\n(self-hosted)"]
        Groq["Groq API"]
        Bedrock["AWS Bedrock"]
        Google["Google Gemini"]
        NVIDIA["NVIDIA NIM"]
        HF["HuggingFace Hub"]
        LlamaCpp["llama.cpp\n(local GGUF)"]
        OR["OpenRouter"]
    end

    MongoDB[("MongoDB\nai_chat_app\nusers / chats / chat_messages")]
    DDGS["DuckDuckGo Search\n(ddgs library)"]
    SMTP["Gmail SMTP\nOTP emails"]

    Client -- "HTTP REST / SSE" --> CORS
    CORS --> AuthRouter
    CORS --> ChatRouter
    AuthRouter --> Deps
    ChatRouter --> Deps
    AuthRouter --> Utils
    Deps --> MongoDB
    AuthRouter --> MongoDB
    ChatRouter --> MongoDB
    ChatRouter --> Pipeline
    Pipeline --> LLMClient
    Pipeline --> DDGS
    LLMClient --> LLMProviders
    Utils --> SMTP
```

---

## 2. Component Layering and Dependency Direction

Maps the four layers of the codebase — Presentation (API routes), Application (business logic and
pipeline), Infrastructure (database + LLM clients), and Configuration — and shows which modules
import which.

![Component Layering](diagrams/02-component-layering.png)

```mermaid
graph TB
    subgraph Presentation["Presentation Layer — API Routes"]
        CR["chat_router.py\nCRUD for conversations + pipeline"]
        UR["user_router.py\nsignup / login / password reset"]
    end

    subgraph Application["Application Layer — Business Logic"]
        Deps["deps.py\nget_current_user + RoleChecker"]
        Utils["utils.py\nJWT tokens, bcrypt, OTP, SMTP"]
        Nodes["pipelines/nodes.py\nselect_tool, chat, search, self"]
        Builder["pipelines/builder.py\nLangGraph StateGraph"]
        State["pipelines/pipeline_state.py\nPipelineState TypedDict"]
        Prompts["prompts/prompts.py\nWEB / IMAGE / NEWS / SELF templates"]
    end

    subgraph Infrastructure["Infrastructure Layer"]
        DB["database.py\nMotor AsyncIOMotorClient"]
        LLMClient["clients/llm_client.py\nget_llm_model() singleton"]
        LLMFactory["llms/llm_factory.py\nLLMFactory.get_provider()"]
        Providers["llms/*.py\n9 provider implementations"]
        Parser["llms/llm_parser.py\nparse_response()"]
    end

    subgraph Config["Configuration"]
        YML["config/config.yml\nserver / DB / LLM / email settings"]
        ENV[".env\nJWT secret / API keys / credentials"]
    end

    CR --> Deps
    CR --> Builder
    CR --> DB
    CR --> Utils
    UR --> Deps
    UR --> DB
    UR --> Utils
    Deps --> DB
    Deps --> Utils
    Builder --> Nodes
    Nodes --> State
    Nodes --> LLMClient
    Nodes --> Prompts
    Nodes --> Parser
    LLMClient --> LLMFactory
    LLMFactory --> Providers
    LLMClient --> YML
    LLMClient --> ENV
    DB --> YML
    Utils --> ENV
    Utils --> YML
```

---

## 3. Authentication Flow

Covers all three user-auth paths: Signup, Login (OAuth2PasswordRequestForm + JSON variants),
and the Forgot Password → OTP → Reset flow. JWT tokens are HS256, signed with `JWT_SECRET_KEY`,
and expire after 6 hours (configurable). Passwords are hashed with bcrypt.

![Auth Flow](diagrams/03-auth-flow.png)

```mermaid
sequenceDiagram
    participant C as Client
    participant UR as user_router
    participant U as utils.py
    participant DB as MongoDB users
    participant E as Gmail SMTP

    note over C,DB: Signup
    C->>UR: POST /auth/signup {name, email, password, role}
    UR->>DB: find_one email
    DB-->>UR: null (email available)
    UR->>U: hash_password (bcrypt)
    U-->>UR: hashed_password
    UR->>DB: insert_one user document
    UR-->>C: 201 User created successfully

    note over C,DB: Login
    C->>UR: POST /auth/login-json {email, password}
    UR->>DB: find_one email
    DB-->>UR: user document
    UR->>U: verify_password (bcrypt.checkpw)
    U-->>UR: true
    UR->>U: create_access_token (JWT HS256)
    U-->>UR: signed JWT token
    UR-->>C: 200 {access_token, token_type}

    note over C,DB: Authenticated Request
    C->>UR: Any protected route + Bearer token
    UR->>UR: deps.get_current_user
    UR->>UR: jwt.decode(token, JWT_SECRET_KEY)
    UR->>DB: find_one by email from token payload
    DB-->>UR: user document
    UR-->>C: route response

    note over C,E: Forgot Password OTP Flow
    C->>UR: POST /auth/forget-password {email}
    UR->>DB: find_one email
    UR->>U: generate_otp (6 digits, 5 min expiry)
    UR->>DB: update otp and otp_expiry fields
    UR->>U: send_otp_email (SMTP starttls)
    U->>E: send OTP email
    E-->>C: email delivered
    C->>UR: POST /auth/verify-otp-reset-password {email, otp, new_password}
    UR->>DB: find_one email
    UR->>UR: validate otp and check expiry
    UR->>U: hash_password (new password)
    UR->>DB: update hashed_password, unset otp fields
    UR-->>C: 200 Password reset successfully
```

---

## 4. Chat Request Flow (Non-Streaming)

Traces a full non-streaming chat request through JWT validation, conversation history loading
(last 5 turns), the LangGraph pipeline, LLM inference, and dual-path MongoDB persistence
(new vs. existing conversation). Entry point: `chat_router.py:execute_user_query` (line 49).

![Chat Request Flow](diagrams/04-chat-request-flow.png)

```mermaid
sequenceDiagram
    participant C as Client
    participant CR as chat_router
    participant JWT as deps.get_current_user
    participant DB as MongoDB
    participant P as LangGraph Pipeline
    participant N as Pipeline Nodes
    participant LLM as LLM Provider
    participant DDGS as DuckDuckGo

    C->>CR: POST /chat/run_pipeline {user_query, service_name, conversation_id}
    CR->>JWT: validate Bearer token
    JWT-->>CR: user document

    alt conversation_id provided
        CR->>DB: find conversation in chats
        DB-->>CR: conversation document
        CR->>DB: find last 5 messages from chat_messages (sorted desc, limit 5)
        DB-->>CR: message turns
        CR->>CR: build llm_messages list (HumanMsg + AIMsg pairs)
    end

    CR->>CR: append current HumanMessage to llm_messages
    CR->>P: ainvoke({service_name, user_input, llm_messages})
    P->>N: select_tool_node

    alt already routed or SELF_PATTERN match
        N->>N: set service = self or keep service
    else SEARCH_PATTERN keyword keyword match
        N->>N: set service = web_search
    end

    alt service = web_search or image_search or news_search
        N->>DDGS: text/images/news search (max 5 results)
        DDGS-->>N: search results with body and links
        N->>N: format prompt from WEB/IMAGE/NEWS template
        N->>LLM: ainvoke([HumanMessage(formatted_prompt)])
    else service = self
        N->>LLM: ainvoke([HumanMessage(SELF_PROMPT)])
    else service = chat or thinking
        N->>LLM: ainvoke(llm_messages with history)
    end

    LLM-->>N: AIMessage (content + response_metadata)
    N->>N: parse_response, measure response_time
    N-->>P: updated PipelineState
    P-->>CR: {llm_response, input_tokens, output_tokens, response_time}

    alt new conversation (no conversation_id)
        CR->>LLM: generate_chat_title (short 3-5 word title)
        LLM-->>CR: title string
        CR->>DB: insert_one into chats collection
        DB-->>CR: new conversation_id
    else existing conversation
        CR->>DB: find_one_and_update chats (inc message_count, set updated_at)
        DB-->>CR: updated conversation
    end

    CR->>DB: insert_one turn into chat_messages (user, assistant, tokens, seq)
    CR-->>C: 201 {conversation_id, message}
```

---

## 5. Streaming Chat Flow (SSE)

Shows how the streaming endpoint (`POST /chat/run_pipeline/stream`) uses
`pipeline.astream_events()` to forward token chunks as Server-Sent Events while deferring
MongoDB writes until the stream completes. Entry point: `chat_router.py:execute_user_query_streaming`
(line 152).

![Streaming Chat Flow](diagrams/05-streaming-chat-flow.png)

```mermaid
sequenceDiagram
    participant C as Client
    participant CR as chat_router
    participant P as LangGraph Pipeline
    participant LLM as LLM Provider
    participant DB as MongoDB

    C->>CR: POST /chat/run_pipeline/stream {user_query, service_name, conversation_id}
    CR->>CR: validate JWT, load history (same as non-stream)
    CR-->>C: 200 StreamingResponse (text/event-stream)

    note over C,LLM: SSE streaming loop via pipeline.astream_events()

    loop on_chat_model_stream events
        P->>LLM: astream tokens
        LLM-->>P: token chunk
        P-->>C: data: {"type":"content","content":"token"}
    end

    P->>LLM: on_chat_model_end (usage_metadata)
    LLM-->>P: input_tokens, output_tokens

    P->>P: on_chain_end (full state with llm_response)
    P-->>P: capture full_response from pipeline state

    note over CR,C: Check for extra content not streamed (e.g. link sections)
    CR->>CR: compare full_response vs streamed_response
    alt extra content (links section)
        CR-->>C: data: {"type":"content","content":"...links..."}
    end

    CR->>DB: generate_chat_title if new conversation
    CR->>DB: insert_one conversations or update message_count
    CR->>DB: insert_one chat_messages (full_response, tokens, seq)
    CR-->>C: data: {"type":"metadata","conversation_id":"..."}
```

---

## 6. LangGraph Pipeline Flowchart

Traces the LangGraph `StateGraph` compiled in `pipelines/builder.py`. The routing logic in
`select_tool_node` (nodes.py:43) inspects the incoming `service_name` and two regex patterns
(`SEARCH_PATTERN`, `SELF_PATTERN`) to decide which downstream node handles the request.

![LangGraph Pipeline](diagrams/06-langgraph-pipeline.png)

```mermaid
flowchart TD
    START([START]) --> SN["select_tool_node\n(nodes.py:43)"]

    SN --> Q1{already routed to\nweb/image/news?}
    Q1 -->|yes| ROUTE{route by\nservice_name}
    Q1 -->|no| Q2{SELF_PATTERN\nmatch in user_input?}
    Q2 -->|yes| SET_SELF[set service_name = self]
    Q2 -->|no| Q3{SEARCH_PATTERN\nkeyword match?}
    Q3 -->|yes| SET_WEB[set service_name = web_search]
    Q3 -->|no| KEEP[keep original service_name]
    SET_SELF --> ROUTE
    SET_WEB --> ROUTE
    KEEP --> ROUTE

    ROUTE -->|self| SELFN["self_node_\n(nodes.py:168)"]
    ROUTE -->|"chat, thinking"| CHAT["chat_node\n(nodes.py:63)"]
    ROUTE -->|"web_search,\nimage_search,\nnews_search"| SEARCH["search_node\n(nodes.py:85)"]

    SELFN --> LLM_S["ainvoke SELF_PROMPT\nvia llm_model"]
    CHAT --> LLM_C["ainvoke llm_messages\n(with chat history)"]
    SEARCH --> Q4{service_name?}

    Q4 -->|web_search| WEB["DDGS().text()\nmax_results=5"]
    Q4 -->|image_search| IMG["DDGS().images()\nmax_results=4"]
    Q4 -->|news_search| NEWS["DDGS().news()\nmax_results=5"]

    WEB --> FMT_W["format WEB_SEARCH_PROMPT\n+ links_section"]
    IMG --> FMT_I["format IMAGE_SEARCH_PROMPT\n+ image URLs"]
    NEWS --> FMT_N["format NEWS_SEARCH_PROMPT\n+ news URLs"]

    FMT_W --> LLM_SR["ainvoke formatted prompt\nvia llm_model"]
    FMT_I --> LLM_SR
    FMT_N --> LLM_SR

    LLM_S --> PARSE_S["parse_response()\nrecord response_time, tokens"]
    LLM_C --> PARSE_C["parse_response()\nrecord response_time, tokens"]
    LLM_SR --> PARSE_SR["parse_response()\nrecord response_time, tokens\nappend links_section"]

    PARSE_S --> END1([END])
    PARSE_C --> END2([END])
    PARSE_SR --> END3([END])
```

---

## 7. LLM Provider Factory Pattern

`LLMFactory` (llms/llm_factory.py) maps a string key from `config.yml` → `LLM.Provider` to a
concrete `BaseLLMProvider` subclass. `get_llm_model()` in `clients/llm_client.py` resolves the
singleton at startup; all pipeline nodes share the same instance.

![LLM Provider Factory](diagrams/07-llm-provider-factory.png)

```mermaid
classDiagram
    class BaseLLMProvider {
        <<abstract>>
        +create_model(config dict, kwargs) LangChain_LLM
    }

    class LLMFactory {
        +_providers dict
        +get_provider(provider_type str) BaseLLMProvider
    }

    class OllamaProvider {
        +create_model(config, kwargs)
    }
    class VLLMProvider {
        +create_model(config, kwargs)
    }
    class GroqProvider {
        +create_model(config, kwargs)
    }
    class AWSBedrockProvider {
        +create_model(config, kwargs)
    }
    class GoogleProvider {
        +create_model(config, kwargs)
    }
    class NVIDIAProvider {
        +create_model(config, kwargs)
    }
    class HuggingFaceProvider {
        +create_model(config, kwargs)
    }
    class LlamaCppProvider {
        +create_model(config, kwargs)
    }
    class OpenRouterProvider {
        +create_model(config, kwargs)
    }

    class LLMClient {
        +get_llm_model() LangChain_LLM
        +llm_model singleton
    }

    BaseLLMProvider <|-- OllamaProvider
    BaseLLMProvider <|-- VLLMProvider
    BaseLLMProvider <|-- GroqProvider
    BaseLLMProvider <|-- AWSBedrockProvider
    BaseLLMProvider <|-- GoogleProvider
    BaseLLMProvider <|-- NVIDIAProvider
    BaseLLMProvider <|-- HuggingFaceProvider
    BaseLLMProvider <|-- LlamaCppProvider
    BaseLLMProvider <|-- OpenRouterProvider

    LLMFactory ..> BaseLLMProvider : instantiates
    LLMClient --> LLMFactory : calls get_provider()
```

---

## 8. Data Model (MongoDB Collections)

Three MongoDB collections in the `ai_chat_app` database. `chat_id` in `chat_messages` is stored
as a string (str(ObjectId)) — not a native ObjectId — matching the pattern in chat_router.py
lines 115 and 139.

![Data Model](diagrams/08-data-model.png)

```mermaid
erDiagram
    users {
        ObjectId _id PK
        string name
        string email UK
        string hashed_password
        list_string role
        string otp
        datetime otp_expiry
    }

    chats {
        ObjectId _id PK
        string user_id FK
        string title
        int message_count
        string created_at
        string updated_at
    }

    chat_messages {
        ObjectId _id PK
        string chat_id FK
        string user
        string assistant
        int input_tokens
        int output_tokens
        float response_time
        string created_at
        int seq
    }

    users ||--o{ chats : "owns (user_id)"
    chats ||--o{ chat_messages : "contains (chat_id)"
```

---

## 9. Deployment Topology

Shows both runtime modes — Development (Uvicorn single-process with `--reload`) and Production
(Gunicorn managing 2 UvicornWorkers) — and how each tier connects to MongoDB, LLM APIs, and
external services.

![Deployment Topology](diagrams/09-deployment-topology.png)

```mermaid
graph TB
    subgraph Client["Client Tier"]
        Browser["Browser / Frontend App"]
    end

    subgraph DevMode["Development Mode — python main.py dev"]
        UV["Uvicorn\n--reload --host 0.0.0.0 --port 45001"]
        APP_DEV["FastAPI app\nSingle process"]
        UV --> APP_DEV
    end

    subgraph ProdMode["Production Mode — python main.py"]
        GUN["Gunicorn\nProcess Manager\n-w 2 -k UvicornWorker"]
        W1["UvicornWorker 1\nFastAPI app"]
        W2["UvicornWorker 2\nFastAPI app"]
        GUN --> W1
        GUN --> W2
    end

    subgraph DataTier["Data Tier"]
        MONGO[("MongoDB\nlocalhost:27017\nDB: ai_chat_app")]
    end

    subgraph ExternalServices["External Services"]
        LLM_API["LLM APIs\nGroq / AWS Bedrock / Google\nNVIDIA / HuggingFace / OpenRouter"]
        LOCAL_LLM["Local LLM\nOllama (localhost:11434)\nvLLM / llama.cpp"]
        DDGS_SVC["DuckDuckGo Search\nPublic API (no key)"]
        SMTP_SVC["Gmail SMTP\nsmtp.gmail.com:587"]
    end

    Browser -- "HTTP / SSE" --> DevMode
    Browser -- "HTTP / SSE" --> ProdMode

    APP_DEV --> MONGO
    APP_DEV --> LLM_API
    APP_DEV --> LOCAL_LLM
    APP_DEV --> DDGS_SVC
    APP_DEV --> SMTP_SVC

    W1 --> MONGO
    W2 --> MONGO
    W1 --> LLM_API
    W2 --> LLM_API
    W1 --> LOCAL_LLM
    W2 --> LOCAL_LLM
    W1 --> DDGS_SVC
    W2 --> DDGS_SVC
```
