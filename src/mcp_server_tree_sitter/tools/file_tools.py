"""File listing and content tool handlers."""

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from ..app import get_app
from .file_operations import get_file_content, get_file_info, list_project_files


def register_file_tools(mcp_server: FastMCP) -> None:
    """Register file operation tools."""

    @mcp_server.tool()
    def list_files(
        project: str,
        pattern: Optional[str] = None,
        max_depth: Optional[int] = None,
        extensions: Optional[List[str]] = None,
    ) -> List[str]:
        """List files in a project.

        Args:
            project: Project name
            pattern: Optional glob pattern (e.g., "**/*.py")
            max_depth: Maximum directory depth
            extensions: List of file extensions to include (without dot)

        Returns:
            List of file paths
        """
        project_registry = get_app().project_registry
        return list_project_files(project_registry.get_project(project), pattern, max_depth, extensions)

    @mcp_server.tool()
    def get_file(project: str, path: str, max_lines: Optional[int] = None, start_line: int = 0) -> str:
        """Get content of a file.

        Args:
            project: Project name
            path: File path relative to project root
            max_lines: Maximum number of lines to return
            start_line: First line to include (0-based)

        Returns:
            File content
        """
        project_registry = get_app().project_registry
        content = get_file_content(
            project_registry.get_project(project),
            path,
            as_bytes=False,
            max_lines=max_lines,
            start_line=start_line,
        )
        assert isinstance(content, str), "as_bytes=False returns str"
        return content

    @mcp_server.tool()
    def get_file_metadata(project: str, path: str) -> Dict[str, Any]:
        """Get metadata for a file.

        Args:
            project: Project name
            path: File path relative to project root

        Returns:
            File metadata
        """
        return get_file_info(get_app().project_registry.get_project(project), path)
