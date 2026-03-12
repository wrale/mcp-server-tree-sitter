"""Analysis tool handlers (symbols, dependencies, complexity, similar code, usage)."""

from typing import cast

from mcp.server.fastmcp import Context, FastMCP

from ..app import get_app
from ..utils.context import MCPContextProtocol
from .analysis import (
    ComplexityResult,
    ProjectStructureResult,
    analyze_code_complexity,
    analyze_project_structure,
    extract_symbols,
    find_dependencies,
)
from .search import QueryMatchResult, TextMatchResult, query_code, search_text


def register_analysis_tools(mcp_server: FastMCP) -> None:
    """Register analysis tools."""

    @mcp_server.tool()
    def get_symbols(
        project: str,
        file_path: str,
        symbol_types: list[str] | None = None,
    ) -> dict[str, list[dict[str, object]]]:
        """Extract symbols (functions, classes, imports, etc.) from a file.

        Args:
            project: Name of the registered project.
            file_path: Path to the file relative to project root.
            symbol_types: Optional filter (e.g. ['functions', 'classes']). Defaults to None (all types).

        Returns:
            Dict mapping symbol type to list of symbol dicts (name, range, etc.).

        Raises:
            ProjectError: If project is not registered.
        """
        app = get_app()
        return extract_symbols(
            app.project_registry.get_project(project),
            file_path,
            app.language_registry,
            symbol_types,
        )

    @mcp_server.tool()
    def analyze_project(
        project: str,
        scan_depth: int = 3,
        ctx: Context | None = None,
    ) -> ProjectStructureResult:
        """Analyze project structure (languages, entry points, build files).

        Args:
            project: Name of the registered project.
            scan_depth: Depth of detailed analysis (higher is slower). Defaults to 3.
            ctx: Optional MCP context for progress reporting. Defaults to None. Omit when calling from LLM.

        Returns:
            ProjectStructureResult with languages, entry_points, build_files, etc.

        Raises:
            ProjectError: If project is not registered.
        """
        app = get_app()
        return analyze_project_structure(
            app.project_registry.get_project(project),
            app.language_registry,
            scan_depth,
            cast(MCPContextProtocol | None, ctx),
        )

    @mcp_server.tool()
    def get_dependencies(project: str, file_path: str) -> dict[str, list[str]]:
        """Get imports/includes for a file (parsed from AST).

        Args:
            project: Name of the registered project.
            file_path: Path to the file relative to project root.

        Returns:
            Dict mapping category (e.g. 'imports') to list of dependency strings.

        Raises:
            ProjectError: If project is not registered.
        """
        app = get_app()
        return find_dependencies(
            app.project_registry.get_project(project),
            file_path,
            app.language_registry,
        )

    @mcp_server.tool()
    def analyze_complexity(project: str, file_path: str) -> ComplexityResult:
        """Compute code complexity metrics for a file.

        Args:
            project: Name of the registered project.
            file_path: Path to the file relative to project root.

        Returns:
            ComplexityResult with line_count, function_count, class_count, cyclomatic_complexity, etc.

        Raises:
            ProjectError: If project is not registered.
        """
        app = get_app()
        return analyze_code_complexity(
            app.project_registry.get_project(project),
            file_path,
            app.language_registry,
        )

    @mcp_server.tool()
    def find_similar_code(
        project: str,
        snippet: str,
        language: str | None = None,
        threshold: float = 0.8,
        max_results: int = 10,
    ) -> list[TextMatchResult]:
        """Find text-similar code to a snippet (substring search).

        Args:
            project: Name of the registered project.
            snippet: Code snippet to find.
            language: Optional language to restrict by extension. Defaults to None (all files).
            threshold: Unused (reserved). Defaults to 0.8.
            max_results: Maximum number of matches. Defaults to 10.

        Returns:
            List of text match objects (path, line_number, line_text, etc.).

        Raises:
            ProjectError: If project is not registered.
        """
        app = get_app()
        clean_snippet = snippet.strip()

        extension_map = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "rust": "rs",
            "go": "go",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "ruby": "rb",
            "swift": "swift",
            "kotlin": "kt",
        }

        extension = extension_map.get(language, language) if language else None
        file_pattern = f"**/*.{extension}" if extension else None

        return search_text(
            app.project_registry.get_project(project),
            clean_snippet,
            file_pattern=file_pattern,
            max_results=max_results,
            case_sensitive=False,
            whole_word=False,
            use_regex=False,
        )

    @mcp_server.tool()
    def find_usage(
        project: str,
        symbol: str,
        file_path: str | None = None,
        language: str | None = None,
    ) -> list[QueryMatchResult]:
        """Find references to a symbol (identifier) in the project.

        Args:
            project: Name of the registered project.
            symbol: Symbol name (identifier) to find.
            file_path: Optional single file to search (e.g. for local symbols). Defaults to None.
            language: Language when searching multiple files. Defaults to None.
                Either file_path or language must be provided.

        Returns:
            List of query match objects (path, captures, range).

        Raises:
            ProjectError: If project is not registered.
            ValueError: If neither file_path nor language is provided.
        """
        app = get_app()
        language_registry = app.language_registry
        if not language and file_path:
            language = language_registry.language_for_file(file_path)

        if not language:
            raise ValueError("Either language or file_path must be provided")

        query = f"""
        (
          (identifier) @reference
          (#eq? @reference "{symbol}")
        )
        """

        return query_code(
            app.project_registry.get_project(project),
            query,
            language_registry,
            app.tree_cache,
            file_path,
            language,
        )
