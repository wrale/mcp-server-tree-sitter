"""Search, query, and enclosing-scope tool handlers."""

from mcp.server.fastmcp import FastMCP

from ..app import get_app
from .ast_operations import get_enclosing_scope_for_path
from .search import QueryMatchResult, TextMatchResult, query_code, search_text


def register_search_tools(mcp_server: FastMCP) -> None:
    """Register search and query tools."""

    @mcp_server.tool()
    def find_text(
        project: str,
        pattern: str,
        file_pattern: str | None = None,
        max_results: int = 100,
        case_sensitive: bool = False,
        whole_word: bool = False,
        use_regex: bool = False,
        context_lines: int = 2,
    ) -> list[TextMatchResult]:
        """Search for text pattern in project files.

        Args:
            project: Name of the registered project.
            pattern: Text pattern to search for.
            file_pattern: Glob to restrict files (e.g. '**/*.py'). Defaults to None (all files).
            max_results: Maximum number of results. Defaults to 100 (or config max_results_default).
            case_sensitive: Case-sensitive matching. Defaults to False.
            whole_word: Match whole words only. Defaults to False.
            use_regex: Treat pattern as regex. Defaults to False.
            context_lines: Context lines per match. Defaults to 2.

        Returns:
            List of match objects (path, line_number, line_text, matches, etc.).

        Raises:
            ProjectError: If project is not registered.
        """
        app = get_app()
        config = app.config_manager.get_config()
        return search_text(
            app.project_registry.get_project(project),
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
        label: str | None = None,
        max_lines: int = 0,
    ) -> dict[str, object]:
        """Find enclosing scope (function, class, or module) at position. Row and column are 0-based.

        Args:
            project: Name of the registered project.
            file_path: Path to the file relative to project root.
            row: Line number (0-based).
            column: Column number (0-based).
            label: Optional label at position (e.g. variable name). Defaults to None.
            max_lines: Max lines for snippet; 0 means no limit. Defaults to 0.
                If scope is larger, returns truncated snippet when max_lines > 0.

        Returns:
            Dict with type, name, range (and optional snippet). Empty dict if no scope at position.

        Raises:
            ProjectError: If project is not registered.
            ValueError: If language cannot be detected for file.
        """
        app = get_app()
        project_obj = app.project_registry.get_project(project)
        return get_enclosing_scope_for_path(
            project_obj,
            file_path,
            row,
            column,
            label if label is not None else "",
            app.language_registry,
            app.tree_cache,
            max_lines,
        )

    @mcp_server.tool()
    def run_query(
        project: str,
        query: str,
        file_path: str | None = None,
        language: str | None = None,
        max_results: int = 100,
    ) -> list[QueryMatchResult]:
        """Run a tree-sitter query on project files. Provide file_path (single file) or language (all matching files).

        Args:
            project: Name of the registered project.
            query: Tree-sitter query string.
            file_path: Optional single file to query. Defaults to None.
            language: Language when querying multiple files. Defaults to None.
                Either file_path or language must be set when not querying a single file.
            max_results: Maximum number of results. Defaults to 100 (or config max_results_default).

        Returns:
            List of query match objects (captures, path, range).

        Raises:
            ProjectError: If project is not registered.
            ValueError: If neither file_path nor language provided when required.
        """
        app = get_app()
        config = app.config_manager.get_config()
        return query_code(
            app.project_registry.get_project(project),
            query,
            app.language_registry,
            app.tree_cache,
            file_path,
            language,
            max_results if max_results is not None else config.max_results_default,
        )

    @mcp_server.tool()
    def get_query_template_tool(language: str, template_name: str) -> dict[str, str]:
        """Get a predefined tree-sitter query template for a language.

        Args:
            language: Language identifier (e.g. 'python', 'javascript').
            template_name: Template name (e.g. 'functions', 'classes').

        Returns:
            Dict with language, name, query (the query string).

        Raises:
            ValueError: If template_name or language is not found.
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
    def list_query_templates_tool(language: str | None = None) -> dict[str, object]:
        """List available query template names.

        Args:
            language: Optional language to filter by. Defaults to None (all languages).

        Returns:
            Dict mapping language (or 'all') to list of template names.
        """
        from ..language.query_templates import list_query_templates

        return list_query_templates(language)

    @mcp_server.tool()
    def build_query(language: str, patterns: list[str], combine: str = "or") -> dict[str, str]:
        """Build a tree-sitter query from template or pattern names.

        Args:
            language: Language identifier.
            patterns: List of template names or custom patterns.
            combine: How to combine patterns. Defaults to 'or'. Use 'and' for conjunction.

        Returns:
            Dict with language and query (the combined query string).
        """
        from .query_builder import build_compound_query

        query = build_compound_query(language, patterns, combine)
        return {
            "language": language,
            "query": query,
        }

    @mcp_server.tool()
    def adapt_query(query: str, from_language: str, to_language: str) -> dict[str, str]:
        """Adapt a tree-sitter query from one language grammar to another.

        Args:
            query: Original query string.
            from_language: Source language identifier.
            to_language: Target language identifier.

        Returns:
            Dict with original_language, target_language, original_query, adapted_query.
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
    def get_node_types(language: str) -> dict[str, str]:
        """Get node type names and short descriptions for a language.

        Args:
            language: Language identifier (e.g. 'python', 'javascript').

        Returns:
            Dict mapping node type name to description string.
        """
        from .query_builder import describe_node_types

        return describe_node_types(language)
