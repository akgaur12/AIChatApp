
import logging
import logging.config
import logging.handlers
import os
import yaml


# Custom Filter for Exact Level Matching
class ExactLevelFilter(logging.Filter):
    def __init__(self, level: int):
        super().__init__()   # good practice
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self.level


def setup_logging(config_path: str = "src/config/logging.yaml"):
    os.makedirs("logs", exist_ok=True)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    logging.config.dictConfig(config)