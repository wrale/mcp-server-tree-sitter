"""Test the cursor-based AST implementation."""

import tempfile
from pathlib import Path

from mcp_server_tree_sitter.language.registry import LanguageRegistry
from mcp_server_tree_sitter.models.ast_cursor import node_to_dict_cursor
from mcp_server_tree_sitter.utils.file_io import read_binary_file
from mcp_server_tree_sitter.utils.tree_sitter_helpers import create_parser, parse_source


def test_cursor_based_ast() -> None:
    """Test that the cursor-based AST node_to_dict function works."""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+") as f:
        f.write("def hello():\n    print('Hello, world!')\n\nhello()\n")
        f.flush()

        file_path = Path(f.name)

        # Set up language registry
        registry = LanguageRegistry()
        language = registry.language_for_file(file_path.name)
        assert language is not None, "Could not detect language for test file"
        language_obj = registry.get_language(language)

        # Parse the file
        parser = create_parser(language_obj)
        source_bytes = read_binary_file(file_path)
        tree = parse_source(source_bytes, parser)

        # Get AST using cursor-based approach
        cursor_ast = node_to_dict_cursor(tree.root_node, source_bytes, max_depth=3)

        # Basic validation
        assert "id" in cursor_ast, "AST should include node ID"
        assert cursor_ast["type"] == "module", "Root node should be a module"
        assert "children" in cursor_ast, "AST should include children"
        assert len(cursor_ast["children"]) > 0, "AST should have at least one child"

        # Check function definition
        if cursor_ast["children"]:
            function_node = cursor_ast["children"][0]
            assert function_node["type"] == "function_definition", "Expected function definition"

            # Check if children are properly included
            assert "children" in function_node, "Function should have children"
            assert function_node["children_count"] > 0, "Function should have children"

            # Verify some function components exist
            function_children_types = [child["type"] for child in function_node["children"]]
            assert "identifier" in function_children_types, "Function should have identifier"

            # Verify text extraction works if available
            if "text" in function_node:
                # Check for 'hello' in the text, handling both string and bytes
                if isinstance(function_node["text"], bytes):
                    assert b"hello" in function_node["text"], "Function text should contain 'hello'"
                else:
                    assert "hello" in function_node["text"], "Function text should contain 'hello'"


if __name__ == "__main__":
    test_cursor_based_ast()
    print("All tests passed!")
