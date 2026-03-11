"""Analysis tool handlers (symbols, dependencies, complexity, similar code, usage)."""

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from ..di import get_container
from ..utils.context.mcp_context import MCPContextProtocol
from .analysis import (
    analyze_code_complexity,
    analyze_project_structure,
    extract_symbols,
    find_dependencies,
)
from .search import query_code, search_text


def register_analysis_tools(mcp_server: FastMCP) -> None:
    """Register analysis tools."""

    @mcp_server.tool()
    def get_symbols(
        project: str,
        file_path: str,
        symbol_types: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract symbols from a file.

        Args:
            project: Project name
            file_path: Path to the file
            symbol_types: Types of symbols to extract (functions, classes, imports, etc.)

        Returns:
            Dictionary of symbols by type
        """
        container = get_container()
        return extract_symbols(
            container.project_registry.get_project(project),
            file_path,
            container.language_registry,
            symbol_types,
        )

    @mcp_server.tool()
    def analyze_project(
        project: str,
        scan_depth: int = 3,
        ctx: Optional[MCPContextProtocol] = None,
    ) -> Dict[str, Any]:
        """Analyze overall project structure.

        Args:
            project: Project name
            scan_depth: Depth of detailed analysis (higher is slower)
            ctx: Optional MCP context for progress reporting

        Returns:
            Project analysis
        """
        container = get_container()
        return analyze_project_structure(
            container.project_registry.get_project(project),
            container.language_registry,
            scan_depth,
            ctx,
        )

    @mcp_server.tool()
    def get_dependencies(project: str, file_path: str) -> Dict[str, List[str]]:
        """Find dependencies of a file.

        Args:
            project: Project name
            file_path: Path to the file

        Returns:
            Dictionary of imports/includes
        """
        container = get_container()
        return find_dependencies(
            container.project_registry.get_project(project),
            file_path,
            container.language_registry,
        )

    @mcp_server.tool()
    def analyze_complexity(project: str, file_path: str) -> Dict[str, Any]:
        """Analyze code complexity.

        Args:
            project: Project name
            file_path: Path to the file

        Returns:
            Complexity metrics
        """
        container = get_container()
        return analyze_code_complexity(
            container.project_registry.get_project(project),
            file_path,
            container.language_registry,
        )

    @mcp_server.tool()
    def find_similar_code(
        project: str,
        snippet: str,
        language: Optional[str] = None,
        threshold: float = 0.8,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
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
        container = get_container()
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
            container.project_registry.get_project(project),
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
        file_path: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Find usage of a symbol.

        Args:
            project: Project name
            symbol: Symbol name to find
            file_path: Optional file to look in (for local symbols)
            language: Language to search in

        Returns:
            List of usage locations
        """
        container = get_container()
        language_registry = container.language_registry
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
            container.project_registry.get_project(project),
            query,
            language_registry,
            container.tree_cache,
            file_path,
            language,
        )
