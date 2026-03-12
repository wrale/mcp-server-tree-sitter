"""AST representation models for MCP server.

This module provides functions for converting tree-sitter AST nodes to dictionaries,
finding nodes at specific positions, and other AST-related operations.
"""

from typing import Any, Dict, List, Optional

from ..language.scope_node_types import get_enclosure_node_types, node_type_to_kind
from ..utils.tree_sitter_helpers import (
    get_node_text,
    walk_tree,
)
from ..utils.tree_sitter_types import Node, ensure_node

# Import the cursor-based implementation
from .ast_cursor import node_to_dict_cursor


def node_to_dict(
    node: Node,
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


def summarize_node(node: Node, source_bytes: Optional[bytes] = None) -> Dict[str, Any]:
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
            # Use helper function to get text safely - make sure to decode
            text = get_node_text(safe_node, source_bytes, decode=True)
            if isinstance(text, bytes):
                text = text.decode("utf-8", errors="replace")
            lines = text.splitlines()
            if lines:
                snippet = lines[0][:50]
                if len(snippet) < len(lines[0]) or len(lines) > 1:
                    snippet += "..."
                result["preview"] = snippet
        except Exception:
            pass

    return result


def find_node_at_position(root_node: Node, row: int, column: int) -> Optional[Node]:
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

    # Special handling for function definitions and identifiers
    def check_for_specific_nodes(node: Node) -> Optional[Node]:
        # For function definitions, check if position is over the function name
        if node.type == "function_definition":
            for child in node.children:
                if child.type in ["identifier", "name"]:
                    if (
                        child.start_point[0] <= row <= child.end_point[0]
                        and child.start_point[1] <= column <= child.end_point[1]
                    ):
                        return child
        return None

    # First check if we have a specific node like a function name
    specific_node = check_for_specific_nodes(safe_node)
    if specific_node:
        return specific_node

    while cursor.goto_first_child():
        # If current node contains the point, it's better than the parent
        if cursor.node is not None and cursor.node.start_point <= point <= cursor.node.end_point:
            current_best = cursor.node

            # Check for specific nodes like identifiers
            specific_node = check_for_specific_nodes(cursor.node)
            if specific_node:
                return specific_node

            continue  # Continue to first child

        # Try siblings
        found_in_sibling = False
        while cursor.goto_next_sibling():
            if cursor.node is not None and cursor.node.start_point <= point <= cursor.node.end_point:
                current_best = cursor.node

                # Check for specific nodes
                specific_node = check_for_specific_nodes(cursor.node)
                if specific_node:
                    return specific_node

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
    root_node: Node,
    target_node: Node,
) -> List[tuple[str, Optional[str]]]:
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


def find_enclosing_scope(
    root_node: Node,
    source_bytes: bytes,
    row: int,
    column: int,
    label: str,
    language: str,
    max_lines: int = 0,
) -> Dict[str, Any]:
    """
    Find the enclosing scope (function, class, or module) for a position and return its block info.

    Used by get_enclosing_scope(project, path, row, column); does not depend on project or file path.

    Args:
        root_node: Root node of the parsed tree.
        source_bytes: Source code bytes.
        row: Row (0-based).
        column: Column (0-based).
        label: Text label at the position
        language: Language id (e.g. "python", "javascript").
        max_lines: Maximum number of lines to return (0 = no limit). When exceeded,
                  returns a centered window around the target row with truncation markers.

    Returns:
        Dict with keys: kind, text, start_line, end_line, truncated.

    TODO:
    - We are not checking the label against the node text. This could be an enhancement to ensure we are returning
      a scope that actually contains the label, or find nearest scope that contains the label if the position is not
      accurate.
    """
    safe_root = ensure_node(root_node)
    node = find_node_at_position(safe_root, row, column)

    if node is None:
        # We didn't find any node. This should only happen if the position is outside the root node's span.
        # In that case, we will return None.
        return dict()

    enclosure_types = set(get_enclosure_node_types(language))

    # Lookup the node and its ancestors until we find one in the enclosure list
    # (function, class, module), or we reach the root.
    while node is not None:
        if node.type in enclosure_types:
            break
        node = node.parent

    # If we reached the root without finding an enclosure node, we will use the root as the scope node.
    scope_node = safe_root if node is None else node

    # Resolve kind from node type; extract name (e.g. Python/JS: "name" or "identifier" child).
    scope_kind = node_type_to_kind(language, scope_node.type)

    # Set text and start_line/end_line (0-based), return dict.
    text = get_node_text(scope_node, source_bytes, decode=True)
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")

    start_line = scope_node.start_point[0]
    end_line = scope_node.end_point[0]

    # Apply truncation if max_lines is set and scope exceeds it
    truncated = False
    if max_lines > 0 and (end_line - start_line + 1) > max_lines:
        truncated = True
        text, start_line, end_line = _truncate_scope_text(text, start_line, end_line, row, max_lines)

    return {
        "kind": scope_kind.value,
        "text": text,
        "start_line": start_line,
        "end_line": end_line,
        "truncated": truncated,
    }


def _truncate_scope_text(
    text: str,
    original_start_line: int,
    original_end_line: int,
    target_row: int,
    max_lines: int,
) -> tuple[str, int, int]:
    """
    Truncate scope text to max_lines, centered around target_row.

    Args:
        text: Full scope text
        original_start_line: Original start line (0-based)
        original_end_line: Original end line (0-based)
        target_row: Target row to center around (0-based)
        max_lines: Maximum number of lines to keep

    Returns:
        Tuple of (truncated_text, new_start_line, new_end_line)
    """
    lines = text.splitlines(keepends=True)
    total_lines = len(lines)

    # Calculate the target line within the scope
    target_line_in_scope = target_row - original_start_line
    target_line_in_scope = max(0, min(target_line_in_scope, total_lines - 1))

    # Calculate window: keep max_lines/2 before and after target
    half_window = max_lines // 2
    window_start = max(0, target_line_in_scope - half_window)
    window_end = min(total_lines, window_start + max_lines)

    # Adjust window_start if we hit the end
    if window_end - window_start < max_lines:
        window_start = max(0, window_end - max_lines)

    # Build truncated text with markers
    result_lines = []

    # Add marker for omitted lines at the start
    if window_start > 0:
        result_lines.append(f"// ... {window_start} lines omitted ...\n")

    # Add the window of lines
    result_lines.extend(lines[window_start:window_end])

    # Add marker for omitted lines at the end
    omitted_at_end = total_lines - window_end
    if omitted_at_end > 0:
        result_lines.append(f"// ... {omitted_at_end} lines omitted ...\n")

    truncated_text = "".join(result_lines)
    new_start_line = original_start_line + window_start
    new_end_line = original_start_line + window_end - 1

    return truncated_text, new_start_line, new_end_line
