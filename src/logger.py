import os, sys, logging
from logging.handlers import RotatingFileHandler
from src.utils import cfg

# Configuration extraction
LOG_DIR = cfg["Logging"]["LOG_DIR"]
DEBUG_LOG_FILE_NAME = cfg["Logging"]["DEBUG_LOG_FILE_NAME"]
INFO_LOG_FILE_NAME = cfg["Logging"]["INFO_LOG_FILE_NAME"]
WARNING_LOG_FILE_NAME = cfg["Logging"]["WARNING_LOG_FILE_NAME"]
ERROR_LOG_FILE_NAME = cfg["Logging"]["ERROR_LOG_FILE_NAME"]
MAX_FILE_SIZE = cfg["Logging"]["MAX_FILE_SIZE"]
MAX_FILE_COUNT = cfg["Logging"]["MAX_FILE_COUNT"] 
LOG_FORMAT = cfg["Logging"]["LOG_FORMAT"]
LOG_LEVEL = cfg["Logging"]["LOG_LEVEL"]

# Custom Filter for Exact Level Matching
class ExactLevelFilter(logging.Filter):
    def __init__(self, level: int):
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self.level

def setup_logging():
    # Ensure logs directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Determine log level
    root_level = logging.DEBUG if str(LOG_LEVEL).lower() == "debug" else logging.INFO

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(root_level)
    
    # Clear existing handlers to prevent duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # -------- DEBUG (Exact) --------
    # Only attach debug handler if we include debug logs
    if root_level == logging.DEBUG:
        debug_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, DEBUG_LOG_FILE_NAME), 
            maxBytes=MAX_FILE_SIZE, 
            backupCount=MAX_FILE_COUNT
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.addFilter(ExactLevelFilter(logging.DEBUG))
        debug_handler.setFormatter(formatter)
        root_logger.addHandler(debug_handler)

    # -------- INFO (Exact) --------
    info_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, INFO_LOG_FILE_NAME), 
        maxBytes=MAX_FILE_SIZE, 
        backupCount=MAX_FILE_COUNT
    )
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(ExactLevelFilter(logging.INFO))
    info_handler.setFormatter(formatter)

    # -------- WARNING (Exact) --------
    warning_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, WARNING_LOG_FILE_NAME), 
        maxBytes=MAX_FILE_SIZE, 
        backupCount=MAX_FILE_COUNT
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.addFilter(ExactLevelFilter(logging.WARNING))
    warning_handler.setFormatter(formatter)

    # -------- ERROR & CRITICAL (Inclusive) --------
    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, ERROR_LOG_FILE_NAME), 
        maxBytes=MAX_FILE_SIZE, 
        backupCount=MAX_FILE_COUNT
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # -------- STREAM (Console) --------
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(root_level) # Match the root level configuration
    stream_handler.setFormatter(formatter)

    # Attach handlers
    root_logger.addHandler(info_handler)
    root_logger.addHandler(warning_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(stream_handler)
