"""AST representation models using cursor-based traversal."""

from typing import Any, Dict, Optional

from ..utils.tree_sitter_helpers import (
    get_node_text,
    walk_tree,
)
from ..utils.tree_sitter_types import Node, ensure_node


def node_to_dict_cursor(
    node: Any,
    source_bytes: Optional[bytes] = None,
    include_children: bool = True,
    include_text: bool = True,
    max_depth: int = 5,
) -> Dict[str, Any]:
    """
    Convert a tree-sitter node to a dictionary using cursor-based traversal.

    This implementation avoids stack overflow issues for large ASTs by
    using cursor-based traversal instead of recursion.

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

    # Create a map to track node IDs
    node_map: Dict[int, Dict[str, Any]] = {}

    # Function to generate unique ID for a node
    def get_node_id(node: Node) -> int:
        return hash((node.start_byte, node.end_byte, node.type))

    # Initialize the root node data
    root_id = get_node_id(safe_node)
    root_data = {
        "id": root_id,
        "type": safe_node.type,
        "start_point": {
            "row": safe_node.start_point[0],
            "column": safe_node.start_point[1],
        },
        "end_point": {"row": safe_node.end_point[0], "column": safe_node.end_point[1]},
        "start_byte": safe_node.start_byte,
        "end_byte": safe_node.end_byte,
        "named": safe_node.is_named,
        "children": [],
        "children_count": 0,
    }

    # Add text if requested
    if source_bytes and include_text:
        try:
            root_data["text"] = get_node_text(safe_node, source_bytes)
        except Exception as e:
            root_data["text_error"] = str(e)

    # Add root to node map
    node_map[root_id] = root_data

    # Skip child processing if not requested or at max depth
    if not include_children or max_depth <= 0:
        return root_data

    # Get cursor at root
    cursor = walk_tree(safe_node)

    # Track current node data, parent stack, and depth
    current_data = root_data
    parent_stack = []
    current_depth = 0

    # Process a node and add it to node_map
    def process_node(current_node: Node, parent_data: Dict[str, Any], depth: int) -> Dict[str, Any]:
        node_id = get_node_id(current_node)

        # Return existing node data if already processed
        if node_id in node_map:
            return node_map[node_id]

        # Create node data
        node_data = {
            "id": node_id,
            "type": current_node.type,
            "start_point": {
                "row": current_node.start_point[0],
                "column": current_node.start_point[1],
            },
            "end_point": {
                "row": current_node.end_point[0],
                "column": current_node.end_point[1],
            },
            "start_byte": current_node.start_byte,
            "end_byte": current_node.end_byte,
            "named": current_node.is_named,
        }

        # Add text if requested
        if source_bytes and include_text:
            try:
                node_data["text"] = get_node_text(current_node, source_bytes)
            except Exception as e:
                node_data["text_error"] = str(e)

        # Handle children based on depth
        if depth < max_depth:
            node_data["children"] = []
            node_data["children_count"] = 0
        else:
            node_data["truncated"] = True

        # Add to node map
        node_map[node_id] = node_data

        # Add to parent's children list
        if parent_data and "children" in parent_data:
            parent_data["children"].append(node_data)
            parent_data["children_count"] = len(parent_data["children"])

        return node_data

    # Traversal state
    visited_children = False

    # Main traversal loop
    while True:
        # Try to visit children if not already visited and depth allows
        if not visited_children and current_depth < max_depth:
            if cursor.goto_first_child():
                # Process the child node
                current_depth += 1
                parent_stack.append(current_data)
                # Ensure node is not None before processing
                if cursor.node is not None:
                    current_data = process_node(cursor.node, current_data, current_depth)
                else:
                    visited_children = True
                continue
            else:
                # No children
                visited_children = True

        # Try next sibling if children visited
        elif cursor.goto_next_sibling():
            # Ensure node is not None before processing
            if cursor.node is not None:
                current_data = process_node(cursor.node, parent_stack[-1], current_depth)
            else:
                visited_children = True
            visited_children = False
            continue

        # Go back to parent if no more siblings
        elif parent_stack:
            cursor.goto_parent()
            current_data = parent_stack.pop()
            current_depth -= 1
            visited_children = True

            # If we're back at root level and finished all children, we're done
            if not parent_stack:
                break
        else:
            # No more nodes to process
            break

    return root_data
