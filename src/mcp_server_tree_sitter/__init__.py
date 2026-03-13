"""MCP Server for Tree-sitter - Code analysis capabilities using tree-sitter.

This module provides a Model Context Protocol server that gives LLMs like Claude
intelligent access to codebases with appropriate context management.
"""

# Import bootstrap package first to ensure core services are set up
# before any other modules are imported
from . import bootstrap as bootstrap

# Logging is now configured via the bootstrap.logging_bootstrap module
# The bootstrap module automatically calls configure_root_logger() when imported

def _get_version() -> str:
    """Return package version from metadata (single source of truth: pyproject.toml)."""
    try:
        from importlib.metadata import version
        return version("mcp-server-tree-sitter")
    except Exception:
        return "0.0.0+unknown"


__version__ = _get_version()
