"""File operation tools for MCP server."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from ..exceptions import FileAccessError, ProjectError
from ..models.project import Project
from ..utils.security import validate_file_access

logger = logging.getLogger(__name__)


def list_project_files(
    project: Project,
    pattern: Optional[str] = None,
    max_depth: Optional[int] = None,
    filter_extensions: Optional[List[str]] = None,
) -> List[str]:
    """
    List files in a project, optionally filtered by pattern.

    Args:
        project: Project object
        pattern: Glob pattern for files (e.g., "**/*.py")
        max_depth: Maximum directory depth to traverse
        filter_extensions: List of file extensions to include (without dot)

    Returns:
        List of relative file paths
    """
    root = project.root_path
    pattern = pattern or "**/*"
    files = []

    # Handle max_depth=0 specially to avoid glob patterns with /*
    if max_depth == 0:
        # For max_depth=0, only list files directly in root directory
        for path in root.iterdir():
            if path.is_file():
                # Skip files that don't match extension filter
                if filter_extensions and path.suffix.lower()[1:] not in filter_extensions:
                    continue

                # Get path relative to project root
                rel_path = path.relative_to(root)
                files.append(str(rel_path))

        return sorted(files)

    # Handle max depth for glob pattern for max_depth > 0
    if max_depth is not None and max_depth > 0 and "**" in pattern:
        parts = pattern.split("**")
        if len(parts) == 2:
            pattern = f"{parts[0]}{'*/' * max_depth}{parts[1]}"

    # Ensure pattern doesn't start with / to avoid NotImplementedError
    if pattern.startswith("/"):
        pattern = pattern[1:]

    # Convert extensions to lowercase for case-insensitive matching
    if filter_extensions:
        filter_extensions = [ext.lower() for ext in filter_extensions]

    for path in root.glob(pattern):
        if path.is_file():
            # Skip files that don't match extension filter
            if filter_extensions and path.suffix.lower()[1:] not in filter_extensions:
                continue

            # Get path relative to project root
            rel_path = path.relative_to(root)
            files.append(str(rel_path))

    return sorted(files)


def get_file_content(
    project: Project,
    path: str,
    as_bytes: bool = False,
    max_lines: Optional[int] = None,
    start_line: int = 0,
) -> str | bytes:
    """
    Get content of a file in a project.

    Args:
        project: Project object
        path: Path to the file, relative to project root
        as_bytes: Whether to return raw bytes instead of string
        max_lines: Maximum number of lines to return
        start_line: First line to include (0-based)

    Returns:
        File content

    Raises:
        ProjectError: If project not found
        FileAccessError: If file access fails
    """
    try:
        file_path = project.get_file_path(path)
    except ProjectError as e:
        raise FileAccessError(str(e)) from e

    try:
        validate_file_access(file_path, project.root_path)
    except Exception as e:
        raise FileAccessError(f"Access denied: {e}") from e

    try:
        need_slice = start_line > 0 or max_lines is not None
        lines: List[str] | List[bytes]

        if as_bytes:
            with open(file_path, "rb") as f:
                if not need_slice:
                    return f.read()
                lines = f.readlines()
        else:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                if not need_slice:
                    return f.read()
                lines = f.readlines()

        n = len(lines)
        start_idx = min(start_line, n)
        end_idx = min(start_idx + max_lines, n) if max_lines is not None else n
        chunk = lines[start_idx:end_idx]

        if as_bytes:
            return b"".join(cast(List[bytes], chunk))
        return "".join(cast(List[str], chunk))

    except FileNotFoundError as e:
        raise FileAccessError(f"File not found: {path}") from e
    except PermissionError as e:
        raise FileAccessError(f"Permission denied: {path}") from e
    except Exception as e:
        raise FileAccessError(f"Error reading file: {e}") from e


def get_file_info(project: Project, path: str) -> Dict[str, Any]:
    """
    Get metadata about a file.

    Args:
        project: Project object
        path: Path to the file, relative to project root

    Returns:
        Dictionary with file information

    Raises:
        ProjectError: If project not found
        FileAccessError: If file access fails
    """
    try:
        file_path = project.get_file_path(path)
    except ProjectError as e:
        raise FileAccessError(str(e)) from e

    try:
        validate_file_access(file_path, project.root_path)
    except Exception as e:
        raise FileAccessError(f"Access denied: {e}") from e

    try:
        stat = file_path.stat()
        return {
            "path": str(path),
            "size": stat.st_size,
            "last_modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_directory": file_path.is_dir(),
            "extension": file_path.suffix[1:] if file_path.suffix else None,
            "line_count": count_lines(file_path) if file_path.is_file() else None,
        }
    except FileNotFoundError as e:
        raise FileAccessError(f"File not found: {path}") from e
    except PermissionError as e:
        raise FileAccessError(f"Permission denied: {path}") from e
    except Exception as e:
        raise FileAccessError(f"Error getting file info: {e}") from e


def count_lines(file_path: Path) -> int:
    """
    Count lines in a file efficiently.

    Args:
        file_path: Path to the file

    Returns:
        Number of lines
    """
    try:
        with open(file_path, "rb") as f:
            return sum(1 for _ in f)
    except (IOError, OSError):
        return 0
