"""Security utilities for mcp-server-tree-sitter."""

import logging
from pathlib import Path
from typing import Union

from ..api import get_config
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
    # Always get a fresh config for each validation
    config = get_config()
    logger = logging.getLogger(__name__)

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
    for excluded in config.security.excluded_dirs:
        if excluded in normalized_path.parts:
            raise SecurityError(f"Access denied to excluded directory: {excluded}")

    # Check file extension if restriction is enabled
    if config.security.allowed_extensions and path_obj.suffix.lower()[1:] not in config.security.allowed_extensions:
        raise SecurityError(f"File type not allowed: {path_obj.suffix}")

    # Check file size if it exists
    if normalized_path.exists() and normalized_path.is_file():
        file_size_mb = normalized_path.stat().st_size / (1024 * 1024)
        max_file_size_mb = config.security.max_file_size_mb
        logger.debug(f"File size check: {file_size_mb:.2f}MB, limit: {max_file_size_mb}MB")
        if file_size_mb > max_file_size_mb:
            raise SecurityError(f"File too large: {file_size_mb:.2f}MB exceeds limit of {max_file_size_mb}MB")
