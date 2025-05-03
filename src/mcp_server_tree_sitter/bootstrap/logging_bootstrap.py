"""Bootstrap module for logging configuration with minimal dependencies.

This module is imported first in the initialization sequence to ensure logging
is configured before any other modules are imported. It has no dependencies
on other modules in the project to avoid import cycles.

This is the CANONICAL implementation of logging configuration. If you need to
modify how logging is configured, make changes here and nowhere else.
"""

import logging
import os
from typing import Dict, Union

# Numeric values corresponding to log level names
LOG_LEVEL_MAP: Dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def get_log_level_from_env() -> int:
    """
    Get log level from environment variable MCP_TS_LOG_LEVEL.

    Returns:
        int: Logging level value (e.g., logging.DEBUG, logging.INFO)
    """
    env_level = os.environ.get("MCP_TS_LOG_LEVEL", "INFO").upper()
    return LOG_LEVEL_MAP.get(env_level, logging.INFO)


def configure_root_logger() -> None:
    """
    Configure the root logger based on environment variables.
    This should be called at the earliest possible point in the application.
    """
    log_level = get_log_level_from_env()

    # Configure the root logger with proper format and level
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Ensure the root logger for our package is also set correctly
    pkg_logger = logging.getLogger("mcp_server_tree_sitter")
    pkg_logger.setLevel(log_level)

    # Ensure all handlers have the correct level
    for handler in logging.root.handlers:
        handler.setLevel(log_level)

    # Ensure propagation is preserved
    pkg_logger.propagate = True


def update_log_levels(level_name: Union[str, int]) -> None:
    """
    Update the root package logger level and synchronize handler levels.

    This function sets the level of the root package logger only. Child loggers
    will inherit this level unless they have their own explicit level settings.
    Handler levels are updated to match their logger's effective level.

    Args:
        level_name: Log level name (DEBUG, INFO, etc.) or numeric value
    """
    # Convert string level name to numeric value if needed
    if isinstance(level_name, str):
        level_value = LOG_LEVEL_MAP.get(level_name.upper(), logging.INFO)
    else:
        level_value = level_name

    # Update ONLY the root package logger level
    pkg_logger = logging.getLogger("mcp_server_tree_sitter")
    pkg_logger.setLevel(level_value)

    # Update all handlers on the root package logger
    for handler in pkg_logger.handlers:
        handler.setLevel(level_value)

    # Synchronize handler levels with their logger's effective level
    # for all existing loggers in our package hierarchy
    for name in logging.root.manager.loggerDict:
        if name == "mcp_server_tree_sitter" or name.startswith("mcp_server_tree_sitter."):
            logger = logging.getLogger(name)

            # DO NOT set the logger's level explicitly to maintain hierarchy
            # Only synchronize handler levels with the logger's effective level
            for handler in logger.handlers:
                handler.setLevel(logger.getEffectiveLevel())

            # Ensure propagation is preserved
            logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a properly configured logger with appropriate level.

    Args:
        name: Logger name, typically __name__

    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)

    # Only set level explicitly for the root package logger
    # Child loggers will inherit levels as needed
    if name == "mcp_server_tree_sitter":
        log_level = get_log_level_from_env()
        logger.setLevel(log_level)

        # Ensure all handlers have the correct level
        for handler in logger.handlers:
            handler.setLevel(log_level)
    else:
        # For child loggers, ensure handlers match their effective level
        # without setting the logger level explicitly
        effective_level = logger.getEffectiveLevel()
        for handler in logger.handlers:
            handler.setLevel(effective_level)

        # Ensure propagation is enabled
        logger.propagate = True

    return logger


# Run the root logger configuration when this module is imported
configure_root_logger()
