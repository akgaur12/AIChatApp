# 🤖 AIChatApp

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0%2B-009688.svg?style=flat&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Motor-47A248?style=flat&logo=mongodb&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat&logo=langchain&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat&logo=langgraph&logoColor=white)
![uv](https://img.shields.io/badge/uv-0.5.0%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 📖 Overview

**AIChatApp** is a robust, production-ready AI Chat application backend built with **FastAPI**. It provides a scalable architecture for handling real-time AI conversations and web searches, integrating with multiple Large Language Model (LLM) providers such as **Ollama**, **vLLM**, **AWS Bedrock**, and **Groq**.

Designed for performance and flexibility, it features asynchronous database operations with **MongoDB**, secure JWT authentication, and a modular architecture suitable for rapid development and deployment.

---

## ✨ Key Features

-   **🤖 Chat & Web Search**: Real-time AI chat with web search capabilities.
-   **🚀 High Performance**: Built on FastAPI with asynchronous support for high concurrency.
-   **🔐 Secure Authentication**: Full user authentication system using JWT (JSON Web Tokens) with Forgot Password (OTP) functionality.
-   **🧠 Multi-LLM Support**: Seamlessly switch between different LLM providers (Ollama, vLLM, AWS Bedrock, Groq) via configuration.
-   **💾 Persistent History**: Stores user conversations and chat history in MongoDB using Motor (Async Driver).
-   **⚙️ Configurable**: extensive configuration via `config.yml` and environment variables.
-   **🐳 Production Ready**: specific entry points for Development (Uvicorn with reload) and Production (Gunicorn managed Uvicorn workers).
-   **🔍 Logging**: Comprehensive logging structure with rotating file handlers.

---

## 🛠️ Tech Stack

-   **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
-   **Server**: [Uvicorn](https://www.uvicorn.org/) (Dev), [Gunicorn](https://gunicorn.org/) (Prod)
-   **Database**: [MongoDB](https://motor.readthedocs.io/en/stable/) (Async Motor Driver)
-   **Dependency & project manager**: [uv](https://docs.astral.sh/uv/)
-   **Authentication**: [Python-jose (JWT)](https://python-jose.readthedocs.io/en/latest/), [Passlib (Hashing)](https://pypi.org/project/passlib/)
-   **Configuration**: [PyYAML](https://pypi.org/project/PyYAML/), [DotEnv](https://pypi.org/project/python-dotenv/)
-   **Web Search**: [ddgs](https://pypi.org/project/duckduckgo-search/)
-   **AI Framework**: [LangChain](https://python.langchain.com/), [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview)
-   **LLM Providers**: [Ollama](https://ollama.com/), [vLLM](https://github.com/vllm-project/vllm), [AWS Bedrock](https://aws.amazon.com/bedrock/), [Groq](https://console.groq.com/docs/models)

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed on your system:

-   **Python 3.12+**
-   **MongoDB** (Running locally or accessible remotely)
-   **Git**

### Installation

1.  **Clone the Repository**

    ```bash
    git clone https://github.com/akgaur12/AIChatApp.git
    cd AIChatApp
    ```

2.  **Create a Virtual Environment**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies**

    Using `pip` with `pyproject.toml`:
    ```bash
    pip install -e .
    ```
    *Or if you are using `uv`:*
    ```bash
    uv sync
    ```

### ⚙️ Configuration

The application uses a combination of `config.yml` and environment variables.

1.  **Environment Variables**: Create a `.env` file in the root directory for sensitive secrets.
    ```env
    # JWT Secret Key
    JWT_SECRET_KEY = "your-32-character-secret-key"

    # AWS Credentials
    AWS_ACCESS_KEY_ID = "your-aws-access-key-id"
    AWS_SECRET_ACCESS_KEY = "your-aws-secret-access-key"

    # GROQ API Key
    GROQ_API_KEY = "your-groq-api-key"

    # NVIDIA API Key
    NVIDIA_API_KEY = "your-nvidia-api-key"

    # Google API Key
    GOOGLE_API_KEY = "your-google-api-key"

    # HuggingFace Access Token
    HUGGINGFACEHUB_API_TOKEN = "your-huggingface-api-token"

    # Email Credentials
    SENDER_EMAIL = "your-email@gmail.com"
    SENDER_PASSWORD = "your-16-character-app-specific-password"
    ```

    *Note: Replace the values with your actual credentials.*
    
    - For GROQ API Key, follow this link: [Generate GROQ API Key](https://console.groq.com/docs/models)
    - For NVIDIA API Key, follow this link: [Generate NVIDIA API Key](https://build.nvidia.com/)
    - For Google API Key, follow this link: [Generate Google API Key](https://ai.google.dev/gemini-api/docs/api-key)
    - For Hugging Face API Key, follow this link: [Generate Hugging Face API Key](https://huggingface.co/docs/hub/security-tokens)
    - For AWS Security Credentials, follow this link: [AWS security credentials](https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html)
    - For generating app-specific password (Gmail), follow this link: [Generate App-Specific Password](https://support.google.com/accounts/answer/185833?hl=en)
   
2.  **Application Config**: Edit `src/config/config.yml` to adjust server settings, logging, and LLM providers.
    ```yaml
    FastAPI:
      HOST: "0.0.0.0"
      PORT: "45001"
      WORKERS: "2"
    
    LLM:
      Provider: "ollama" # Change to "groq", "vllm", etc.
    ```
---

## 🏃‍♂️ Running the Application

The application handles both Development and Production modes via a single entry point `main.py`.

### Development Mode
Runs with hot-reloading enabled.

```bash
python main.py dev

    or

uv run start dev

    or

source .venv/bin/activate
start dev
```

### Production Mode
Runs with Gunicorn process manager and Uvicorn workers for stability and performance.

```bash
python main.py

    or 

uv run start

    or

source .venv/bin/activate
start
```

*Note: Ensure your MongoDB instance is running before starting the application.*

---

## 🧪 Testing

The project includes a comprehensive test suite using `pytest`.

To run the tests:

```bash
pytest -v
```

---

## 📚 API Documentation

Once the server is running, you can access the interactive API documentation:

-   **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
-   **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

These interfaces allow you to test endpoints directly from your browser.

---

## 📂 Project Structure

```plaintext
AIChatApp/
├── .venv/                      # Virtual Environment
├── logs/                       # Application Logs
├── scripts/                    # Utility scripts
├── tests/                      # Testing files
├── src/
│   ├── api_router/             # API Route definitions (Chat, User)
│   |   ├── chat_router.py      # Chat API Router
│   |   └── user_router.py      # User API Router
│   ├── config/                 # Configuration files
│   |   └── config.yml          # Configuration file
|   |   └── logging.yaml        # Logging Config File
│   ├── pipelines/              # AI/LLM Processing Pipelines
|   |   ├── builder.py          # Pipeline builder
|   |   ├── nodes.py            # Pipeline nodes
|   |   └── pipeline_state.py   # Pipeline state
│   ├── Prompts/                # Prompt templates
│   ├── services/               # Business Logic Services
|   |   └── models.py           # llm models interface 
│   ├── database.py             # Database Connection Logic
│   ├── deps.py                 # Dependency Injection
│   ├── lifespan.py             # App Lifecycle Manager
│   ├── schemas.py              # Pydantic Models
│   └── utils.py                # Utility Functions
├── .env                        # Environment Variables
├── .gitattributes              # Git Attributes
├── .gitignore                  # Git Ignore
├── .python-version             # Python Version
├── main.py                     # Application Entry Point
├── pyproject.toml              # Project Dependencies & Metadata
├── README.md                   # Project Documentation
└── uv.lock                     # uv lock file
└── LICENSE                     # Project License
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.
