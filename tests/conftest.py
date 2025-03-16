"""Pytest configuration for mcp-server-tree-sitter tests."""

# Import and register the diagnostic plugin
pytest_plugins = ["mcp_server_tree_sitter.testing.pytest_diagnostic"]
