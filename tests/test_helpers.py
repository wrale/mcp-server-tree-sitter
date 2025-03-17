"""Helper functions for tests using the new dependency injection pattern."""

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from mcp_server_tree_sitter.api import (
    clear_cache as api_clear_cache,
)
from mcp_server_tree_sitter.api import (
    get_config,
    get_language_registry,
    get_project_registry,
    get_tree_cache,
)
from mcp_server_tree_sitter.api import (
    list_projects as api_list_projects,
)
from mcp_server_tree_sitter.api import (
    register_project as api_register_project,
)
from mcp_server_tree_sitter.api import (
    remove_project as api_remove_project,
)
from mcp_server_tree_sitter.di import get_container
from mcp_server_tree_sitter.language.query_templates import (
    get_query_template,
    list_query_templates,
)
from mcp_server_tree_sitter.tools.analysis import (
    analyze_code_complexity,
    analyze_project_structure,
    extract_symbols,
    find_dependencies,
)
from mcp_server_tree_sitter.tools.ast_operations import find_node_at_position as ast_find_node_at_position
from mcp_server_tree_sitter.tools.ast_operations import get_file_ast as ast_get_file_ast
from mcp_server_tree_sitter.tools.file_operations import (
    get_file_content,
    get_file_info,
    list_project_files,
)
from mcp_server_tree_sitter.tools.query_builder import (
    adapt_query_for_language,
    build_compound_query,
    describe_node_types,
)
from mcp_server_tree_sitter.tools.search import query_code, search_text


@contextmanager
def temp_config(**kwargs):
    """
    Context manager for temporarily changing configuration settings.

    Args:
        **kwargs: Configuration values to change temporarily
    """
    # Get container and save original values
    container = get_container()
    config_manager = container.config_manager
    original_values = {}

    # Apply configuration changes
    for key, value in kwargs.items():
        # For tree_cache settings that need to be applied directly
        if key == "cache.enabled":
            original_values["tree_cache.enabled"] = container.tree_cache.enabled
            container.tree_cache.set_enabled(value)

        if key == "cache.max_size_mb":
            original_values["tree_cache.max_size_mb"] = container.tree_cache._get_max_size_mb()
            container.tree_cache.set_max_size_mb(value)

        # Handle log level specially
        if key == "log_level":
            # Save the original logger level
            root_logger = logging.getLogger("mcp_server_tree_sitter")
            original_values["root_logger_level"] = root_logger.level

            # Apply the new level directly
            log_level_value = getattr(logging, value, None)
            if log_level_value is not None:
                root_logger.setLevel(log_level_value)
                logging.debug(f"Set root logger to {value} in temp_config")

        # Update config manager values
        config_manager.update_value(key, value)

    try:
        yield
    finally:
        # Restore original values
        for key, value in original_values.items():
            if key == "tree_cache.enabled":
                container.tree_cache.set_enabled(value)
            elif key == "tree_cache.max_size_mb":
                container.tree_cache.set_max_size_mb(value)
            elif key == "root_logger_level":
                # Restore original logger level
                root_logger = logging.getLogger("mcp_server_tree_sitter")
                root_logger.setLevel(value)
                logging.debug(f"Restored root logger level to {value} in temp_config")

        # Re-apply original config values to config manager
        current_config = container.get_config()
        for key, _value in kwargs.items():
            parts = key.split(".")
            if len(parts) == 2:
                section, setting = parts
                if hasattr(current_config, section):
                    section_obj = getattr(current_config, section)
                    if hasattr(section_obj, setting):
                        # Get the original value from container's config
                        original_config = container.config_manager.get_config()
                        original_section = getattr(original_config, section, None)
                        if original_section and hasattr(original_section, setting):
                            original_value = getattr(original_section, setting)
                            config_manager.update_value(key, original_value)
            elif hasattr(current_config, key):
                # Handle top-level attributes like log_level
                original_config = container.config_manager.get_config()
                if hasattr(original_config, key):
                    original_value = getattr(original_config, key)
                    config_manager.update_value(key, original_value)


# Project Management Tools
def register_project_tool(path: str, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """Register a project directory for code exploration."""
    return api_register_project(path, name, description)


def list_projects_tool() -> List[Dict[str, Any]]:
    """List all registered projects."""
    return api_list_projects()


def remove_project_tool(name: str) -> Dict[str, str]:
    """Remove a registered project."""
    return api_remove_project(name)


# Language Tools
def list_languages() -> Dict[str, Any]:
    """List available languages."""
    language_registry = get_language_registry()
    available = language_registry.list_available_languages()
    return {
        "available": available,
        "installable": [],  # No separate installation needed with language-pack
    }


def check_language_available(language: str) -> Dict[str, str]:
    """Check if a tree-sitter language parser is available."""
    language_registry = get_language_registry()
    if language_registry.is_language_available(language):
        return {
            "status": "success",
            "message": f"Language '{language}' is available via tree-sitter-language-pack",
        }
    else:
        return {
            "status": "error",
            "message": f"Language '{language}' is not available",
        }


# File Operations
def list_files(
    project: str,
    pattern: Optional[str] = None,
    max_depth: Optional[int] = None,
    extensions: Optional[List[str]] = None,
) -> List[str]:
    """List files in a project."""
    project_registry = get_project_registry()
    return list_project_files(project_registry.get_project(project), pattern, max_depth, extensions)


def get_file(project: str, path: str, max_lines: Optional[int] = None, start_line: int = 0) -> str:
    """Get content of a file."""
    project_registry = get_project_registry()
    return get_file_content(project_registry.get_project(project), path, max_lines=max_lines, start_line=start_line)


def get_file_metadata(project: str, path: str) -> Dict[str, Any]:
    """Get metadata for a file."""
    project_registry = get_project_registry()
    return get_file_info(project_registry.get_project(project), path)


# AST Analysis
def get_ast(project: str, path: str, max_depth: Optional[int] = None, include_text: bool = True) -> Dict[str, Any]:
    """Get abstract syntax tree for a file."""
    project_registry = get_project_registry()
    language_registry = get_language_registry()
    tree_cache = get_tree_cache()
    config = get_config()

    depth = max_depth or config.language.default_max_depth

    return ast_get_file_ast(
        project_registry.get_project(project),
        path,
        language_registry,
        tree_cache,
        max_depth=depth,
        include_text=include_text,
    )


def get_node_at_position(project: str, path: str, row: int, column: int) -> Optional[Dict[str, Any]]:
    """Find the AST node at a specific position."""
    from mcp_server_tree_sitter.models.ast import node_to_dict

    project_registry = get_project_registry()
    project_obj = project_registry.get_project(project)
    file_path = project_obj.get_file_path(path)

    language_registry = get_language_registry()
    language = language_registry.language_for_file(path)
    if not language:
        raise ValueError(f"Could not detect language for {path}")

    from mcp_server_tree_sitter.tools.ast_operations import parse_file

    tree, source_bytes = parse_file(file_path, language, language_registry, get_tree_cache())

    node = ast_find_node_at_position(tree.root_node, row, column)
    if node:
        return node_to_dict(node, source_bytes, max_depth=2)

    return None


# Search and Query Tools
def find_text(
    project: str,
    pattern: str,
    file_pattern: Optional[str] = None,
    max_results: int = 100,
    case_sensitive: bool = False,
    whole_word: bool = False,
    use_regex: bool = False,
    context_lines: int = 2,
) -> List[Dict[str, Any]]:
    """Search for text pattern in project files."""
    project_registry = get_project_registry()
    return search_text(
        project_registry.get_project(project),
        pattern,
        file_pattern,
        max_results,
        case_sensitive,
        whole_word,
        use_regex,
        context_lines,
    )


def run_query(
    project: str,
    query: str,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    max_results: int = 100,
) -> List[Dict[str, Any]]:
    """Run a tree-sitter query on project files."""
    project_registry = get_project_registry()
    language_registry = get_language_registry()
    tree_cache = get_tree_cache()

    return query_code(
        project_registry.get_project(project),
        query,
        language_registry,
        tree_cache,
        file_path,
        language,
        max_results,
    )


def get_query_template_tool(language: str, template_name: str) -> Dict[str, Any]:
    """Get a predefined tree-sitter query template."""
    template = get_query_template(language, template_name)
    if not template:
        raise ValueError(f"No template '{template_name}' for language '{language}'")

    return {
        "language": language,
        "name": template_name,
        "query": template,
    }


def list_query_templates_tool(language: Optional[str] = None) -> Dict[str, Any]:
    """List available query templates."""
    return list_query_templates(language)


def build_query(language: str, patterns: List[str], combine: str = "or") -> Dict[str, str]:
    """Build a tree-sitter query from templates or patterns."""
    query = build_compound_query(language, patterns, combine)
    return {
        "language": language,
        "query": query,
    }


def adapt_query(query: str, from_language: str, to_language: str) -> Dict[str, str]:
    """Adapt a query from one language to another."""
    adapted = adapt_query_for_language(query, from_language, to_language)
    return {
        "original_language": from_language,
        "target_language": to_language,
        "original_query": query,
        "adapted_query": adapted,
    }


def get_node_types(language: str) -> Dict[str, str]:
    """Get descriptions of common node types for a language."""
    return describe_node_types(language)


# Code Analysis Tools
def get_symbols(
    project: str, file_path: str, symbol_types: Optional[List[str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Extract symbols from a file."""
    project_registry = get_project_registry()
    language_registry = get_language_registry()

    return extract_symbols(project_registry.get_project(project), file_path, language_registry, symbol_types)


def analyze_project(project: str, scan_depth: int = 3, ctx: Optional[Any] = None) -> Dict[str, Any]:
    """Analyze overall project structure."""
    project_registry = get_project_registry()
    language_registry = get_language_registry()

    return analyze_project_structure(project_registry.get_project(project), language_registry, scan_depth, ctx)


def get_dependencies(project: str, file_path: str) -> Dict[str, List[str]]:
    """Find dependencies of a file."""
    project_registry = get_project_registry()
    language_registry = get_language_registry()

    return find_dependencies(
        project_registry.get_project(project),
        file_path,
        language_registry,
    )


def analyze_complexity(project: str, file_path: str) -> Dict[str, Any]:
    """Analyze code complexity."""
    project_registry = get_project_registry()
    language_registry = get_language_registry()

    return analyze_code_complexity(
        project_registry.get_project(project),
        file_path,
        language_registry,
    )


def find_similar_code(
    project: str,
    snippet: str,
    language: Optional[str] = None,
    threshold: float = 0.8,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """Find similar code to a snippet."""
    # This is a simple implementation that uses text search
    project_registry = get_project_registry()

    # Map language names to file extensions
    extension_map = {
        "python": "py",
        "javascript": "js",
        "typescript": "ts",
        "rust": "rs",
        "go": "go",
        "java": "java",
        "c": "c",
        "cpp": "cpp",
        "ruby": "rb",
        "swift": "swift",
        "kotlin": "kt",
    }

    # Get the appropriate file extension for the language
    extension = extension_map.get(language, language) if language else None
    file_pattern = f"**/*.{extension}" if extension else None

    return search_text(
        project_registry.get_project(project),
        snippet,
        file_pattern=file_pattern,
        max_results=max_results,
    )


def find_usage(
    project: str,
    symbol: str,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Find usage of a symbol."""
    project_registry = get_project_registry()
    language_registry = get_language_registry()
    tree_cache = get_tree_cache()

    # Detect language if not provided but file_path is
    if not language and file_path:
        language = language_registry.language_for_file(file_path)

    if not language:
        raise ValueError("Either language or file_path must be provided")

    # Build a query to find references to the symbol
    query = f"""
    (
      (identifier) @reference
      (#eq? @reference "{symbol}")
    )
    """

    return query_code(project_registry.get_project(project), query, language_registry, tree_cache, file_path, language)


# Cache Management
def clear_cache(project: Optional[str] = None, file_path: Optional[str] = None) -> Dict[str, str]:
    """Clear the parse tree cache."""
    return api_clear_cache(project, file_path)


# Server configuration
def configure(
    config_path: Optional[str] = None,
    cache_enabled: Optional[bool] = None,
    max_file_size_mb: Optional[int] = None,
    log_level: Optional[str] = None,
) -> Dict[str, Any]:
    """Configure the server using the DI container."""
    container = get_container()
    config_manager = container.config_manager

    # Load config if path provided
    if config_path:
        logging.info(f"Configuring server with YAML config from: {config_path}")
        config_manager.load_from_file(config_path)

    # Update specific settings if provided
    if cache_enabled is not None:
        logging.info(f"Setting cache.enabled to {cache_enabled}")
        config_manager.update_value("cache.enabled", cache_enabled)
        container.tree_cache.set_enabled(cache_enabled)

    if max_file_size_mb is not None:
        logging.info(f"Setting security.max_file_size_mb to {max_file_size_mb}")
        config_manager.update_value("security.max_file_size_mb", max_file_size_mb)

    if log_level is not None:
        logging.info(f"Setting log_level to {log_level}")
        config_manager.update_value("log_level", log_level)

        # Apply log level directly to loggers
        log_level_value = getattr(logging, log_level, None)
        if log_level_value is not None:
            # Set the root logger for the package
            root_logger = logging.getLogger("mcp_server_tree_sitter")
            root_logger.setLevel(log_level_value)
            logging.info(f"Applied log level {log_level} to mcp_server_tree_sitter loggers")

    # Return current config as dict
    return config_manager.to_dict()


def configure_with_context(
    context: Any,
    config_path: Optional[str] = None,
    cache_enabled: Optional[bool] = None,
    max_file_size_mb: Optional[int] = None,
    log_level: Optional[str] = None,
) -> tuple[Dict[str, Any], Any]:
    """
    Configure with explicit context - compatibility function.

    In new DI model, context is replaced by container. This is a compatibility
    function that accepts a context parameter but uses the container internally.
    """
    # Just delegate to the regular configure function and return current config
    result = configure(config_path, cache_enabled, max_file_size_mb, log_level)
    return result, get_container().get_config()
