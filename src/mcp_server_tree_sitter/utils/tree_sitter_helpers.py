"""Helper functions for tree-sitter operations.

This module provides wrappers and utility functions for common tree-sitter operations
to ensure type safety and consistent handling of tree-sitter objects.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from ..cache.parser_cache import tree_cache
from ..utils.file_io import read_binary_file
from ..utils.tree_sitter_types import (
    Language,
    Node,
    Parser,
    Tree,
    TreeCursor,
    ensure_cursor,
    ensure_language,
    ensure_node,
    ensure_parser,
    ensure_tree,
)

T = TypeVar("T")


def create_parser(language_obj: Any) -> Parser:
    """
    Create a parser configured for a specific language.

    Args:
        language_obj: Language object

    Returns:
        Configured Parser
    """
    parser = Parser()
    safe_language = ensure_language(language_obj)

    # Try both set_language and language methods
    try:
        parser.set_language(safe_language)  # type: ignore
    except AttributeError:
        if hasattr(parser, "language"):
            # Use the language method if available
            parser.language = safe_language  # type: ignore
        else:
            # Fallback to setting the attribute directly
            parser.language = safe_language  # type: ignore

    return ensure_parser(parser)


def parse_source(parser: Parser, source: bytes) -> Tree:
    """
    Parse source code using a configured parser.

    Args:
        parser: Configured Parser object
        source: Source code as bytes

    Returns:
        Parsed Tree
    """
    safe_parser = ensure_parser(parser)
    tree = safe_parser.parse(source)
    return ensure_tree(tree)


def parse_source_incremental(parser: Parser, source: bytes, old_tree: Optional[Tree] = None) -> Tree:
    """
    Parse source code incrementally using a configured parser.

    Args:
        parser: Configured Parser object
        source: Source code as bytes
        old_tree: Previous tree for incremental parsing

    Returns:
        Parsed Tree
    """
    safe_parser = ensure_parser(parser)
    tree = safe_parser.parse(source, old_tree)
    return ensure_tree(tree)


def edit_tree(
    tree: Tree,
    start_byte: int,
    old_end_byte: int,
    new_end_byte: int,
    start_point: Tuple[int, int],
    old_end_point: Tuple[int, int],
    new_end_point: Tuple[int, int],
) -> Tree:
    """
    Edit a syntax tree to reflect source code changes.

    Args:
        tree: Tree to edit
        start_byte: Start byte of the edit
        old_end_byte: End byte of the old text
        new_end_byte: End byte of the new text
        start_point: Start point (row, column) of the edit
        old_end_point: End point of the old text
        new_end_point: End point of the new text

    Returns:
        Edited tree
    """
    safe_tree = ensure_tree(tree)
    safe_tree.edit(
        start_byte=start_byte,
        old_end_byte=old_end_byte,
        new_end_byte=new_end_byte,
        start_point=start_point,
        old_end_point=old_end_point,
        new_end_point=new_end_point,
    )
    return safe_tree


def get_changed_ranges(old_tree: Tree, new_tree: Tree) -> List[Dict[str, Any]]:
    """
    Get changed ranges between two syntax trees.

    Args:
        old_tree: Old syntax tree
        new_tree: New syntax tree

    Returns:
        List of changed ranges with start and end points
    """
    safe_old_tree = ensure_tree(old_tree)
    safe_new_tree = ensure_tree(new_tree)

    # Note: This is a simplified implementation as tree_sitter Python
    # binding might not expose changed_ranges directly
    # In a real implementation, you would call:
    # ranges = old_tree.changed_ranges(new_tree)

    # For now, return a basic comparison at the root level
    old_root = safe_old_tree.root_node
    new_root = safe_new_tree.root_node

    if old_root.start_byte != new_root.start_byte or old_root.end_byte != new_root.end_byte:
        # Return the entire tree as changed
        return [
            {
                "start_point": {
                    "row": new_root.start_point[0],
                    "column": new_root.start_point[1],
                },
                "end_point": {
                    "row": new_root.end_point[0],
                    "column": new_root.end_point[1],
                },
                "start_byte": new_root.start_byte,
                "end_byte": new_root.end_byte,
            }
        ]

    return []


def parse_file(file_path: Path, parser: Parser) -> Tuple[Tree, bytes]:
    """
    Parse a file using a configured parser.

    Args:
        file_path: Path to the file
        parser: Configured Parser object

    Returns:
        Tuple of (Tree, source_bytes)
    """
    source_bytes = read_binary_file(file_path)
    tree = parse_source(parser, source_bytes)
    return tree, source_bytes


def get_node_text(node: Node, source_bytes: bytes) -> str:
    """
    Safely get text for a node from source bytes.

    Args:
        node: Node object
        source_bytes: Source code as bytes

    Returns:
        Text for the node
    """
    safe_node = ensure_node(node)
    try:
        return source_bytes[safe_node.start_byte : safe_node.end_byte].decode("utf-8", errors="replace")
    except (IndexError, ValueError):
        return ""


def walk_tree(node: Node) -> TreeCursor:
    """
    Get a cursor for walking a tree from a node.

    Args:
        node: Node to start from

    Returns:
        Tree cursor
    """
    safe_node = ensure_node(node)
    cursor = safe_node.walk()
    return ensure_cursor(cursor)


def cursor_walk_tree(node: Node, visit_fn: Callable[[Optional[Node], Optional[str], int], bool]) -> None:
    """
    Walk a tree using cursor for efficiency.

    Args:
        node: Root node to start from
        visit_fn: Function called for each node, receives (node, field_name, depth)
                  Return True to continue traversal, False to skip children
    """
    cursor = walk_tree(node)
    field_name = None
    depth = 0

    if not visit_fn(cursor.node, field_name, depth):
        return

    if cursor.goto_first_child():
        depth += 1

        while True:
            # Get field name if available
            field_name = None
            if cursor.node and cursor.node.parent:
                parent_field_names = getattr(cursor.node.parent, "children_by_field_name", {})
                if hasattr(parent_field_names, "items"):
                    for name, nodes in parent_field_names.items():
                        if cursor.node in nodes:
                            field_name = name
                            break

            if visit_fn(cursor.node, field_name, depth):
                # Visit children
                if cursor.goto_first_child():
                    depth += 1
                    continue

            # No children or children skipped, try siblings
            if cursor.goto_next_sibling():
                continue

            # No more siblings, go up
            while depth > 0:
                cursor.goto_parent()
                depth -= 1

                if cursor.goto_next_sibling():
                    break

            # If we've returned to the root, we're done
            if depth == 0:
                break


def collect_with_cursor(
    node: Node,
    collector_fn: Callable[[Optional[Node], Optional[str], int], Optional[T]],
) -> List[T]:
    """
    Collect items from a tree using cursor traversal.

    Args:
        node: Root node to start from
        collector_fn: Function that returns an item to collect or None to skip
                     Receives (node, field_name, depth)

    Returns:
        List of collected items
    """
    items: List[T] = []

    def visit(node: Optional[Node], field_name: Optional[str], depth: int) -> bool:
        if node is None:
            return False
        item = collector_fn(node, field_name, depth)
        if item is not None:
            items.append(item)
        return True  # Continue traversal

    cursor_walk_tree(node, visit)
    return items


def find_nodes_by_type(root_node: Node, node_type: str) -> List[Node]:
    """
    Find all nodes of a specific type in a tree.

    Args:
        root_node: Root node to search from
        node_type: Type of node to find

    Returns:
        List of matching nodes
    """

    def collector(node: Optional[Node], _field_name: Optional[str], _depth: int) -> Optional[Node]:
        if node is None:
            return None
        if node.type == node_type:
            return node
        return None

    return collect_with_cursor(root_node, collector)


def get_node_descendants(node: Optional[Node], max_depth: Optional[int] = None) -> List[Node]:
    """
    Get all descendants of a node.

    Args:
        node: Node to get descendants for
        max_depth: Maximum depth to traverse

    Returns:
        List of descendant nodes
    """
    descendants: List[Node] = []

    if node is None:
        return descendants

    def visit(node: Optional[Node], _field_name: Optional[str], depth: int) -> bool:
        if node is None:
            return False
        if max_depth is not None and depth > max_depth:
            return False  # Skip children

        if depth > 0:  # Skip the root node
            descendants.append(node)

        return True  # Continue traversal

    cursor_walk_tree(node, visit)
    return descendants


def parse_with_cached_tree(file_path: Path, language: str, language_obj: Language) -> Tuple[Tree, bytes]:
    """
    Parse a file with tree caching.

    Args:
        file_path: Path to the file
        language: Language identifier
        language_obj: Language object

    Returns:
        Tuple of (Tree, source_bytes)
    """
    # Check if we have a cached tree
    cached = tree_cache.get(file_path, language)
    if cached:
        return cached

    # Parse the file
    parser = create_parser(language_obj)
    tree, source_bytes = parse_file(file_path, parser)

    # Cache the tree
    tree_cache.put(file_path, language, tree, source_bytes)

    return tree, source_bytes


def update_cached_tree(
    file_path: Path,
    language: str,
    language_obj: Language,
    start_byte: int,
    old_end_byte: int,
    new_end_byte: int,
    start_point: Tuple[int, int],
    old_end_point: Tuple[int, int],
    new_end_point: Tuple[int, int],
) -> Optional[Tuple[Tree, bytes]]:
    """
    Update a cached tree with edit operation.

    Args:
        file_path: Path to the source file
        language: Language identifier
        language_obj: Language object
        start_byte, old_end_byte, new_end_byte: Byte positions of edit
        start_point, old_end_point, new_end_point: Row/column positions of edit

    Returns:
        Updated (tree, source_bytes) if successful, None otherwise
    """
    # Check if we have a cached tree
    cached = tree_cache.get(file_path, language)
    if not cached:
        return None

    old_tree, old_source = cached

    try:
        # Apply edit to the tree
        edit_tree(
            old_tree,
            start_byte=start_byte,
            old_end_byte=old_end_byte,
            new_end_byte=new_end_byte,
            start_point=start_point,
            old_end_point=old_end_point,
            new_end_point=new_end_point,
        )

        # Read updated source
        with open(file_path, "rb") as f:
            new_source = f.read()

        # Parse incrementally
        parser = create_parser(language_obj)
        new_tree = parse_source_incremental(parser, new_source, old_tree)

        # Update cache
        tree_cache.put(file_path, language, new_tree, new_source)

        return new_tree, new_source
    except Exception:
        # If incremental parsing fails, fall back to full parse
        return parse_with_cached_tree(file_path, language, language_obj)
