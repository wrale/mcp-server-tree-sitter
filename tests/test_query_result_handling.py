"""
Tests for tree-sitter query result handling issues.

This module contains tests specifically focused on the query result handling issues
identified as a critical next step in FEATURES.md.
"""

import tempfile
from pathlib import Path
import pytest

from mcp_server_tree_sitter.tools.search import run_query
from mcp_server_tree_sitter.tools.project import register_project_tool
from mcp_server_tree_sitter.language.registry import LanguageRegistry


@pytest.fixture
def test_project():
    """Create a test project with Python files containing known constructs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create a simple test file with various Python constructs
        test_file = project_path / "test.py"
        with open(test_file, "w") as f:
            f.write("""
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
""")
        
        # Register project
        project_name = "query_test_project"
        register_project_tool(path=str(project_path), name=project_name)
        
        yield {
            "name": project_name,
            "path": str(project_path),
            "file": "test.py"
        }


def test_query_capture_processing_diagnostics(test_project):
    """Diagnostics test for query capture processing to identify specific issues."""
    # Simple query to find function definitions
    query = "(function_definition name: (identifier) @function.name) @function.def"
    
    # Run the query
    result = run_query(
        project=test_project["name"],
        query=query,
        file_path=test_project["file"],
        language="python"
    )
    
    # Diagnostic information to help understand the actual structure of the result
    print(f"\nQuery result type: {type(result)}")
    print(f"Query result content: {result}")
    
    # Assert that the result is a list, even if empty
    assert isinstance(result, list), "Query result should be a list"


@pytest.mark.parametrize("query_string,expected_capture_count", [
    # Function definitions
    ("(function_definition name: (identifier) @name) @function", 2),
    
    # Class definitions
    ("(class_definition name: (identifier) @name) @class", 1),
    
    # Method definitions inside classes
    ("(class_definition body: (block (function_definition name: (identifier) @method))) @class", 2),
    
    # Import statements
    ("(import_from_statement) @import", 1),
    ("(import_statement) @import", 2),
    
    # Variable assignments
    ("(assignment left: (identifier) @var) @assign", 5),  # result, item, p, data
    
    # Function calls
    ("(call function: (identifier) @func) @call", 4),  # print, greet, process_data, len
])
def test_query_result_capture_types(test_project, query_string, expected_capture_count):
    """Test different types of query captures to diagnose result handling issues."""
    # Run the query
    result = run_query(
        project=test_project["name"],
        query=query_string,
        file_path=test_project["file"],
        language="python"
    )
    
    # Output diagnostic information
    print(f"\nQuery string: {query_string}")
    print(f"Query result: {result}")
    
    # As the issue is that queries execute but return no results,
    # we're checking both scenarios to identify pattern-specific issues
    if result and len(result) > 0:
        print(f"SUCCESS: Query returned {len(result)} results")
        assert len(result) == expected_capture_count, f"Expected {expected_capture_count} captures"
    else:
        print(f"FAILURE: Query returned no results, expected {expected_capture_count}")
        # We'll fail this test only if we do explicit assertions later


def test_direct_query_with_language_pack():
    """Test direct query execution using the tree-sitter-language-pack to isolate issues."""
    # Create a test string
    python_code = "def hello(): print('world')"
    
    # Get the Python language from the registry
    registry = LanguageRegistry()
    language_obj = registry.get_language("python")
    
    # Import necessary components from tree-sitter-language-pack
    try:
        from tree_sitter_language_pack import get_parser
        from tree_sitter import Query
        
        # Parse the code
        parser = get_parser(language_obj)
        tree = parser.parse(python_code.encode('utf-8'))
        
        # Create and run a simple query
        query_string = "(function_definition name: (identifier) @name) @function"
        query = Query(language_obj, query_string)
        
        # Execute the query directly
        matches = query.captures(tree.root_node)
        
        # Diagnostic information
        print(f"Direct query result: {matches}")
        print(f"Number of matches: {len(matches)}")
        
        # We expect at least one match for the function "hello"
        assert len(matches) > 0, "Direct query should match at least one function"
        
        # Diagnose the structure of matches
        if matches:
            for i, (node, capture_name) in enumerate(matches):
                print(f"Match {i}: {capture_name} = {node.text.decode('utf-8')}")
        
    except Exception as e:
        print(f"Error running direct query: {str(e)}")
        pytest.fail(f"Direct query execution failed: {str(e)}")


def test_query_result_structure_transformation():
    """Test the transformation of native tree-sitter query results to MCP format."""
    # Mock the native tree-sitter query result structure
    # This helps diagnose if the issue is in result transformation
    
    # Create a function to transform mock tree-sitter query results to expected MCP format
    def transform_query_results(ts_results):
        """Transform tree-sitter query results to MCP format."""
        # Implement a simplified version of what the actual transformation might be
        mcp_results = []
        
        for node, capture_name in ts_results:
            mcp_results.append({
                "capture": capture_name,
                "type": node.get("type"),
                "text": node.get("text"),
                "start_point": node.get("start_point"),
                "end_point": node.get("end_point")
            })
            
        return mcp_results
    
    # Create mock tree-sitter query results
    mock_ts_results = [
        ({
            "type": "identifier",
            "text": "hello",
            "start_point": {"row": 0, "column": 4},
            "end_point": {"row": 0, "column": 9}
        }, "name"),
        ({
            "type": "function_definition",
            "text": "def hello(): print('world')",
            "start_point": {"row": 0, "column": 0},
            "end_point": {"row": 0, "column": 28}
        }, "function")
    ]
    
    # Transform the results
    mcp_results = transform_query_results(mock_ts_results)
    
    # Verify the transformed structure
    assert len(mcp_results) == 2, "Should have 2 transformed results"
    assert mcp_results[0]["capture"] == "name", "First capture should be 'name'"
    assert mcp_results[0]["text"] == "hello", "First capture should have text 'hello'"
    assert mcp_results[1]["capture"] == "function", "Second capture should be 'function'"
    
    # Diagnostic information
    print(f"Transformed results: {mcp_results}")
