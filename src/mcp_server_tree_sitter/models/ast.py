"""AST representation models for MCP server.

This module provides functions for converting tree-sitter AST nodes to dictionaries,
finding nodes at specific positions, and other AST-related operations.
"""

from typing import Any, Dict, List, Optional, Tuple

from ..utils.tree_sitter_helpers import (
    get_node_text,
    walk_tree,
)
from ..utils.tree_sitter_types import ensure_node

# Import the cursor-based implementation
from .ast_cursor import node_to_dict_cursor


def node_to_dict(
    node: Any,
    source_bytes: Optional[bytes] = None,
    include_children: bool = True,
    include_text: bool = True,
    max_depth: int = 5,
) -> Dict[str, Any]:
    """
    Convert a tree-sitter node to a dictionary representation.

    This function now uses a cursor-based traversal approach for efficiency and
    reliability, especially with large ASTs that could cause stack overflow with
    recursive processing.

    Args:
        node: Tree-sitter Node object
        source_bytes: Source code bytes
        include_children: Whether to include children nodes
        include_text: Whether to include node text
        max_depth: Maximum depth to traverse

    Returns:
        Dictionary representation of the node
    """
    # Use the cursor-based implementation for improved reliability
    return node_to_dict_cursor(node, source_bytes, include_children, include_text, max_depth)


def summarize_node(node: Any, source_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Create a compact summary of a node without details or children.

    Args:
        node: Tree-sitter Node object
        source_bytes: Source code bytes

    Returns:
        Dictionary with basic node information
    """
    safe_node = ensure_node(node)

    result = {
        "type": safe_node.type,
        "start_point": {
            "row": safe_node.start_point[0],
            "column": safe_node.start_point[1],
        },
        "end_point": {"row": safe_node.end_point[0], "column": safe_node.end_point[1]},
    }

    # Add a short text snippet if source is available
    if source_bytes:
        try:
            # Use helper function to get text safely
            text = get_node_text(safe_node, source_bytes)
            lines = text.splitlines()
            if lines:
                snippet = lines[0][:50]
                if len(snippet) < len(lines[0]) or len(lines) > 1:
                    snippet += "..."
                result["preview"] = snippet
        except Exception:
            pass

    return result


def find_node_at_position(root_node: Any, row: int, column: int) -> Optional[Any]:
    """
    Find the most specific node at a given position using cursor-based traversal.

    Args:
        root_node: Root node to search from
        row: Row (line) number, 0-based
        column: Column number, 0-based

    Returns:
        The most specific node at the position, or None if not found
    """
    safe_node = ensure_node(root_node)
    point = (row, column)

    # Check if point is within root_node
    if not (safe_node.start_point <= point <= safe_node.end_point):
        return None

    # Find the smallest node that contains the point
    cursor = walk_tree(safe_node)
    current_best = cursor.node

    while cursor.goto_first_child():
        # If current node contains the point, it's better than the parent
        if cursor.node is not None and cursor.node.start_point <= point <= cursor.node.end_point:
            current_best = cursor.node
            continue  # Continue to first child

        # If first child doesn't contain point, try siblings
        cursor.goto_parent()
        current_best = cursor.node  # Reset current best to parent

        # Try siblings
        found_in_sibling = False
        while cursor.goto_next_sibling():
            if cursor.node is not None and cursor.node.start_point <= point <= cursor.node.end_point:
                current_best = cursor.node
                found_in_sibling = True
                break

        # If a sibling contains the point, continue to its children
        if found_in_sibling:
            continue
        else:
            # No child or sibling contains the point, we're done
            break

    return current_best


def extract_node_path(
    root_node: Any,
    target_node: Any,
) -> List[Tuple[str, Optional[str]]]:
    """
    Extract the path from root to a specific node using safe node handling.

    Args:
        root_node: Root node
        target_node: Target node

    Returns:
        List of (node_type, field_name) tuples from root to target
    """
    safe_root = ensure_node(root_node)
    safe_target = ensure_node(target_node)

    # If nodes are the same, return empty path
    if safe_root == safe_target:
        return []

    path = []
    current = safe_target

    while current != safe_root and current.parent:
        field_name = None

        # Find field name if any
        parent_field_names = getattr(current.parent, "children_by_field_name", {})
        if hasattr(parent_field_names, "items"):
            for name, nodes in parent_field_names.items():
                if current in nodes:
                    field_name = name
                    break

        path.append((current.type, field_name))
        current = current.parent

    # Add root node unless it's already the target
    if current == safe_root and path:
        path.append((safe_root.type, None))

    # Reverse to get root->target order
    return list(reversed(path))
