"""File resource functionality for MCP server."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..exceptions import FileAccessError
from ..models.project import ProjectRegistry
from ..utils.security import validate_file_access

project_registry = ProjectRegistry()


def list_project_files(
    project_name: str,
    pattern: Optional[str] = None,
    max_depth: Optional[int] = None,
    filter_extensions: Optional[List[str]] = None,
) -> List[str]:
    """
    List files in a project, optionally filtered by pattern.

    Args:
        project_name: Name of the registered project
        pattern: Glob pattern for files (e.g., "**/*.py")
        max_depth: Maximum directory depth to traverse
        filter_extensions: List of file extensions to include (without dot)

    Returns:
        List of relative file paths

    Raises:
        ProjectError: If project not found
    """
    project = project_registry.get_project(project_name)
    root = project.root_path

    pattern = pattern or "**/*"
    files = []

    # Handle max depth for glob pattern
    if max_depth is not None and "**" in pattern:
        parts = pattern.split("**")
        if len(parts) == 2:
            pattern = f"{parts[0]}{'*/' * max_depth}{parts[1]}"

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
    project_name: str,
    path: str,
    as_bytes: bool = False,
    max_lines: Optional[int] = None,
    start_line: int = 0,
) -> str:
    """
    Get content of a file in a project.

    Args:
        project_name: Name of the registered project
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
    project = project_registry.get_project(project_name)
    file_path = project.get_file_path(path)

    try:
        validate_file_access(file_path, project.root_path)
    except Exception as e:
        raise FileAccessError(f"Access denied: {e}") from e

    try:
        if as_bytes:
            with open(file_path, "rb") as f:
                content = f.read()

            # Handle line limiting for bytes (more complex)
            if max_lines is not None or start_line > 0:
                lines = content.split(b"\n")
                end_line = min(start_line + max_lines, len(lines)) if max_lines else len(lines)
                content = b"\n".join(lines[start_line:end_line])

            return content  # type: ignore
        else:
            if max_lines is None and start_line == 0:
                # Simple case: read whole file
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            else:
                # Read specific lines
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    # Skip lines before start_line
                    for _ in range(start_line):
                        next(f, None)

                    # Read up to max_lines
                    if max_lines is not None:
                        return "".join(f.readline() for _ in range(max_lines))
                    else:
                        return f.read()

    except FileNotFoundError as e:
        raise FileAccessError(f"File not found: {path}") from e
    except PermissionError as e:
        raise FileAccessError(f"Permission denied: {path}") from e
    except Exception as e:
        raise FileAccessError(f"Error reading file: {e}") from e


def get_file_info(project_name: str, path: str) -> Dict[str, Any]:
    """
    Get metadata about a file.

    Args:
        project_name: Name of the registered project
        path: Path to the file, relative to project root

    Returns:
        Dictionary with file information

    Raises:
        ProjectError: If project not found
        FileAccessError: If file access fails
    """
    project = project_registry.get_project(project_name)
    file_path = project.get_file_path(path)

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
