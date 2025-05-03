"""MCP Server for Tree-sitter - Code analysis capabilities using tree-sitter.

This module provides a Model Context Protocol server that gives LLMs like Claude
intelligent access to codebases with appropriate context management.
"""

# Import bootstrap package first to ensure core services are set up
# before any other modules are imported
from . import bootstrap as bootstrap  # noqa: F401 - Import needed for initialization

# Logging is now configured via the bootstrap.logging_bootstrap module
# The bootstrap module automatically calls configure_root_logger() when imported

__version__ = "0.1.0"
