"""Path utilities for mcp-server-tree-sitter."""

import os
from pathlib import Path
from typing import Union


def normalize_path(path: Union[str, Path], ensure_absolute: bool = False) -> Path:
    """
    Normalize a path for cross-platform compatibility.

    Args:
        path: Path string or object
        ensure_absolute: If True, raises ValueError for relative paths

    Returns:
        Normalized Path object
    """
    path_obj = Path(path).expanduser().resolve()

    if ensure_absolute and not path_obj.is_absolute():
        raise ValueError(f"Path must be absolute: {path}")

    return path_obj


def safe_relative_path(path: Union[str, Path], base: Union[str, Path]) -> Path:
    """
    Safely get a relative path that prevents directory traversal attacks.

    Args:
        path: Target path
        base: Base directory that should contain the path

    Returns:
        Relative path object

    Raises:
        ValueError: If path attempts to escape base directory
    """
    base_path = normalize_path(base)
    target_path = normalize_path(path)

    # Ensure target is within base
    try:
        relative = target_path.relative_to(base_path)
        # Check for directory traversal
        if ".." in str(relative).split(os.sep):
            raise ValueError(f"Path contains forbidden directory traversal: {path}")
        return relative
    except ValueError as e:
        raise ValueError(f"Path {path} is not within base directory {base}") from e


def get_project_root(path: Union[str, Path]) -> Path:
    """
    Attempt to determine project root from a file path by looking for common markers.

    Args:
        path: Path to start from (file or directory)

    Returns:
        Path to likely project root
    """
    path_obj = normalize_path(path)

    # If path is a file, start from its directory
    if path_obj.is_file():
        path_obj = path_obj.parent

    # Look for common project indicators
    markers = [
        ".git",
        "pyproject.toml",
        "setup.py",
        "package.json",
        "Cargo.toml",
        "CMakeLists.txt",
        ".svn",
        "Makefile",
    ]

    # Start from path and go up directories until a marker is found
    current = path_obj
    while current != current.parent:  # Stop at filesystem root
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    # If no marker found, return original directory
    return path_obj
