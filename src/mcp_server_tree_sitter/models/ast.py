"""AST representation models for MCP server."""

from typing import Any, Dict, List, Optional, Tuple


def node_to_dict(
    node,
    source_bytes: Optional[bytes] = None,
    include_children: bool = True,
    include_text: bool = True,
    depth: int = 0,
    max_depth: int = 5,
    field_path: str = "",
) -> Dict[str, Any]:
    """
    Convert a tree-sitter node to a dictionary representation.

    Args:
        node: Tree-sitter Node object
        source_bytes: Source code bytes
        include_children: Whether to include children nodes
        include_text: Whether to include node text
        depth: Current depth in the tree
        max_depth: Maximum depth to traverse
        field_path: Path of field names from root

    Returns:
        Dictionary representation of the node
    """
    if depth > max_depth:
        return {
            "type": node.type,
            "truncated": True,
            "path": field_path,
            "children_count": len(node.children),
        }

    result = {
        "type": node.type,
        "start_point": {"row": node.start_point[0], "column": node.start_point[1]},
        "end_point": {"row": node.end_point[0], "column": node.end_point[1]},
        "start_byte": node.start_byte,
        "end_byte": node.end_byte,
        "named": node.is_named,
    }

    # Add path information for better navigation
    if field_path:
        result["path"] = field_path

    # Add text if source is available and requested
    if source_bytes and include_text:
        try:
            result["text"] = source_bytes[node.start_byte : node.end_byte].decode(
                "utf-8", errors="replace"
            )
        except (IndexError, ValueError) as e:
            result["text_error"] = str(e)

    # Add current field name if available
    if node.parent:
        for field_name, field_nodes in node.parent.children_by_field_name.items():
            if node in field_nodes:
                result["field"] = field_name
                if not field_path:
                    field_path = field_name
                else:
                    field_path = f"{field_path}.{field_name}"
                break

    # Add named children for more compact representation
    if include_children and depth < max_depth:
        # Always include number of children for reference
        result["children_count"] = len(node.children)

        if node.named_children:
            result["children"] = []
            for child in node.named_children:
                child_path = f"{field_path}.{child.type}" if field_path else child.type
                result["children"].append(
                    node_to_dict(
                        child,
                        source_bytes,
                        include_children,
                        include_text,
                        depth + 1,
                        max_depth,
                        child_path,
                    )
                )

    return result


def summarize_node(node, source_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Create a compact summary of a node without details or children.

    Args:
        node: Tree-sitter Node object
        source_bytes: Source code bytes

    Returns:
        Dictionary with basic node information
    """
    result = {
        "type": node.type,
        "start_point": {"row": node.start_point[0], "column": node.start_point[1]},
        "end_point": {"row": node.end_point[0], "column": node.end_point[1]},
    }

    # Add a short text snippet if source is available
    if source_bytes:
        try:
            # Get the first line or up to 50 chars
            text = source_bytes[node.start_byte : node.end_byte].decode(
                "utf-8", errors="replace"
            )
            lines = text.splitlines()
            if lines:
                snippet = lines[0][:50]
                if len(snippet) < len(lines[0]) or len(lines) > 1:
                    snippet += "..."
                result["preview"] = snippet
        except (IndexError, ValueError):
            pass

    return result


def find_node_at_position(root_node, row: int, column: int) -> Optional[Any]:
    """
    Find the most specific node at a given position.

    Args:
        root_node: Root node to search from
        row: Row (line) number, 0-based
        column: Column number, 0-based

    Returns:
        The most specific node at the position, or None if not found
    """
    point = (row, column)

    # Check if point is within root_node
    if not (root_node.start_point <= point <= root_node.end_point):
        return None

    # Find the smallest node that contains the point
    cursor = root_node.walk()

    while cursor.goto_first_child():
        # If current node doesn't contain point, go back up and try next sibling
        if not (cursor.node.start_point <= point <= cursor.node.end_point):
            cursor.goto_parent()
            if not cursor.goto_next_sibling():
                break

            # If sibling doesn't contain point either, go back up
            if not (cursor.node.start_point <= point <= cursor.node.end_point):
                cursor.goto_parent()
                break

    return cursor.node


def extract_node_path(
    root_node,
    target_node,
) -> List[Tuple[str, Optional[str]]]:
    """
    Extract the path from root to a specific node.

    Args:
        root_node: Root node
        target_node: Target node

    Returns:
        List of (node_type, field_name) tuples from root to target
    """
    # If nodes are the same, return empty path
    if root_node == target_node:
        return []

    path = []
    current = target_node

    while current != root_node and current.parent:
        field_name = None

        # Find field name if any
        for name, nodes in current.parent.children_by_field_name.items():
            if current in nodes:
                field_name = name
                break

        path.append((current.type, field_name))
        current = current.parent

    # Add root node unless it's already the target
    if current == root_node and path:
        path.append((root_node.type, None))

    # Reverse to get root->target order
    return list(reversed(path))
