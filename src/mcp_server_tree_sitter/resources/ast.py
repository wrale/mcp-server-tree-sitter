"""AST resource functions for tree-sitter."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..cache.parser_cache import tree_cache
from ..config import CONFIG
from ..exceptions import FileAccessError, ParsingError
from ..language.registry import LanguageRegistry
from ..models.ast import node_to_dict
from ..models.project import ProjectRegistry
from ..utils.security import validate_file_access

project_registry = ProjectRegistry()
language_registry = LanguageRegistry()


def parse_file(file_path: Path, language: str) -> Tuple[Any, bytes]:
    """
    Parse a file using tree-sitter.

    Args:
        file_path: Path to file
        language: Language identifier

    Returns:
        (Tree, source_bytes) tuple

    Raises:
        ParsingError: If parsing fails
    """
    # Check if we have a cached tree
    cached = tree_cache.get(file_path, language)
    if cached:
        return cached

    try:
        # Read file
        with open(file_path, "rb") as f:
            source_bytes = f.read()

        # Parse
        parser = language_registry.get_parser(language)
        tree = parser.parse(source_bytes)

        # Cache the tree
        tree_cache.put(file_path, language, tree, source_bytes)

        return tree, source_bytes
    except Exception as e:
        raise ParsingError(f"Error parsing {file_path}: {e}") from e


def get_file_ast(
    project_name: str,
    file_path: str,
    max_depth: Optional[int] = None,
    include_text: bool = True,
) -> Dict[str, Any]:
    """
    Get the AST for a file.

    Args:
        project_name: Project name
        file_path: File path (relative to project root)
        max_depth: Maximum depth to traverse the tree
        include_text: Whether to include node text

    Returns:
        AST as a nested dictionary

    Raises:
        FileAccessError: If file access fails
        ParsingError: If parsing fails
    """
    project = project_registry.get_project(project_name)
    abs_path = project.get_file_path(file_path)

    try:
        validate_file_access(abs_path, project.root_path)
    except Exception as e:
        raise FileAccessError(f"Access denied: {e}") from e

    language = language_registry.language_for_file(file_path)
    if not language:
        raise ParsingError(f"Could not detect language for {file_path}")

    tree, source_bytes = parse_file(abs_path, language)
    depth = max_depth or CONFIG.language.default_max_depth

    return {
        "file": file_path,
        "language": language,
        "tree": node_to_dict(
            tree.root_node,
            source_bytes,
            include_children=True,
            include_text=include_text,
            max_depth=depth,
        ),
    }
