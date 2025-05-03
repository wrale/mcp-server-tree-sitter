"""Logging configuration for MCP Tree-sitter Server.

This module is maintained for backwards compatibility.
All functionality has been moved to the bootstrap.logging_bootstrap module,
which is the canonical source for logging configuration.

All imports from this module should be updated to use:
    from mcp_server_tree_sitter.bootstrap import get_logger, update_log_levels
"""

# Import the bootstrap module's logging components to maintain backwards compatibility
from .bootstrap.logging_bootstrap import (
    LOG_LEVEL_MAP,
    configure_root_logger,
    get_log_level_from_env,
    get_logger,
    update_log_levels,
)

# Re-export all the functions and constants for backwards compatibility
__all__ = ["LOG_LEVEL_MAP", "configure_root_logger", "get_log_level_from_env", "get_logger", "update_log_levels"]

# The bootstrap module already calls configure_root_logger() when imported,
# so we don't need to call it again here.
