import os, sys, logging, subprocess
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.api_router import chat_router, user_router
from src.utils import load_config
from src.lifespan import lifespan

cfg = load_config(filename="config.yml")

HOST = cfg["FastAPI"]["HOST"]
PORT = cfg["FastAPI"]["PORT"]
WORKERS = cfg["FastAPI"]["WORKERS"]
LOG_LEVEL = cfg["FastAPI"]["LOG_LEVEL"]
TIMEOUT = cfg["FastAPI"]["TIMEOUT"]
GRACEFUL_TIMEOUT = cfg["FastAPI"]["GRACEFUL_TIMEOUT"]

LOG_DIR = cfg["Logging"]["LOG_DIR"]
LOG_FILE_NAME = cfg["Logging"]["LOG_FILE_NAME"]
MAX_FILE_SIZE = cfg["Logging"]["MAX_FILE_SIZE"]
MAX_FILE_COUNT = cfg["Logging"]["MAX_FILE_COUNT"] 
LOG_FORMAT = cfg["Logging"]["LOG_FORMAT"]


# Create logs directory if it does not exist
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout), RotatingFileHandler(LOG_DIR + "/" + LOG_FILE_NAME, maxBytes=MAX_FILE_SIZE, backupCount=MAX_FILE_COUNT)],
)
logger = logging.getLogger(__name__)

# logging.getLogger("httpx").setLevel(logging.WARNING)


# Initialize FastAPI application
app = FastAPI(title="AIChatApp", version="1.0.0", lifespan=lifespan)

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

    cmd = [
        "gunicorn",
        "-w", WORKERS,
        "-k", "uvicorn.workers.UvicornWorker",
        "--timeout", TIMEOUT,
        "--graceful-timeout", GRACEFUL_TIMEOUT,
        "-b", f"{HOST}:{PORT}",
        "main:app",
    ]

    subprocess.run(cmd, check=True)

def main_dev():
    cmd = [
        "uvicorn",
        "main:app",
        "--host", HOST,
        "--port", PORT,
        "--reload",
        "--log-level", LOG_LEVEL,
    ]
    subprocess.run(cmd, check=True)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        logger.info("Starting in development mode")
        main_dev()
    else:
        logger.info("Starting in production mode")
        main_prod()


# Run the server
if __name__ == "__main__":
    main()



