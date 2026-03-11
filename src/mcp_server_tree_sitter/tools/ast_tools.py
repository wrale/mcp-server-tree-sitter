"""AST and node-at-position tool handlers."""

from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from ..app import get_app
from ..models.ast import node_to_dict
from .ast_operations import find_node_at_position, get_file_ast
from .ast_operations import parse_file as parse_file_helper


def register_ast_tools(mcp_server: FastMCP) -> None:
    """Register AST tools."""

    @mcp_server.tool()
    def get_ast(
        project: str,
        path: str,
        max_depth: Optional[int] = None,
        include_text: bool = True,
    ) -> Dict[str, Any]:
        """Get abstract syntax tree for a file.

        Args:
            project: Project name
            path: File path relative to project root
            max_depth: Maximum depth of the tree (default: 5)
            include_text: Whether to include node text

        Returns:
            AST as a nested dictionary
        """
        app = get_app()
        config = app.config_manager.get_config()
        depth = max_depth or config.language.default_max_depth
        return get_file_ast(
            app.project_registry.get_project(project),
            path,
            app.language_registry,
            app.tree_cache,
            max_depth=depth,
            include_text=include_text,
        )

    @mcp_server.tool()
    def get_node_at_position(project: str, path: str, row: int, column: int) -> Optional[Dict[str, Any]]:
        """Find the AST node at a specific position.

        Args:
            project: Project name
            path: File path relative to project root
            row: Line number (0-based)
            column: Column number (0-based)

        Returns:
            Node information or None if not found
        """
        app = get_app()
        project_obj = app.project_registry.get_project(project)
        file_path = project_obj.get_file_path(path)
        language_registry = app.language_registry
        tree_cache = app.tree_cache

        language = language_registry.language_for_file(path)
        if not language:
            raise ValueError(f"Could not detect language for {path}")

        tree, source_bytes = parse_file_helper(file_path, language, language_registry, tree_cache)

        node = find_node_at_position(tree.root_node, row, column)
        if node:
            return node_to_dict(node, source_bytes, max_depth=2)

        return None
