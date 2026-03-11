"""Search, query, and enclosing-scope tool handlers."""

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from ..di import get_container
from .ast_operations import get_enclosing_scope_for_path
from .search import query_code, search_text


def register_search_tools(mcp_server: FastMCP) -> None:
    """Register search and query tools."""

    @mcp_server.tool()
    def find_text(
        project: str,
        pattern: str,
        file_pattern: Optional[str] = None,
        max_results: int = 100,
        case_sensitive: bool = False,
        whole_word: bool = False,
        use_regex: bool = False,
        context_lines: int = 2,
    ) -> List[Dict[str, Any]]:
        """Search for text pattern in project files.

        Args:
            project: Project name
            pattern: Text pattern to search for
            file_pattern: Optional glob pattern (e.g., "**/*.py")
            max_results: Maximum number of results
            case_sensitive: Whether to do case-sensitive matching
            whole_word: Whether to match whole words only
            use_regex: Whether to treat pattern as a regular expression
            context_lines: Number of context lines to include

        Returns:
            List of matches with file, line number, and text
        """
        container = get_container()
        config = container.config_manager.get_config()
        return search_text(
            container.project_registry.get_project(project),
            pattern,
            file_pattern,
            max_results if max_results is not None else config.max_results_default,
            case_sensitive,
            whole_word,
            use_regex,
            context_lines,
        )

    @mcp_server.tool()
    def get_enclosing_scope(
        project: str,
        file_path: str,
        row: int,
        column: int,
        label: Optional[str] = None,
        max_lines: int = 0,
    ) -> Dict[str, Any]:
        """Find the enclosing scope (function, class, or module) for a position.

        Args:
            project: Project name
            file_path: Path to the file
            row: Line number (0-based)
            column: Column number (0-based)
            label: Optional text label at the position (e.g., variable name)
            max_lines: Maximum number of lines to return (0 = no limit). When exceeded,
                      returns a centered window around the target row with truncation markers.

        Returns:
            Information about the enclosing scope, including type, name, and range
            Empty if no scope found (e.g., point outside valid code)
        """
        container = get_container()
        project_obj = container.project_registry.get_project(project)
        return get_enclosing_scope_for_path(
            project_obj,
            file_path,
            row,
            column,
            label if label is not None else "",
            container.language_registry,
            container.tree_cache,
            max_lines,
        )

    @mcp_server.tool()
    def run_query(
        project: str,
        query: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """Run a tree-sitter query on project files.

        Args:
            project: Project name
            query: Tree-sitter query string
            file_path: Optional specific file to query
            language: Language to use (required if file_path not provided)
            max_results: Maximum number of results

        Returns:
            List of query matches
        """
        container = get_container()
        config = container.config_manager.get_config()
        return query_code(
            container.project_registry.get_project(project),
            query,
            container.language_registry,
            container.tree_cache,
            file_path,
            language,
            max_results if max_results is not None else config.max_results_default,
        )

    @mcp_server.tool()
    def get_query_template_tool(language: str, template_name: str) -> Dict[str, Any]:
        """Get a predefined tree-sitter query template.

        Args:
            language: Language name
            template_name: Template name (e.g., "functions", "classes")

        Returns:
            Query template information
        """
        from ..language.query_templates import get_query_template

        template = get_query_template(language, template_name)
        if not template:
            raise ValueError(f"No template '{template_name}' for language '{language}'")

        return {
            "language": language,
            "name": template_name,
            "query": template,
        }

    @mcp_server.tool()
    def list_query_templates_tool(language: Optional[str] = None) -> Dict[str, Any]:
        """List available query templates.

        Args:
            language: Optional language to filter by

        Returns:
            Available templates
        """
        from ..language.query_templates import list_query_templates

        return list_query_templates(language)

    @mcp_server.tool()
    def build_query(language: str, patterns: List[str], combine: str = "or") -> Dict[str, str]:
        """Build a tree-sitter query from templates or patterns.

        Args:
            language: Language name
            patterns: List of template names or custom patterns
            combine: How to combine patterns ("or" or "and")

        Returns:
            Combined query
        """
        from .query_builder import build_compound_query

        query = build_compound_query(language, patterns, combine)
        return {
            "language": language,
            "query": query,
        }

    @mcp_server.tool()
    def adapt_query(query: str, from_language: str, to_language: str) -> Dict[str, str]:
        """Adapt a query from one language to another.

        Args:
            query: Original query string
            from_language: Source language
            to_language: Target language

        Returns:
            Adapted query
        """
        from .query_builder import adapt_query_for_language

        adapted = adapt_query_for_language(query, from_language, to_language)
        return {
            "original_language": from_language,
            "target_language": to_language,
            "original_query": query,
            "adapted_query": adapted,
        }

    @mcp_server.tool()
    def get_node_types(language: str) -> Dict[str, str]:
        """Get descriptions of common node types for a language.

        Args:
            language: Language name

        Returns:
            Dictionary of node types and descriptions
        """
        from .query_builder import describe_node_types

        return describe_node_types(language)
