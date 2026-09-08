"""
Logging configuration and request context helpers for Recoll Modern UI.
"""

import logging
import os
import sys
from typing import Dict
import bottle

LOG_LEVEL_MAP: Dict[str, int] = {
    'ERROR': logging.ERROR,
    'WARN': logging.WARNING,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'AUDIT': logging.INFO,
    'DEBUG': logging.DEBUG,
}


def get_configured_log_level() -> int:
    """
    Resolve logging level integer from RECOLL_LOGLEVEL environment variable.
    Defaults to logging.INFO.
    """
    env_level = os.environ.get('RECOLL_LOGLEVEL', 'INFO').strip().upper()
    return LOG_LEVEL_MAP.get(env_level, logging.INFO)


def setup_logging(level: int = None) -> logging.Logger:
    """
    Initialize system-wide logging with standardized timestamps and formatting.
    """
    target_level = level if level is not None else get_configured_log_level()
    logging.basicConfig(
        level=target_level,
        format='%(asctime)s [%(levelname)s] [RecollWeb] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout,
        force=True,
    )
    log = logging.getLogger("recoll.webui")
    log.setLevel(target_level)
    return log


# Default logger instance
logger = setup_logging()


def get_client_ip() -> str:
    """
    Extract client IP address from reverse proxy headers (X-Forwarded-For, X-Real-IP)
    or fall back to the remote socket address.
    """
    for header in ('X-Forwarded-For', 'X-Real-IP'):
        val = bottle.request.headers.get(header)
        if val:
            return val.split(',')[0].strip()
    return bottle.request.environ.get('REMOTE_ADDR') or '127.0.0.1'
