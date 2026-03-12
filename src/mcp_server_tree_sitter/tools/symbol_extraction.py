"""Symbol extraction from source files using tree-sitter queries."""

from typing import Any, Dict, Generator, List, Optional, Union

from ..exceptions import SecurityError
from ..language.import_enrichers import get_symbol_import_enricher
from ..language.loader import get_default_symbol_types
from ..language.query_templates import get_query_template
from ..language.registry import LanguageRegistry
from ..models.project import Project
from ..utils.security import validate_file_access
from ..utils.tree_sitter_helpers import (
    ensure_language,
    ensure_node,
    get_node_text,
    parse_with_cached_tree,
    run_query_captures,
)
from ..utils.tree_sitter_types import Node, Tree


def _node_location(node: Node) -> Dict[str, Any]:
    """Build location dict from a tree-sitter node."""
    return {
        "start": {"row": node.start_point[0], "column": node.start_point[1]},
        "end": {"row": node.end_point[0], "column": node.end_point[1]},
    }


def extract_symbols(
    project: Project,
    file_path: str,
    language_registry: LanguageRegistry,
    symbol_types: Optional[List[str]] = None,
    exclude_class_methods: bool = False,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract symbols (functions, classes, etc) from a file.

    Args:
        project: Project object
        file_path: Path to the file relative to project root
        language_registry: Language registry object
        symbol_types: Types of symbols to extract (functions, classes, imports, etc.)
        exclude_class_methods: Whether to exclude methods from function count

    Returns:
        Dictionary of symbols by type
    """
    abs_path = project.get_file_path(file_path)

    try:
        validate_file_access(abs_path, project.root_path)
    except SecurityError as e:
        raise SecurityError(f"Access denied: {e}") from e

    language = language_registry.language_for_file(file_path)
    if not language:
        raise ValueError(f"Could not detect language for {file_path}")

    # Default symbol types if not specified (from per-language config, or canonical default if language unknown)
    if symbol_types is None:
        symbol_types = get_default_symbol_types(language)

    # Get query templates for each symbol type
    queries = {}
    for symbol_type in symbol_types:
        template = get_query_template(language, symbol_type)
        if template:
            queries[symbol_type] = template

    if not queries:
        raise ValueError(f"No query templates available for {language} and {symbol_types}")

    # Parse file and extract symbols
    try:
        # Get language object
        language_obj = language_registry.get_language(language)
        safe_lang = ensure_language(language_obj)

        # Parse with cached tree
        tree, source_bytes = parse_with_cached_tree(abs_path, language, safe_lang)

        # Execute queries
        symbols: Dict[str, List[Dict[str, Any]]] = {}
        # Track class ranges to identify methods
        class_ranges = []

        # Process classes first if we need to filter out class methods
        if exclude_class_methods and "classes" in queries:
            if "classes" not in symbols:
                symbols["classes"] = []

            class_matches = run_query_captures(safe_lang, queries["classes"], tree.root_node)

            # Process class locations to identify their boundaries
            process_symbol_matches(class_matches, "classes", symbols, source_bytes, tree)

            # Extract class body ranges to check if functions are inside classes
            # Use a more generous range to ensure we catch all methods
            for class_symbol in symbols["classes"]:
                start_row = class_symbol["location"]["start"]["row"]
                # For class end, we need to estimate where the class body might end
                # by scanning the file for likely class boundaries
                source_lines = source_bytes.decode("utf-8", errors="replace").splitlines()
                # Find a reasonable estimate for where the class ends
                end_row = min(start_row + 30, len(source_lines) - 1)
                class_ranges.append((start_row, end_row))

        # Now process all symbol types
        for symbol_type, query_string in queries.items():
            # Skip classes if we already processed them
            if symbol_type == "classes" and exclude_class_methods and class_ranges:
                continue

            if symbol_type not in symbols:
                symbols[symbol_type] = []

            matches = run_query_captures(safe_lang, query_string, tree.root_node)

            process_symbol_matches(
                matches,
                symbol_type,
                symbols,
                source_bytes,
                tree,
                (class_ranges if exclude_class_methods and symbol_type == "functions" else None),
            )

            # Run language-specific import enricher if registered (e.g. Python aliased imports)
            if symbol_type == "imports":
                enricher = get_symbol_import_enricher(language)
                if enricher:
                    enricher(symbols, safe_lang, tree, source_bytes)

        return symbols

    except Exception as e:
        raise ValueError(f"Error extracting symbols from {file_path}: {e}") from e


def process_symbol_matches(
    matches: Union[Dict[str, List[Node]], List[Any]],
    symbol_type: str,
    symbols_dict: Dict[str, List[Dict[str, Any]]],
    source_bytes: bytes,
    tree: Tree,
    class_ranges: Optional[List[tuple[int, int]]] = None,
) -> None:
    """
    Process matches from a query and extract symbols.

    Args:
        matches: Query matches result
        symbol_type: Type of symbol being processed
        symbols_dict: Dictionary to store extracted symbols
        source_bytes: Source file bytes
        tree: Parsed syntax tree
        class_ranges: Optional list of class ranges to filter out class methods
    """

    # Helper function to check if a node is inside a class
    def is_inside_class(node_row: int) -> bool:
        if not class_ranges:
            return False
        for start_row, end_row in class_ranges:
            if start_row <= node_row <= end_row:
                return True
        return False

    # Track functions that should be filtered out (methods inside classes)
    filtered_methods: List[int] = []

    # Helper function to process a single node into a symbol
    def process_node(node: Node, capture_name: str) -> None:
        try:
            safe_node = ensure_node(node)

            # Skip methods inside classes if processing functions with class ranges
            if class_ranges is not None and is_inside_class(safe_node.start_point[0]):
                filtered_methods.append(safe_node.start_point[0])
                return

            # Special handling for imports
            if symbol_type == "imports":
                # For imports, accept more capture types (.module, .from, .item, .alias, etc.)
                if not (capture_name.startswith("import.") or capture_name == "import"):
                    return

                # For aliased imports, we want to include both the original name and the alias
                if capture_name == "import.alias":
                    # This is an alias in an import statement like "from datetime import datetime as dt"
                    # Get the module and item information
                    module_name = None
                    item_name = None

                    # Get the parent import_from_statement node
                    if safe_node.parent and safe_node.parent.parent:
                        import_node = safe_node.parent.parent
                        for child in import_node.children:
                            if child.type == "dotted_name":
                                # First dotted_name is usually the module
                                if module_name is None:
                                    module_name = get_node_text(child, source_bytes, decode=True)
                                # Look for the imported item
                                elif item_name is None and safe_node.parent and safe_node.parent.children:
                                    for item_child in safe_node.parent.children:
                                        if item_child.type == "dotted_name":
                                            item_name = get_node_text(item_child, source_bytes, decode=True)
                                            break

                    def _s(x: str | bytes) -> str:
                        return x.decode("utf-8") if isinstance(x, bytes) else x

                    alias_text = get_node_text(safe_node, source_bytes, decode=True)
                    if module_name and item_name:
                        text = f"{_s(module_name)}.{_s(item_name)} as {_s(alias_text)}"
                    elif module_name:
                        text = f"{_s(module_name)} as {_s(alias_text)}"
                    else:
                        text = alias_text
            # For other symbol types
            elif not capture_name.endswith(".name") and not capture_name == symbol_type:
                return

            text = get_node_text(safe_node, source_bytes, decode=True)

            symbol = {
                "name": text,
                "type": symbol_type,
                "location": _node_location(safe_node),
            }

            # Add to symbols list
            symbols_dict[symbol_type].append(symbol)

        except Exception:
            # Skip problematic nodes
            pass

    def iter_matches() -> Generator[tuple[Node, str], None, None]:
        if isinstance(matches, dict):
            for capture_name, nodes in matches.items():
                for node in nodes:
                    yield node, capture_name
        else:
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    yield match[0], match[1]
                elif hasattr(match, "node") and hasattr(match, "capture_name"):
                    yield match.node, match.capture_name
                elif isinstance(match, dict) and "node" in match and "capture" in match:
                    yield match["node"], match["capture"]

    for node, capture_name in iter_matches():
        process_node(node, capture_name)
