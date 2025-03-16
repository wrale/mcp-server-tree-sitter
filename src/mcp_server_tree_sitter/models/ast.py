"""AST representation models for MCP server."""

from typing import Any, Dict, List, Optional, Tuple

from ..utils.tree_sitter_helpers import (
    cursor_walk_tree,
    get_node_text,
    walk_tree,
)
from ..utils.tree_sitter_types import Node, ensure_node


def node_to_dict(
    node: Any,
    source_bytes: Optional[bytes] = None,
    include_children: bool = True,
    include_text: bool = True,
    max_depth: int = 5,
) -> Dict[str, Any]:
    """
    Convert a tree-sitter node to a dictionary representation using cursor-based
    traversal.

    Args:
        node: Tree-sitter Node object
        source_bytes: Source code bytes
        include_children: Whether to include children nodes
        include_text: Whether to include node text
        max_depth: Maximum depth to traverse

    Returns:
        Dictionary representation of the node
    """
    safe_node = ensure_node(node)

    # Dictionary to store all node information keyed by node id
    nodes_dict: Dict[int, Dict[str, Any]] = {}
    # Track parent-child relationships
    children_map: Dict[int, List[int]] = {}
    # Keep track of node paths
    path_map: Dict[int, str] = {}

    # Root node ID
    root_id = id(safe_node)
    path_map[root_id] = ""

    def process_node(
        node: Optional[Node], field_name: Optional[str], depth: int
    ) -> bool:
        if node is None:
            return False

        node_id = id(node)
        parent_id = id(node.parent) if node.parent else None

        # Skip if beyond max depth
        if depth > max_depth:
            if parent_id is not None and parent_id in nodes_dict:
                # Store truncated info for parent
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(node_id)

                nodes_dict[node_id] = {
                    "type": node.type,
                    "truncated": True,
                    "children_count": len(node.children),
                }

                if parent_id in path_map:
                    path = path_map[parent_id]
                    child_path = f"{path}.{node.type}" if path else node.type
                    path_map[node_id] = child_path
                    nodes_dict[node_id]["path"] = child_path
            return False

        # Build node data
        node_data = {
            "type": node.type,
            "start_point": {"row": node.start_point[0], "column": node.start_point[1]},
            "end_point": {"row": node.end_point[0], "column": node.end_point[1]},
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
            "named": node.is_named,
            "children_count": len(node.children),
        }

        # Set path
        if parent_id is not None and parent_id in path_map:
            path = path_map[parent_id]
            if field_name:
                # Use field name if available
                child_path = f"{path}.{field_name}" if path else field_name
                node_data["field"] = field_name
            else:
                # Use node type otherwise
                child_path = f"{path}.{node.type}" if path else node.type

            path_map[node_id] = child_path
            node_data["path"] = child_path

        # Add text if source is available and requested
        if source_bytes and include_text:
            try:
                node_data["text"] = get_node_text(node, source_bytes)
            except Exception as e:
                node_data["text_error"] = str(e)

        # Store node data
        nodes_dict[node_id] = node_data

        # Track parent-child relationship for building the tree later
        if node.parent and include_children:
            parent_id = id(node.parent)
            if parent_id not in children_map:
                children_map[parent_id] = []
            if node.is_named:  # Only include named nodes
                children_map[parent_id].append(node_id)

        return True

    # Walk the tree using cursor
    cursor_walk_tree(safe_node, process_node)

    # Build the final tree from our dictionaries
    def build_tree(node_id: int) -> Dict[str, Any]:
        node_data = nodes_dict[node_id].copy()

        # Add children if they exist
        if (
            include_children
            and node_id in children_map
            and len(children_map[node_id]) > 0
        ):
            node_data["children"] = [
                build_tree(child_id) for child_id in children_map[node_id]
            ]

        return node_data

    # Return the root node with all its children
    return build_tree(root_id)


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
        if (
            cursor.node is not None
            and cursor.node.start_point <= point <= cursor.node.end_point
        ):
            current_best = cursor.node
            continue  # Continue to first child

        # If first child doesn't contain point, try siblings
        cursor.goto_parent()
        current_best = cursor.node  # Reset current best to parent

        # Try siblings
        found_in_sibling = False
        while cursor.goto_next_sibling():
            if (
                cursor.node is not None
                and cursor.node.start_point <= point <= cursor.node.end_point
            ):
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
