"""Bootstrap package for early initialization dependencies.

This package contains modules that should be imported and initialized before
any other modules in the project to ensure proper setup of core services.
"""

# Import logging bootstrap module to ensure it's available
from . import logging_bootstrap

# Export key functions for convenience
from .logging_bootstrap import get_log_level_from_env, get_logger, update_log_levels

__all__ = ["get_logger", "update_log_levels", "get_log_level_from_env", "logging_bootstrap"]
