"""Utilities for safe file operations.

This module provides safe file I/O operations with proper encoding handling
and consistent interfaces for both text and binary operations.
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union


def read_text_file(path: Union[str, Path]) -> List[str]:
    """
    Safely read a text file with proper encoding handling.

    Args:
        path: Path to the file

    Returns:
        List of lines from the file
    """
    with open(str(path), "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


def read_binary_file(path: Union[str, Path]) -> bytes:
    """
    Safely read a binary file.

    Args:
        path: Path to the file

    Returns:
        File contents as bytes
    """
    with open(str(path), "rb") as f:
        return f.read()


def get_file_content_and_lines(path: Union[str, Path]) -> Tuple[bytes, List[str]]:
    """
    Get both binary content and text lines from a file.

    Args:
        path: Path to the file

    Returns:
        Tuple of (binary_content, text_lines)
    """
    binary_content = read_binary_file(path)
    text_lines = read_text_file(path)
    return binary_content, text_lines


def is_line_comment(line: str, comment_prefix: str) -> bool:
    """
    Check if a line is a comment.

    Args:
        line: The line to check
        comment_prefix: Comment prefix character(s)

    Returns:
        True if the line is a comment
    """
    return line.strip().startswith(comment_prefix)


def count_comment_lines(lines: List[str], comment_prefix: str) -> int:
    """
    Count comment lines in a file.

    Args:
        lines: List of lines to check
        comment_prefix: Comment prefix character(s)

    Returns:
        Number of comment lines
    """
    return sum(1 for line in lines if is_line_comment(line, comment_prefix))


def get_comment_prefix(language: str) -> Optional[str]:
    """
    Get the comment prefix for a language.

    Args:
        language: Language identifier

    Returns:
        Comment prefix or None if unknown
    """
    # Language-specific comment detection
    comment_starters = {
        "python": "#",
        "javascript": "//",
        "typescript": "//",
        "java": "//",
        "c": "//",
        "cpp": "//",
        "go": "//",
        "ruby": "#",
        "rust": "//",
        "php": "//",
        "swift": "//",
        "kotlin": "//",
        "scala": "//",
        "bash": "#",
        "shell": "#",
        "yaml": "#",
        "html": "<!--",
        "css": "/*",
        "scss": "//",
        "sass": "//",
        "sql": "--",
    }

    return comment_starters.get(language)


def parse_file_with_encoding(path: Union[str, Path], encoding: str = "utf-8") -> Tuple[bytes, List[str]]:
    """
    Parse a file with explicit encoding handling, returning both binary and text.

    Args:
        path: Path to the file
        encoding: Text encoding to use

    Returns:
        Tuple of (binary_content, decoded_lines)
    """
    binary_content = read_binary_file(path)

    # Now decode the binary content with the specified encoding
    text = binary_content.decode(encoding, errors="replace")
    lines = text.splitlines(True)  # Keep line endings

    return binary_content, lines


def read_file_lines(path: Union[str, Path], start_line: int = 0, max_lines: Optional[int] = None) -> List[str]:
    """
    Read specific lines from a file.

    Args:
        path: Path to the file
        start_line: First line to include (0-based)
        max_lines: Maximum number of lines to return

    Returns:
        List of requested lines
    """
    with open(str(path), "r", encoding="utf-8", errors="replace") as f:
        # Skip lines before start_line
        for _ in range(start_line):
            next(f, None)

        # Read up to max_lines
        if max_lines is not None:
            return [f.readline() for _ in range(max_lines)]
        else:
            return f.readlines()
