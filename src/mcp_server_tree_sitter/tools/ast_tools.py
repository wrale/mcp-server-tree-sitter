"""AST and node-at-position tool handlers."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..api import get_config, get_language_registry, get_project_registry, get_tree_cache
from ..models.ast import node_to_dict
from .ast_operations import find_node_at_position, get_file_ast
from .ast_operations import parse_file as parse_file_helper


def register_ast_tools(mcp_server: FastMCP) -> None:
    """Register AST tools."""

    @mcp_server.tool()
    def get_ast(
        project: str,
        path: str,
        max_depth: int | None = None,
        include_text: bool = True,
    ) -> dict[str, Any]:
        """Get abstract syntax tree for a file.

        Args:
            project: Name of the registered project.
            path: File path relative to project root.
            max_depth: Maximum tree depth. Defaults to None (use server config, typically 5).
            include_text: Whether to include node text. Defaults to True.

        Returns:
            Nested dict with type, text, children, range (up to max_depth).

        Raises:
            ProjectError: If project is not registered.
            ValueError: If language cannot be detected for path.
        """
        config = get_config()
        depth = max_depth or config.language.default_max_depth
        return get_file_ast(
            get_project_registry().get_project(project),
            path,
            get_language_registry(),
            get_tree_cache(),
            max_depth=depth,
            include_text=include_text,
        )

    @mcp_server.tool()
    def get_node_at_position(project: str, path: str, row: int, column: int) -> dict[str, Any] | None:
        """Get the AST node at a given position. Row and column are 0-based.

        Args:
            project: Name of the registered project.
            path: File path relative to project root.
            row: Line number (0-based).
            column: Column number (0-based).

        Returns:
            Dict with node type, text, range (and children to depth 2), or None if no node at position.

        Raises:
            ProjectError: If project is not registered.
            ValueError: If language cannot be detected for path.
        """
        project_obj = get_project_registry().get_project(project)
        file_path = project_obj.get_file_path(path)
        language_registry = get_language_registry()
        tree_cache = get_tree_cache()

        language = language_registry.language_for_file(path)
        if not language:
            raise ValueError(f"Could not detect language for {path}")

        tree, source_bytes = parse_file_helper(file_path, language, language_registry, tree_cache)

        node = find_node_at_position(tree.root_node, row, column)
        if node:
            return node_to_dict(node, source_bytes, max_depth=2)

        return None
