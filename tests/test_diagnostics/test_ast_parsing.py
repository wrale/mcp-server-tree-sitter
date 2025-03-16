"""Pytest-based diagnostic tests for AST parsing functionality."""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from mcp_server_tree_sitter.language.registry import LanguageRegistry
from mcp_server_tree_sitter.models.ast import node_to_dict
from mcp_server_tree_sitter.models.project import ProjectRegistry
from mcp_server_tree_sitter.resources.ast import parse_file
from mcp_server_tree_sitter.server import get_ast


@pytest.fixture
def test_project() -> Generator[Dict[str, Any], None, None]:
    """Create a temporary test project with a sample file."""
    # Set up a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create a test file
        test_file = project_path / "test.py"
        with open(test_file, "w") as f:
            f.write("def hello():\n    print('Hello, world!')\n\nhello()\n")

        # Register project
        project_registry = ProjectRegistry()
        project_name = "ast_test_project"
        project_registry.register_project(project_name, str(project_path))

        # Yield the project info
        yield {"name": project_name, "path": project_path, "file": "test.py"}

        # Clean up
        project_registry.remove_project(project_name)


@pytest.mark.diagnostic
def test_get_ast_functionality(test_project, diagnostic) -> None:
    """Test the get_ast MCP tool functionality."""
    # Add test details to diagnostic data
    diagnostic.add_detail("project", test_project["name"])
    diagnostic.add_detail("file", test_project["file"])

    try:
        # Try to get the AST using the MCP tool
        ast_result = get_ast(
            project=test_project["name"],
            path=test_project["file"],
            max_depth=3,
            include_text=True,
        )

        # Record success details
        diagnostic.add_detail("ast_result_status", "success")
        diagnostic.add_detail("ast_result_keys", list(ast_result.keys()))

        # This assertion would fail if there's an issue with AST parsing
        assert "tree" in ast_result, "AST result should contain a tree"
        assert "file" in ast_result, "AST result should contain file info"
        assert "language" in ast_result, "AST result should contain language info"

        # Check that the tree doesn't contain an error
        if isinstance(ast_result["tree"], dict) and "error" in ast_result["tree"]:
            raise AssertionError(f"AST tree contains an error: {ast_result['tree']['error']}")

    except Exception as e:
        # Record the error in diagnostics
        diagnostic.add_error("AstParsingError", str(e))

        # Create an artifact with detailed information
        artifact = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "project": test_project["name"],
            "file": test_project["file"],
        }
        diagnostic.add_artifact("ast_failure", artifact)

        # Re-raise to fail the test
        raise


@pytest.mark.diagnostic
def test_direct_parsing(test_project, diagnostic) -> None:
    """Test lower-level parse_file function to isolate issues."""
    file_path = test_project["path"] / test_project["file"]
    diagnostic.add_detail("file_path", str(file_path))

    try:
        # Get language
        registry = LanguageRegistry()
        language = registry.language_for_file(test_project["file"])
        assert language is not None, "Could not detect language for file"
        language_obj = None

        try:
            language_obj = registry.get_language(language)
            diagnostic.add_detail("language_loaded", True)
            diagnostic.add_detail("language", language)
        except Exception as e:
            diagnostic.add_detail("language_loaded", False)
            diagnostic.add_error("LanguageLoadError", str(e))
            pytest.fail(f"Failed to load language: {e}")

        # Try direct parsing if language is loaded
        if language_obj:
            try:
                tree, source_bytes = parse_file(file_path, language) if language is not None else (None, None)

                parsing_info = {
                    "status": "success",
                    "tree_type": type(tree).__name__,
                    "has_root_node": hasattr(tree, "root_node"),
                }
                diagnostic.add_detail("parsing", parsing_info)

                # Try to access the root node
                if hasattr(tree, "root_node"):
                    root = tree.root_node
                    root_info = {
                        "type": root.type,
                        "start_byte": root.start_byte,
                        "end_byte": root.end_byte,
                        "child_count": (len(root.children) if hasattr(root, "children") else -1),
                    }
                    diagnostic.add_detail("root_node", root_info)

                    # Try to convert to dict
                    try:
                        node_dict = node_to_dict(root, source_bytes, max_depth=2)
                        diagnostic.add_detail(
                            "node_to_dict",
                            {
                                "status": "success",
                                "keys": list(node_dict.keys()),
                            },
                        )

                        # Assert dictionary structure
                        assert "type" in node_dict, "node_dict should contain type"
                        assert "children" in node_dict or "truncated" in node_dict, (
                            "node_dict should contain children or be truncated"
                        )

                        # Check for error in node dictionary
                        if "error" in node_dict:
                            raise AssertionError(f"node_dict contains an error: {node_dict['error']}")

                    except Exception as e:
                        diagnostic.add_error("NodeToDictError", str(e))
                        pytest.fail(f"node_to_dict failed: {e}")

                else:
                    diagnostic.add_error("NoRootNodeError", "Tree has no root_node attribute")
                    pytest.fail("Tree has no root_node attribute")

            except Exception as e:
                diagnostic.add_error("ParsingError", str(e))
                pytest.fail(f"Direct parsing failed: {e}")

    except Exception as e:
        # Catch any unexpected errors
        diagnostic.add_error("UnexpectedError", str(e))
        raise

    diagnostic.add_detail("test_completed", True)
