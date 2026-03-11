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
        """Extract symbols from a file.

        Args:
            project: Project name
            file_path: Path to the file
            symbol_types: Types of symbols to extract (functions, classes, imports, etc.)

        Returns:
            Dictionary of symbols by type
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
        """Analyze overall project structure.

        Args:
            project: Project name
            scan_depth: Depth of detailed analysis (higher is slower)
            ctx: Optional MCP context for progress reporting

        Returns:
            Project analysis
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
        """Find dependencies of a file.

        Args:
            project: Project name
            file_path: Path to the file

        Returns:
            Dictionary of imports/includes
        """
        app = get_app()
        return find_dependencies(
            app.project_registry.get_project(project),
            file_path,
            app.language_registry,
        )

    @mcp_server.tool()
    def analyze_complexity(project: str, file_path: str) -> ComplexityResult:
        """Analyze code complexity.

        Args:
            project: Project name
            file_path: Path to the file

        Returns:
            Complexity metrics
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
        """Find similar code to a snippet.

        Args:
            project: Project name
            snippet: Code snippet to find
            language: Language of the snippet
            threshold: Similarity threshold (0.0-1.0)
            max_results: Maximum number of results

        Returns:
            List of similar code locations
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
        """Find usage of a symbol.

        Args:
            project: Project name
            symbol: Symbol name to find
            file_path: Optional file to look in (for local symbols)
            language: Language to search in

        Returns:
            List of usage locations
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
