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
        """List files in a registered project.

        Use this to discover which files exist before reading them with get_file.
        The project must already be registered (e.g. via register_project_tool).

        Args:
            project: Name of the registered project.
            pattern: Optional glob pattern relative to project root. Examples:
                "**/*.py" (all Python files), "src/**/*" (all under src/).
                If omitted, defaults to "**/*" (all files).
            max_depth: Optional maximum directory depth to traverse. Omit for no limit.
            extensions: Optional list of extensions to include, without the dot.
                Example: ["py", "js", "ts"]. If omitted, all extensions are included.

        Returns:
            List of file paths relative to the project root (e.g. ["src/main.py", "README.md"]).
        """
        project_registry = get_app().project_registry
        return list_project_files(project_registry.get_project(project), pattern, max_depth, extensions)

    @mcp_server.tool()
    def get_file(project: str, path: str, max_lines: Optional[int] = None, start_line: int = 0) -> str:
        """Read file content from a registered project, optionally a line range.

        Use this to read whole files or a slice of lines. The project must already
        be registered. Path is relative to the project root (e.g. "src/main.py").

        Line range: Lines are 0-based. First line is 0. You can request a slice by
        start_line and optionally cap the number of lines with max_lines.
        - Omit both: returns the entire file.
        - start_line only: returns from that line to the end of the file.
        - max_lines only (start_line=0): returns the first max_lines lines.
        - Both: returns up to max_lines lines starting at start_line.
        Out-of-bounds: start_line past end of file returns empty string; max_lines
        beyond the end of the file returns from start_line to end of file (no error).

        Args:
            project: Name of the registered project.
            path: File path relative to project root. Use forward slashes (e.g. "src/main.py").
            max_lines: Optional. Maximum number of lines to return. Omit to return all lines
                from start_line to end of file.
            start_line: First line to include (0-based). Default 0.

        Returns:
            File content as a string: either the full file or the requested line range.
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
        """Get metadata for a file or directory in a registered project.

        Use this to check size, line count, or whether a path is a file/directory
        before reading. The project must already be registered.

        Args:
            project: Name of the registered project.
            path: File or directory path relative to project root (e.g. "src/main.py").

        Returns:
            Dictionary with: path (relative), size (bytes), last_modified (Unix timestamp),
            created (Unix timestamp), is_directory (bool), extension (e.g. "py" or None),
            line_count (number of lines for files, None for directories).
        """
        return get_file_info(get_app().project_registry.get_project(project), path)
