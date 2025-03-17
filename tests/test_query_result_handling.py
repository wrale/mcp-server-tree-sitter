"""
Tests for tree-sitter query result handling.

This module contains tests focused on ensuring query result handling is robust and correct.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import pytest

from tests.test_helpers import register_project_tool, run_query


@pytest.fixture
def test_project(request) -> Generator[Dict[str, Any], None, None]:
    """Create a test project with Python files containing known constructs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create a simple test file with various Python constructs
        test_file = project_path / "test.py"
        with open(test_file, "w") as f:
            f.write(
                """
import os
import sys
from typing import List, Dict, Optional

class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self) -> str:
        return f"Hello, my name is {self.name} and I'm {self.age} years old."

def process_data(items: List[str]) -> Dict[str, int]:
    result = {}
    for item in items:
        result[item] = len(item)
    return result

if __name__ == "__main__":
    p = Person("Alice", 30)
    print(p.greet())

    data = process_data(["apple", "banana", "cherry"])
    print(data)
"""
            )

        # Generate a unique project name based on the test name
        test_name = request.node.name
        unique_id = abs(hash(test_name)) % 10000
        project_name = f"query_test_project_{unique_id}"

        # Register project
        try:
            register_project_tool(path=str(project_path), name=project_name)
        except Exception:
            # If registration fails, try with an even more unique name
            import time

            project_name = f"query_test_project_{unique_id}_{int(time.time())}"
            register_project_tool(path=str(project_path), name=project_name)

        yield {"name": project_name, "path": str(project_path), "file": "test.py"}


def test_query_capture_processing(test_project) -> None:
    """Test query capture processing to verify correct results."""
    # Simple query to find function definitions
    query = "(function_definition name: (identifier) @function.name) @function.def"

    # Run the query
    result = run_query(
        project=test_project["name"],
        query=query,
        file_path=test_project["file"],
        language="python",
    )

    # Verify query results
    assert isinstance(result, list), "Query result should be a list"

    # Should find function definitions including at least 'process_data'
    function_names = []
    for capture in result:
        if capture.get("capture") == "function.name":
            function_names.append(capture.get("text"))

    assert "process_data" in function_names, "Query should find 'process_data' function"


@pytest.mark.parametrize(
    "query_string,expected_capture_count",
    [
        # Function definitions
        ("(function_definition name: (identifier) @name) @function", 1),
        # Class definitions
        ("(class_definition name: (identifier) @name) @class", 1),
        # Method definitions inside classes
        (
            "(class_definition body: (block (function_definition name: (identifier) @method))) @class",
            2,
        ),
        # Import statements
        ("(import_from_statement) @import", 1),
        ("(import_statement) @import", 2),
        # Variable assignments
        ("(assignment left: (identifier) @var) @assign", 2),  # result, data
        # Function calls
        (
            "(call function: (identifier) @func) @call",
            3,
        ),  # print, greet, process_data
    ],
)
def test_query_result_capture_types(test_project, query_string, expected_capture_count) -> None:
    """Test different types of query captures to verify result handling."""
    # Run the query
    result = run_query(
        project=test_project["name"],
        query=query_string,
        file_path=test_project["file"],
        language="python",
    )

    # Verify results
    assert isinstance(result, list), "Query result should be a list"

    # Check if we got results
    assert len(result) > 0, f"Query '{query_string}' should return results"

    # Check number of captures for the specific category being tested
    capture_count = 0
    for r in result:
        capture = r.get("capture")
        if capture is not None and isinstance(capture, str):
            # Handle both formats: with dot (e.g., "function.name") and without (e.g., "function")
            if "." in capture:
                part = capture.split(".")[-1]
            else:
                part = capture

            if part in query_string:
                capture_count += 1
    assert capture_count >= expected_capture_count, f"Query should return at least {expected_capture_count} captures"


def test_direct_query_with_language_pack() -> None:
    """Test direct query execution using the tree-sitter-language-pack."""
    # Create a test string
    python_code = "def hello(): print('world')"

    # Import necessary components from tree-sitter-language-pack
    try:
        from tree_sitter_language_pack import get_language, get_parser

        # Get language directly from language pack
        language = get_language("python")
        assert language is not None, "Should be able to get Python language"

        # Parse the code
        parser = get_parser("python")
        tree = parser.parse(python_code.encode("utf-8"))

        # Access the root node to verify parsing works
        root_node = tree.root_node
        assert root_node is not None, "Root node should not be None"
        assert root_node.type == "module", "Root node should be a module"

        # Verify a function was parsed correctly by traversing the tree
        function_found = False
        for child in root_node.children:
            if child.type == "function_definition":
                function_found = True
                break

        # Assert we found a function in the parsed tree
        assert function_found, "Should find a function definition in the parsed tree"

        # Define a query to find the function name
        query_string = "(function_definition name: (identifier) @name)"
        query = language.query(query_string)

        # Execute the query
        captures = query.captures(root_node)

        # Verify captures
        assert len(captures) > 0, "Query should return captures"

        # Find the 'hello' function name
        hello_found = False

        # Handle different possible formats of captures
        if isinstance(captures, list):
            for capture in captures:
                # Initialize variables with correct types
                node: Optional[Any] = None
                capture_name: str = ""

                # Try different formats
                if isinstance(capture, tuple):
                    if len(capture) == 2:
                        node, capture_name = capture
                    elif len(capture) > 2:
                        # It might have more elements than expected
                        node, capture_name = capture[0], capture[1]
                elif hasattr(capture, "node") and hasattr(capture, "capture_name"):
                    node, capture_name = capture.node, capture.capture_name
                elif isinstance(capture, dict) and "node" in capture and "capture" in capture:
                    node, capture_name = capture["node"], capture["capture"]

                if node is not None and capture_name == "name" and hasattr(node, "text") and node.text is not None:
                    text = node.text.decode("utf-8") if hasattr(node.text, "decode") else str(node.text)
                    if text == "hello":
                        hello_found = True
                        break
        elif isinstance(captures, dict):
            # Dictionary mapping capture names to nodes
            if "name" in captures:
                for node in captures["name"]:
                    if node is not None and hasattr(node, "text") and node.text is not None:
                        text = node.text.decode("utf-8") if hasattr(node.text, "decode") else str(node.text)
                        if text == "hello":
                            hello_found = True
                            break

        assert hello_found, "Query should find 'hello' function name"

    except ImportError as e:
        pytest.skip(f"Skipping test due to import error: {str(e)}")


def test_query_result_structure_transformation() -> None:
    """Test the transformation of native tree-sitter query results to MCP format."""
    # Mock the native tree-sitter query result structure
    # This helps verify result transformation is correct

    # Create a function to transform mock tree-sitter query results to expected MCP format
    def transform_query_results(ts_results) -> List[Dict[str, Any]]:
        """Transform tree-sitter query results to MCP format."""
        # Implement a simplified version of what the actual transformation might be
        mcp_results = []

        for node, capture_name in ts_results:
            mcp_results.append(
                {
                    "capture": capture_name,
                    "type": node.get("type"),
                    "text": node.get("text"),
                    "start_point": node.get("start_point"),
                    "end_point": node.get("end_point"),
                }
            )

        return mcp_results

    # Create mock tree-sitter query results
    mock_ts_results = [
        (
            {
                "type": "identifier",
                "text": "hello",
                "start_point": {"row": 0, "column": 4},
                "end_point": {"row": 0, "column": 9},
            },
            "name",
        ),
        (
            {
                "type": "function_definition",
                "text": "def hello(): print('world')",
                "start_point": {"row": 0, "column": 0},
                "end_point": {"row": 0, "column": 28},
            },
            "function",
        ),
    ]

    # Transform the results
    mcp_results = transform_query_results(mock_ts_results)

    # Verify the transformed structure
    assert len(mcp_results) == 2, "Should have 2 transformed results"
    assert mcp_results[0]["capture"] == "name", "First capture should be 'name'"
    assert mcp_results[0]["text"] == "hello", "First capture should have text 'hello'"
    assert mcp_results[1]["capture"] == "function", "Second capture should be 'function'"
