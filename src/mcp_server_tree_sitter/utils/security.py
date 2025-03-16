"""Security utilities for mcp-server-tree-sitter."""

from pathlib import Path
from typing import Union

from ..config import CONFIG
from ..exceptions import SecurityError


def validate_file_access(file_path: Union[str, Path], project_root: Union[str, Path]) -> None:
    """
    Validate a file can be safely accessed.

    Args:
        file_path: Path to validate
        project_root: Project root directory

    Raises:
        SecurityError: If path fails validation
    """
    path_obj = Path(file_path)
    root_obj = Path(project_root)

    # Normalize paths to prevent directory traversal
    try:
        normalized_path = path_obj.resolve()
        normalized_root = root_obj.resolve()
    except (ValueError, OSError) as e:
        raise SecurityError(f"Invalid path: {e}") from e

    # Check if path is inside project root
    if not str(normalized_path).startswith(str(normalized_root)):
        raise SecurityError(f"Access denied: {file_path} is outside project root")

    # Check excluded directories
    for excluded in CONFIG.security.excluded_dirs:
        if excluded in normalized_path.parts:
            raise SecurityError(f"Access denied to excluded directory: {excluded}")

    # Check file extension if restriction is enabled
    if CONFIG.security.allowed_extensions and path_obj.suffix.lower()[1:] not in CONFIG.security.allowed_extensions:
        raise SecurityError(f"File type not allowed: {path_obj.suffix}")

    # Check file size if it exists
    if normalized_path.exists() and normalized_path.is_file():
        file_size_mb = normalized_path.stat().st_size / (1024 * 1024)
        if file_size_mb > CONFIG.security.max_file_size_mb:
            raise SecurityError(
                f"File too large: {file_size_mb:.2f}MB exceeds limit of {CONFIG.security.max_file_size_mb}MB"
            )
