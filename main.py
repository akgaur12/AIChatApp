import os, sys, logging, subprocess
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.api_router import chat_router, user_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("app.log")],
)
logger = logging.getLogger(__name__)


# Initialize FastAPI application
app = FastAPI(title="AIChatApp", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,           # Middleware to handle Cross-Origin Resource Sharing (CORS). CORS controls which frontend domains (origins) are allowed to call your backend APIs.
    allow_origins=["*"],      # Allows requests from any origin (any domain).
    allow_credentials=True,   # Allows sending cookies, authorization headers, or tokens (like JWT).
    allow_methods=["*"],      # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.).
    allow_headers=["*"],      # Allows all headers (like Content-Type, Authorization, etc.) This is important for: JWT auth, Streaming responses, LLM metadata headers
)

# Include API routers
app.include_router(chat_router.router)
app.include_router(user_router.router)



# Entry points for running the application in production or development mode
def main_prod():
    workers = 2

    cmd = [
        "gunicorn",
        "-w", str(workers),
        "-k", "uvicorn.workers.UvicornWorker",
        "--timeout", "240",
        "--graceful-timeout", "60",
        "-b", "0.0.0.0:8000",
        "main:app",
    ]

    subprocess.run(cmd, check=True)

def main_dev():
    cmd = [
        "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
        "--log-level", "debug",
    ]
    subprocess.run(cmd, check=True)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        main_dev()
    else:
        main_prod()


# Run the server
if __name__ == "__main__":
    main()



