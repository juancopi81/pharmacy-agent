"""Structured logging configuration."""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure structured logging for the application.

    Args:
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Check if a StreamHandler to stdout already exists to avoid duplicates
    handler_exists = any(
        isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
        for h in root_logger.handlers
    )

    if not handler_exists:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        root_logger.addHandler(handler)

    logger = logging.getLogger("pharmacy_agent")
    logger.setLevel(level)

    return logger


def get_logger(name: str = "pharmacy_agent") -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
