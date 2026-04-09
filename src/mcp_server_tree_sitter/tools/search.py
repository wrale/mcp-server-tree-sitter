"""Search tools for tree-sitter code analysis."""

import concurrent.futures
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..exceptions import QueryError, SecurityError
from ..utils.security import validate_file_access


def search_text(
    project: Any,
    pattern: str,
    file_pattern: Optional[str] = None,
    max_results: int = 100,
    case_sensitive: bool = False,
    whole_word: bool = False,
    use_regex: bool = False,
    context_lines: int = 0,
) -> List[Dict[str, Any]]:
    """
    Search for text pattern in project files.

    Args:
        project: Project object
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
                    # Simple case-sensitive search - check both original and stripped versions
                    match = pattern in line or pattern.strip() in line.strip()
                else:
                    # Simple case-insensitive search - check both original and stripped versions
                    line_lower = line.lower()
                    pattern_lower = pattern.lower()
                    match = pattern_lower in line_lower or pattern_lower.strip() in line_lower.strip()

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
    project: Any,
    query_string: str,
    language_registry: Any,
    tree_cache: Any,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    max_results: int = 100,
    include_snippets: bool = True,
    capture_filter: Optional[str] = None,
    compact: bool = False,
) -> List[Dict[str, Any]]:
    """
    Run a tree-sitter query on code files.

    Args:
        project: Project object
        query_string: Tree-sitter query string
        language_registry: Language registry
        tree_cache: Tree cache instance
        file_path: Optional specific file to query
        language: Language to use (required if file_path not provided)
        max_results: Maximum number of results to return
        include_snippets: Whether to include code snippets in results

    Returns:
        List of query matches
    """
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

                parser = language_registry.get_parser(language)
                tree = parser.parse(source_bytes)

                # Cache the tree
                tree_cache.put(abs_path, language, tree, source_bytes)

            # Execute query
            lang = language_registry.get_language(language)
            query = lang.query(query_string)

            from ..utils.tree_sitter_helpers import query_captures

            captures = query_captures(query, tree.root_node)

            # Handle different return formats from query.captures()
            if isinstance(captures, dict):
                # Dictionary format: {capture_name: [node1, node2, ...], ...}
                for capture_name, nodes in captures.items():
                    if capture_filter and capture_name != capture_filter:
                        continue

                    for node in nodes:
                        # Skip if we've reached max results
                        if max_results is not None and len(results) >= max_results:
                            break

                        try:
                            from ..utils.tree_sitter_helpers import get_node_text

                            text = get_node_text(node, source_bytes, decode=True)
                        except Exception:
                            text = "<binary data>"

                        if compact:
                            result: Dict[str, Any] = {"capture": capture_name, "text": text}
                        else:
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

                    if capture_filter and capture_name != capture_filter:
                        continue

                    # Skip if we've reached max results
                    if max_results is not None and len(results) >= max_results:
                        break

                    try:
                        from ..utils.tree_sitter_helpers import get_node_text

                        text = get_node_text(node, source_bytes, decode=True)
                    except Exception:
                        text = "<binary data>"

                    if compact:
                        result = {"capture": capture_name, "text": text}
                    else:
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
                    project,
                    query_string,
                    language_registry,
                    tree_cache,
                    rel_path,
                    language,
                    max_results if max_results is None else max_results - len(results),
                    include_snippets,
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


def _extract_ast_fingerprint(node: Any, source_bytes: bytes) -> set:
    """Extract a structural fingerprint from an AST node.

    The fingerprint is a set of (node_type, text) pairs for leaf nodes
    and node_type strings for interior nodes. This captures both the
    structure and the identifiers used in the code.
    """
    fingerprint: set = set()
    stack = [node]
    while stack:
        n = stack.pop()
        if n.child_count == 0:
            # Leaf node — include type and text
            text = source_bytes[n.start_byte : n.end_byte].decode("utf-8", errors="replace")
            fingerprint.add((n.type, text))
        else:
            # Interior node — include type
            fingerprint.add(n.type)
            for i in range(n.child_count):
                child = n.child(i)
                if child is not None:
                    stack.append(child)
    return fingerprint


def _iter_top_level_blocks(tree: Any) -> list:
    """Yield top-level definitions (functions, classes) and their children."""
    blocks = []
    root = tree.root_node
    for i in range(root.child_count):
        child = root.child(i)
        if child is None:
            continue
        blocks.append(child)
        # Also yield nested definitions (methods inside classes)
        if child.type in ("class_definition", "class_declaration", "impl_item"):
            for j in range(child.child_count):
                nested = child.child(j)
                if nested is not None and nested.type in (
                    "function_definition",
                    "function_declaration",
                    "method_definition",
                    "method_declaration",
                    "function_item",
                ):
                    blocks.append(nested)
    return blocks


def find_similar_code(
    project: Any,
    snippet: str,
    language_registry: Any,
    tree_cache: Any,
    language: Optional[str] = None,
    threshold: float = 0.6,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """Find code structurally similar to a snippet using AST fingerprinting.

    Parses the snippet and each candidate code block into ASTs, extracts
    structural fingerprints (node types + leaf identifiers), and computes
    containment similarity — what fraction of the snippet's fingerprint
    is found in each candidate block.

    Args:
        project: Project object
        snippet: Code snippet to find similar code for
        language_registry: Language registry
        tree_cache: Tree cache instance
        language: Language of the snippet
        threshold: Minimum containment similarity (0.0-1.0)
        max_results: Maximum number of results

    Returns:
        List of similar code blocks with similarity scores
    """
    if not language:
        raise QueryError("Language is required for find_similar_code")

    # Parse the snippet
    try:
        parser = language_registry.get_parser(language)
        snippet_bytes = snippet.encode("utf-8")
        snippet_tree = parser.parse(snippet_bytes)
        snippet_fp = _extract_ast_fingerprint(snippet_tree.root_node, snippet_bytes)
    except Exception as e:
        raise QueryError(f"Failed to parse snippet as {language}: {e}") from e

    if not snippet_fp:
        return []

    root = project.root_path
    results: List[Dict[str, Any]] = []

    # Find files for this language
    extensions = [ext for ext, lang in language_registry._language_map.items() if lang == language]
    if not extensions:
        raise QueryError(f"No file extensions found for language {language}")

    for ext in extensions:
        for file_path in root.glob(f"**/*.{ext}"):
            if not file_path.is_file():
                continue

            rel_path = str(file_path.relative_to(root))

            try:
                validate_file_access(file_path, root)

                # Parse file
                cached = tree_cache.get(file_path, language)
                if cached:
                    tree, source_bytes = cached
                else:
                    with open(file_path, "rb") as f:
                        source_bytes = f.read()
                    tree = parser.parse(source_bytes)
                    tree_cache.put(file_path, language, tree, source_bytes)

                # Compare each top-level block against the snippet
                for block in _iter_top_level_blocks(tree):
                    block_fp = _extract_ast_fingerprint(block, source_bytes)
                    if not block_fp:
                        continue

                    # Containment similarity: what fraction of the snippet's
                    # fingerprint is found in the candidate block. This handles
                    # asymmetric sizes well — a short snippet can match a long
                    # function if the snippet's structure is contained within it.
                    intersection = len(snippet_fp & block_fp)
                    similarity = intersection / len(snippet_fp) if snippet_fp else 0.0

                    if similarity >= threshold:
                        block_text = source_bytes[block.start_byte : block.end_byte].decode("utf-8", errors="replace")
                        results.append(
                            {
                                "file": rel_path,
                                "start": {"row": block.start_point[0], "column": block.start_point[1]},
                                "end": {"row": block.end_point[0], "column": block.end_point[1]},
                                "similarity": round(similarity, 3),
                                "node_type": block.type,
                                "text": block_text[:500],
                            }
                        )
            except (SecurityError, Exception):
                continue

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:max_results]
