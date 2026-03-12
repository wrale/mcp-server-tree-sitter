"""File listing and content tool handlers."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..app import get_app
from .file_operations import get_file_content, get_file_info, list_project_files


def register_file_tools(mcp_server: FastMCP) -> None:
    """Register file operation tools."""

    @mcp_server.tool()
    def list_files(
        project: str,
        pattern: str | None = None,
        max_depth: int | None = None,
        extensions: list[str] | None = None,
    ) -> list[str]:
        """List file paths in a registered project (relative to project root).

        Args:
            project: Name of the registered project.
            pattern: Glob pattern (e.g. '**/*.py'). Defaults to '**/*' (all files).
            max_depth: Maximum directory depth. Defaults to None (no limit).
            extensions: File extensions to include, without dot (e.g. ['py', 'js']). Defaults to None (all).

        Returns:
            List of relative path strings (e.g. ['src/main.py']).

        Raises:
            ProjectError: If project is not registered.
        """
        project_registry = get_app().project_registry
        return list_project_files(project_registry.get_project(project), pattern, max_depth, extensions)

    @mcp_server.tool()
    def get_file(project: str, path: str, max_lines: int | None = None, start_line: int = 0) -> str:
        """Read file content. Path relative to project root; line numbers are 0-based.

        Args:
            project: Name of the registered project.
            path: File path relative to project root (e.g. 'src/main.py').
            max_lines: Maximum number of lines to return. Defaults to None (to end of file).
            start_line: First line to include (0-based). Defaults to 0.
                Out-of-range start_line returns empty string.

        Returns:
            File content as string (full file or requested line range).

        Raises:
            ProjectError: If project is not registered.
            FileAccessError: If path is outside project or access is denied.
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
    def get_file_metadata(project: str, path: str) -> dict[str, Any]:
        """Get metadata for a file or directory in the project.

        Args:
            project: Name of the registered project.
            path: File or directory path relative to project root.

        Returns:
            Dict with path, size, last_modified, created, is_directory, extension, line_count.

        Raises:
            ProjectError: If project is not registered.
            FileAccessError: If path is invalid or access is denied.
        """
        return get_file_info(get_app().project_registry.get_project(project), path)
