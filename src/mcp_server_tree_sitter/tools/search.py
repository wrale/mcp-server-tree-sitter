"""Search tools for tree-sitter code analysis."""

import concurrent.futures
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..cache.parser_cache import tree_cache
from ..config import CONFIG
from ..exceptions import QueryError, SecurityError
from ..language.registry import LanguageRegistry
from ..models.project import ProjectRegistry
from ..utils.security import validate_file_access

project_registry = ProjectRegistry()
language_registry = LanguageRegistry()


def search_text(
    project_name: str,
    pattern: str,
    file_pattern: Optional[str] = None,
    max_results: Optional[int] = None,
    case_sensitive: bool = False,
    whole_word: bool = False,
    use_regex: bool = False,
    context_lines: int = 0,
) -> List[Dict[str, Any]]:
    """
    Search for text pattern in project files.

    Args:
        project_name: Name of the registered project
        pattern: Text pattern to search for
        file_pattern: Optional glob pattern to filter files (e.g. "**/*.py")
        max_results: Maximum number of results to return
        case_sensitive: Whether to do case-sensitive matching
        whole_word: Whether to match whole words only
        use_regex: Whether to treat pattern as a regular expression
        context_lines: Number of context lines to include before/after matches

    Returns:
        List of matches with file, line number, and text
    """
    if max_results is None:
        max_results = CONFIG.max_results_default

    project = project_registry.get_project(project_name)
    root = project.root_path

    results: List[Dict[str, Any]] = []
    pattern_obj = None

    # Prepare the pattern
    if use_regex:
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern_obj = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regular expression: {e}") from e
    elif whole_word:
        # Escape pattern for use in regex and add word boundary markers
        pattern_escaped = re.escape(pattern)
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern_obj = re.compile(rf"\b{pattern_escaped}\b", flags)
    elif not case_sensitive:
        # For simple case-insensitive search
        pattern = pattern.lower()

    file_pattern = file_pattern or "**/*"

    # Process files in parallel
    def process_file(file_path: Path) -> List[Dict[str, Any]]:
        file_results = []
        try:
            validate_file_access(file_path, root)

            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                match = False

                if pattern_obj:
                    # Using regex pattern
                    match_result = pattern_obj.search(line)
                    match = bool(match_result)
                elif case_sensitive:
                    # Simple case-sensitive search
                    match = pattern in line
                else:
                    # Simple case-insensitive search
                    match = pattern in line.lower()

                if match:
                    # Calculate context lines
                    start = max(0, i - 1 - context_lines)
                    end = min(len(lines), i + context_lines)

                    context = []
                    for ctx_i in range(start, end):
                        ctx_line = lines[ctx_i].rstrip("\n")
                        context.append(
                            {
                                "line": ctx_i + 1,
                                "text": ctx_line,
                                "is_match": ctx_i == i - 1,
                            }
                        )

                    file_results.append(
                        {
                            "file": str(file_path.relative_to(root)),
                            "line": i,
                            "text": line.rstrip("\n"),
                            "context": context,
                        }
                    )

                    if len(file_results) >= max_results:
                        break
        except Exception:
            # Skip files that can't be read
            pass

        return file_results

    # Collect files to process
    files_to_process = []
    for path in root.glob(file_pattern):
        if path.is_file():
            files_to_process.append(path)

    # Process files in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_file, f) for f in files_to_process]
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())
            if len(results) >= max_results:
                # Cancel any pending futures
                for f in futures:
                    f.cancel()
                break

    return results[:max_results]


def query_code(
    project_name: str,
    query_string: str,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    max_results: Optional[int] = None,
    include_snippets: bool = True,
) -> List[Dict[str, Any]]:
    """
    Run a tree-sitter query on code files.

    Args:
        project_name: Name of the registered project
        query_string: Tree-sitter query string
        file_path: Optional specific file to query
        language: Language to use (required if file_path not provided)
        max_results: Maximum number of results to return
        include_snippets: Whether to include code snippets in results

    Returns:
        List of query matches
    """
    if max_results is None:
        max_results = CONFIG.max_results_default

    project = project_registry.get_project(project_name)
    root = project.root_path
    results: List[Dict[str, Any]] = []

    if file_path is not None:
        # Query a specific file
        abs_path = project.get_file_path(file_path)

        try:
            validate_file_access(abs_path, root)
        except SecurityError as e:
            raise SecurityError(f"Access denied: {e}") from e

        # Detect language if not provided
        if not language:
            detected_language = language_registry.language_for_file(file_path)
            if detected_language:
                language = detected_language
            if not language:
                raise QueryError(f"Could not detect language for {file_path}")

        try:
            # Check if we have a cached tree
            assert language is not None  # For type checking
            cached = tree_cache.get(abs_path, language)
            if cached:
                tree, source_bytes = cached
            else:
                # Parse file
                with open(abs_path, "rb") as f:
                    source_bytes = f.read()

                assert language is not None  # For type checking
                parser = language_registry.get_parser(language)
                tree = parser.parse(source_bytes)

                # Cache the tree
                assert language is not None  # For type checking
                tree_cache.put(abs_path, language, tree, source_bytes)

            # Execute query
            assert language is not None  # For type checking
            lang = language_registry.get_language(language)
            query = lang.query(query_string)

            captures = query.captures(tree.root_node)

            # Handle different return formats from query.captures()
            if isinstance(captures, dict):
                # Dictionary format: {capture_name: [node1, node2, ...], ...}
                for capture_name, nodes in captures.items():
                    for node in nodes:
                        # Skip if we've reached max results
                        if max_results is not None and len(results) >= max_results:
                            break

                        try:
                            text = source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
                        except Exception:
                            text = "<binary data>"

                        result = {
                            "file": file_path,
                            "capture": capture_name,
                            "start": {
                                "row": node.start_point[0],
                                "column": node.start_point[1],
                            },
                            "end": {
                                "row": node.end_point[0],
                                "column": node.end_point[1],
                            },
                        }

                        if include_snippets:
                            result["text"] = text

                        results.append(result)
            else:
                # List format: [(node1, capture_name1), (node2, capture_name2), ...]
                for match in captures:
                    # Handle different return types from query.captures()
                    if isinstance(match, tuple) and len(match) == 2:
                        # Direct tuple unpacking
                        node, capture_name = match
                    elif hasattr(match, "node") and hasattr(match, "capture_name"):
                        # Object with node and capture_name attributes
                        node, capture_name = match.node, match.capture_name
                    elif isinstance(match, dict) and "node" in match and "capture" in match:
                        # Dictionary with node and capture keys
                        node, capture_name = match["node"], match["capture"]
                    else:
                        # Skip if format is unknown
                        continue

                    # Skip if we've reached max results
                    if max_results is not None and len(results) >= max_results:
                        break

                    try:
                        text = source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
                    except Exception:
                        text = "<binary data>"

                    result = {
                        "file": file_path,
                        "capture": capture_name,
                        "start": {
                            "row": node.start_point[0],
                            "column": node.start_point[1],
                        },
                        "end": {"row": node.end_point[0], "column": node.end_point[1]},
                    }

                    if include_snippets:
                        result["text"] = text

                    results.append(result)
        except Exception as e:
            raise QueryError(f"Error querying {file_path}: {e}") from e
    else:
        # Query across multiple files
        if not language:
            raise QueryError("Language is required when file_path is not provided")

        # Find all matching files for the language
        extensions = [(ext, lang) for ext, lang in language_registry._language_map.items() if lang == language]

        if not extensions:
            raise QueryError(f"No file extensions found for language {language}")

        # Process files in parallel
        def process_file(rel_path: str) -> List[Dict[str, Any]]:
            try:
                # Use single-file version of query_code
                file_results = query_code(
                    project_name,
                    query_string,
                    rel_path,
                    language,
                    max_results=(max_results if max_results is None else max_results - len(results)),
                    include_snippets=include_snippets,
                )
                return file_results
            except Exception:
                # Skip files that can't be queried
                return []

        # Collect files to process
        files_to_process = []
        for ext, _ in extensions:
            for path in root.glob(f"**/*.{ext}"):
                if path.is_file():
                    files_to_process.append(str(path.relative_to(root)))

        # Process files until we reach max_results
        for file in files_to_process:
            try:
                file_results = process_file(file)
                results.extend(file_results)

                if max_results is not None and len(results) >= max_results:
                    break
            except Exception:
                # Skip files that cause errors
                continue

    return results[:max_results] if max_results is not None else results
