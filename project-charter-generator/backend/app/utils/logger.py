import logging
import os
import sys

def get_logger(name: str):
    """
    Returns a logger with consistent formatting.
    - Configurable via LOG_LEVEL env var (DEBUG/INFO/WARNING/ERROR).
    - Writes to stdout to be container-friendly.
    - Avoids duplicate propagation.
    """
    logger = logging.getLogger(name)

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
