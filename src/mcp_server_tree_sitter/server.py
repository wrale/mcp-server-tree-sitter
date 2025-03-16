"""MCP server implementation for Tree-sitter with state persistence.

This server maintains state between invocations through singleton patterns,
allowing projects to remain registered throughout the server's lifetime.
"""

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .cache.parser_cache import tree_cache
from .capabilities import register_capabilities
from .config import CONFIG, load_config
from .language.query_templates import list_query_templates
from .language.registry import LanguageRegistry
from .models.ast import find_node_at_position, node_to_dict
from .resources.ast import get_file_ast, parse_file
from .resources.files import (
    get_file_content,
    get_file_info,
    list_project_files,
)
from .tools.analysis import (
    analyze_code_complexity,
    analyze_project_structure,
    extract_symbols,
    find_dependencies,
)
from .tools.project import (
    list_projects,
    project_registry,
    register_project,
    remove_project,
)
from .tools.query_builder import (
    adapt_query_for_language,
    build_compound_query,
    describe_node_types,
    get_template,
)
from .tools.search import query_code, search_text

# Create server instance - this single instance will maintain state across calls
mcp = FastMCP("tree_sitter")

# Register server capabilities
register_capabilities(mcp)

# Initialize language registry - uses singleton pattern for persistence
language_registry = LanguageRegistry()


# Configuration
@mcp.tool()
def configure(
    config_path: Optional[str] = None,
    cache_enabled: Optional[bool] = None,
    max_file_size_mb: Optional[int] = None,
    log_level: Optional[str] = None,
) -> Dict[str, Any]:
    """Configure the server.

    Args:
        config_path: Path to YAML config file
        cache_enabled: Whether to enable parse tree caching
        max_file_size_mb: Maximum file size in MB
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Current configuration
    """
    # Load config if path provided
    if config_path:
        load_config(config_path)

    # Update specific settings if provided
    if cache_enabled is not None:
        CONFIG.cache.enabled = cache_enabled

    if max_file_size_mb is not None:
        CONFIG.security.max_file_size_mb = max_file_size_mb

    if log_level is not None:
        CONFIG.log_level = log_level

    # Return current config
    return {
        "cache": {
            "enabled": CONFIG.cache.enabled,
            "max_size_mb": CONFIG.cache.max_size_mb,
            "ttl_seconds": CONFIG.cache.ttl_seconds,
        },
        "security": {
            "max_file_size_mb": CONFIG.security.max_file_size_mb,
            "excluded_dirs": CONFIG.security.excluded_dirs,
        },
        "language": {
            "auto_install": CONFIG.language.auto_install,
            "default_max_depth": CONFIG.language.default_max_depth,
        },
        "log_level": CONFIG.log_level,
    }


# Project Management Tools
@mcp.tool()
def register_project_tool(path: str, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """Register a project directory for code exploration.

    Args:
        path: Path to the project directory
        name: Optional name for the project (defaults to directory name)
        description: Optional description of the project

    Returns:
        Project information
    """
    return register_project(path, name, description)


@mcp.tool()
def list_projects_tool() -> List[Dict[str, Any]]:
    """List all registered projects.

    Returns:
        List of project information
    """
    return list_projects()


@mcp.tool()
def remove_project_tool(name: str) -> Dict[str, str]:
    """Remove a registered project.

    Args:
        name: Project name

    Returns:
        Success message
    """
    return remove_project(name)


# Language Tools
@mcp.tool()
def list_languages() -> Dict[str, Any]:
    """List available languages.

    Returns:
        Information about available languages
    """
    available = language_registry.list_available_languages()

    return {
        "available": available,
        "installable": [],  # No separate installation needed with language-pack
    }


@mcp.tool()
def check_language_available(language: str) -> Dict[str, str]:
    """Check if a tree-sitter language parser is available.

    Args:
        language: Language to check

    Returns:
        Success message
    """
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


# File Resources
@mcp.resource("project://{project}/files")
def get_project_files_resource(project: str) -> List[str]:
    """List all files in a project."""
    return list_project_files(project)


@mcp.resource("project://{project}/files/{pattern}")
def get_project_files_filtered_resource(project: str, pattern: str) -> List[str]:
    """List files in a project matching a pattern."""
    return list_project_files(project, pattern)


@mcp.resource("project://{project}/file/{file_path}")
def get_project_file_resource(project: str, file_path: str) -> str:
    """Get content of a specific file."""
    return get_file_content(project, file_path)


@mcp.resource("project://{project}/file/{file_path}/lines/{start}-{end}")
def get_file_lines_resource(project: str, file_path: str, start: int, end: int) -> str:
    """Get specific lines from a file."""
    return get_file_content(project, file_path, max_lines=end - start + 1, start_line=start)


# AST Resources
@mcp.resource("project://{project}/ast/{file_path}")
def get_syntax_tree_resource(project: str, file_path: str) -> Dict[str, Any]:
    """Get AST for a specific file."""
    return get_file_ast(project, file_path, max_depth=CONFIG.language.default_max_depth)


@mcp.resource("project://{project}/ast/{file_path}/depth/{depth}")
def get_syntax_tree_depth_resource(project: str, file_path: str, depth: int) -> Dict[str, Any]:
    """Get AST for a specific file with custom depth."""
    return get_file_ast(project, file_path, max_depth=depth)


# File Tools
@mcp.tool()
def list_files(
    project: str,
    pattern: Optional[str] = None,
    max_depth: Optional[int] = None,
    extensions: Optional[List[str]] = None,
) -> List[str]:
    """List files in a project.

    Args:
        project: Project name
        pattern: Optional glob pattern (e.g., "**/*.py")
        max_depth: Maximum directory depth
        extensions: List of file extensions to include (without dot)

    Returns:
        List of file paths
    """
    return list_project_files(project, pattern, max_depth, extensions)


@mcp.tool()
def get_file(project: str, path: str, max_lines: Optional[int] = None, start_line: int = 0) -> str:
    """Get content of a file.

    Args:
        project: Project name
        path: File path relative to project root
        max_lines: Maximum number of lines to return
        start_line: First line to include (0-based)

    Returns:
        File content
    """
    return get_file_content(project, path, max_lines=max_lines, start_line=start_line)


@mcp.tool()
def get_file_metadata(project: str, path: str) -> Dict[str, Any]:
    """Get metadata for a file.

    Args:
        project: Project name
        path: File path relative to project root

    Returns:
        File metadata
    """
    return get_file_info(project, path)


# AST Tools
@mcp.tool()
def get_ast(project: str, path: str, max_depth: Optional[int] = None, include_text: bool = True) -> Dict[str, Any]:
    """Get abstract syntax tree for a file.

    Args:
        project: Project name
        path: File path relative to project root
        max_depth: Maximum depth of the tree (default: 5)
        include_text: Whether to include node text

    Returns:
        AST as a nested dictionary
    """
    return get_file_ast(
        project,
        path,
        max_depth=max_depth or CONFIG.language.default_max_depth,
        include_text=include_text,
    )


@mcp.tool()
def get_node_at_position(project: str, path: str, row: int, column: int) -> Optional[Dict[str, Any]]:
    """Find the AST node at a specific position.

    Args:
        project: Project name
        path: File path relative to project root
        row: Line number (0-based)
        column: Column number (0-based)

    Returns:
        Node information or None if not found
    """
    project_obj = project_registry.get_project(project)
    file_path = project_obj.get_file_path(path)

    language = language_registry.language_for_file(path)
    if not language:
        raise ValueError(f"Could not detect language for {path}")

    tree, source_bytes = parse_file(file_path, language)

    node = find_node_at_position(tree.root_node, row, column)
    if node:
        return node_to_dict(node, source_bytes, max_depth=2)

    return None


# Search Tools
@mcp.tool()
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
    """Search for text pattern in project files.

    Args:
        project: Project name
        pattern: Text pattern to search for
        file_pattern: Optional glob pattern (e.g., "**/*.py")
        max_results: Maximum number of results
        case_sensitive: Whether to do case-sensitive matching
        whole_word: Whether to match whole words only
        use_regex: Whether to treat pattern as a regular expression
        context_lines: Number of context lines to include

    Returns:
        List of matches with file, line number, and text
    """
    return search_text(
        project,
        pattern,
        file_pattern,
        max_results,
        case_sensitive,
        whole_word,
        use_regex,
        context_lines,
    )


@mcp.tool()
def run_query(
    project: str,
    query: str,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    max_results: int = 100,
) -> List[Dict[str, Any]]:
    """Run a tree-sitter query on project files.

    Args:
        project: Project name
        query: Tree-sitter query string
        file_path: Optional specific file to query
        language: Language to use (required if file_path not provided)
        max_results: Maximum number of results

    Returns:
        List of query matches
    """
    return query_code(project, query, file_path, language, max_results)


@mcp.tool()
def get_query_template_tool(language: str, template_name: str) -> Dict[str, Any]:
    """Get a predefined tree-sitter query template.

    Args:
        language: Language name
        template_name: Template name (e.g., "functions", "classes")

    Returns:
        Query template information
    """
    template = get_template(language, template_name)
    if not template:
        raise ValueError(f"No template '{template_name}' for language '{language}'")

    return {
        "language": language,
        "name": template_name,
        "query": template,
    }


@mcp.tool()
def list_query_templates_tool(language: Optional[str] = None) -> Dict[str, Any]:
    """List available query templates.

    Args:
        language: Optional language to filter by

    Returns:
        Available templates
    """
    return list_query_templates(language)


@mcp.tool()
def build_query(language: str, patterns: List[str], combine: str = "or") -> Dict[str, str]:
    """Build a tree-sitter query from templates or patterns.

    Args:
        language: Language name
        patterns: List of template names or custom patterns
        combine: How to combine patterns ("or" or "and")

    Returns:
        Combined query
    """
    query = build_compound_query(language, patterns, combine)
    return {
        "language": language,
        "query": query,
    }


@mcp.tool()
def adapt_query(query: str, from_language: str, to_language: str) -> Dict[str, str]:
    """Adapt a query from one language to another.

    Args:
        query: Original query string
        from_language: Source language
        to_language: Target language

    Returns:
        Adapted query
    """
    adapted = adapt_query_for_language(query, from_language, to_language)
    return {
        "original_language": from_language,
        "target_language": to_language,
        "original_query": query,
        "adapted_query": adapted,
    }


@mcp.tool()
def get_node_types(language: str) -> Dict[str, str]:
    """Get descriptions of common node types for a language.

    Args:
        language: Language name

    Returns:
        Dictionary of node types and descriptions
    """
    return describe_node_types(language)


# Analysis Tools
@mcp.tool()
def get_symbols(
    project: str, file_path: str, symbol_types: Optional[List[str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Extract symbols from a file.

    Args:
        project: Project name
        file_path: Path to the file
        symbol_types: Types of symbols to extract (functions, classes, imports, etc.)

    Returns:
        Dictionary of symbols by type
    """
    return extract_symbols(project, file_path, symbol_types)


@mcp.tool()
def analyze_project(project: str, scan_depth: int = 3, ctx: Optional[Any] = None) -> Dict[str, Any]:
    """Analyze overall project structure.

    Args:
        project: Project name
        scan_depth: Depth of detailed analysis (higher is slower)

    Returns:
        Project analysis
    """
    return analyze_project_structure(project, scan_depth, ctx)


@mcp.tool()
def get_dependencies(project: str, file_path: str) -> Dict[str, List[str]]:
    """Find dependencies of a file.

    Args:
        project: Project name
        file_path: Path to the file

    Returns:
        Dictionary of imports/includes
    """
    return find_dependencies(project, file_path)


@mcp.tool()
def analyze_complexity(project: str, file_path: str) -> Dict[str, Any]:
    """Analyze code complexity.

    Args:
        project: Project name
        file_path: Path to the file

    Returns:
        Complexity metrics
    """
    return analyze_code_complexity(project, file_path)


@mcp.tool()
def find_similar_code(
    project: str,
    snippet: str,
    language: Optional[str] = None,
    threshold: float = 0.8,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """Find similar code to a snippet.

    Args:
        project: Project name
        snippet: Code snippet to find
        language: Language of the snippet
        threshold: Similarity threshold (0.0-1.0)
        max_results: Maximum number of results

    Returns:
        List of similar code locations
    """
    # This is a simple implementation that uses text search
    # A more sophisticated implementation would use tree-sitter to find
    # structurally similar code
    return search_text(
        project,
        snippet,
        file_pattern=f"**/*.{language}" if language else None,
        max_results=max_results,
    )


@mcp.tool()
def find_usage(
    project: str,
    symbol: str,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Find usage of a symbol.

    Args:
        project: Project name
        symbol: Symbol name to find
        file_path: Optional file to look in (for local symbols)
        language: Language to search in

    Returns:
        List of usage locations
    """
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

    return query_code(project, query, file_path, language)


# Cache Management
@mcp.tool()
def clear_cache(project: Optional[str] = None, file_path: Optional[str] = None) -> Dict[str, str]:
    """Clear the parse tree cache.

    Args:
        project: Optional project to clear cache for
        file_path: Optional specific file to clear cache for

    Returns:
        Status message
    """
    if project and file_path:
        # Clear cache for specific file
        project_obj = project_registry.get_project(project)
        abs_path = project_obj.get_file_path(file_path)
        tree_cache.invalidate(abs_path)
        message = f"Cache cleared for {file_path} in project {project}"
    elif project:
        # Clear cache for entire project
        project_obj = project_registry.get_project(project)
        # No direct way to clear by project, so invalidate entire cache
        tree_cache.invalidate()
        message = f"Cache cleared for project {project}"
    else:
        # Clear entire cache
        tree_cache.invalidate()
        message = "All caches cleared"

    return {"status": "success", "message": message}


# Prompts
@mcp.prompt()
def code_review(project: str, file_path: str) -> str:
    """Create a prompt for reviewing a code file"""
    content = get_file_content(project, file_path)
    language = language_registry.language_for_file(file_path)

    # Get structure information
    structure = ""
    try:
        symbols = extract_symbols(project, file_path)

        if "functions" in symbols and symbols["functions"]:
            structure += "\nFunctions:\n"
            for func in symbols["functions"]:
                structure += f"- {func['name']}\n"

        if "classes" in symbols and symbols["classes"]:
            structure += "\nClasses:\n"
            for cls in symbols["classes"]:
                structure += f"- {cls['name']}\n"
    except Exception:
        pass

    return f"""
    Please review this {language} code file:

    ```{language}
    {content}
    ```

    {structure}

    Focus on:
    1. Code clarity and organization
    2. Potential bugs or issues
    3. Performance considerations
    4. Best practices for {language}
    """


@mcp.prompt()
def explain_code(project: str, file_path: str, focus: Optional[str] = None) -> str:
    """Create a prompt for explaining a code file"""
    content = get_file_content(project, file_path)
    language = language_registry.language_for_file(file_path)

    focus_prompt = ""
    if focus:
        focus_prompt = f"\nPlease focus specifically on explaining: {focus}"

    return f"""
    Please explain this {language} code file:

    ```{language}
    {content}
    ```

    Provide a clear explanation of:
    1. What this code does
    2. How it's structured
    3. Any important patterns or techniques used
    {focus_prompt}
    """


@mcp.prompt()
def explain_tree_sitter_query() -> str:
    """Create a prompt explaining tree-sitter query syntax"""
    return """
    Tree-sitter queries use S-expression syntax to match patterns in code.

    Basic query syntax:
    - `(node_type)` - Match nodes of a specific type
    - `(node_type field: (child_type))` - Match nodes with specific field relationships
    - `@name` - Capture a node with a name
    - `#predicate` - Apply additional constraints

    Example query for Python functions:
    ```
    (function_definition
      name: (identifier) @function.name
      parameters: (parameters) @function.params
      body: (block) @function.body) @function.def
    ```

    Please write a tree-sitter query to find:
    """


@mcp.prompt()
def suggest_improvements(project: str, file_path: str) -> str:
    """Create a prompt for suggesting code improvements"""
    content = get_file_content(project, file_path)
    language = language_registry.language_for_file(file_path)

    try:
        complexity = analyze_code_complexity(project, file_path)
        complexity_info = f"""
        Code metrics:
        - Line count: {complexity["line_count"]}
        - Code lines: {complexity["code_lines"]}
        - Comment lines: {complexity["comment_lines"]}
        - Comment ratio: {complexity["comment_ratio"]:.1%}
        - Functions: {complexity["function_count"]}
        - Classes: {complexity["class_count"]}
        - Avg. function length: {complexity["avg_function_lines"]} lines
        - Cyclomatic complexity: {complexity["cyclomatic_complexity"]}
        """
    except Exception:
        complexity_info = ""

    return f"""
    Please suggest improvements for this {language} code:

    ```{language}
    {content}
    ```

    {complexity_info}

    Suggest specific, actionable improvements for:
    1. Code quality and readability
    2. Performance optimization
    3. Error handling and robustness
    4. Following {language} best practices

    Where possible, provide code examples of your suggestions.
    """


@mcp.prompt()
def project_overview(project: str) -> str:
    """Create a prompt for a project overview analysis"""
    project_obj = project_registry.get_project(project)

    try:
        analysis = analyze_project_structure(project)

        languages_str = "\n".join(f"- {lang}: {count} files" for lang, count in analysis["languages"].items())

        entry_points_str = (
            "\n".join(f"- {entry['path']} ({entry['language']})" for entry in analysis["entry_points"])
            if analysis["entry_points"]
            else "None detected"
        )

        build_files_str = (
            "\n".join(f"- {file['path']} ({file['type']})" for file in analysis["build_files"])
            if analysis["build_files"]
            else "None detected"
        )

    except Exception:
        languages_str = "Error analyzing languages"
        entry_points_str = "Error detecting entry points"
        build_files_str = "Error detecting build files"

    return f"""
    Please analyze this codebase:

    Project name: {project_obj.name}
    Path: {project_obj.root_path}

    Languages:
    {languages_str}

    Possible entry points:
    {entry_points_str}

    Build configuration:
    {build_files_str}

    Based on this information, please:
    1. Provide an overview of what this project seems to be
    2. Identify the main components and their relationships
    3. Suggest where to start exploring the codebase
    4. Identify any patterns or architectural approaches used
    """


def main() -> None:
    """Run the server"""
    # Load configuration
    load_config()
    mcp.run()


if __name__ == "__main__":
    main()
