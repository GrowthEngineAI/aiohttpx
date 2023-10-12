import os
import logging
from typing import Optional

_logger: Optional[logging.Logger] = None
_muted_httpx: Optional[bool] = None

def get_logger(level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    """
    global _logger
    if _logger is not None:
        return _logger
    if level is None: level = os.getenv("LOGGER_LEVEL", os.getenv("LOG_LEVEL", "INFO"))
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s: %(message)s", "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(handler)
        # logger.propagate = False
    return logger

def mute_httpx_logger() -> None:
    """
    Mute the httpx logger.
    """
    global _muted_httpx
    if _muted_httpx is not None:
        return
    _muted_httpx = True
    logging.getLogger("httpx").setLevel(logging.WARNING)


logger: logging.Logger = get_logger()