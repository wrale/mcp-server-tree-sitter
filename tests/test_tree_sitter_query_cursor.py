"""
Tests for tree-sitter QueryCursor API compatibility (issue #25).

This module tests that the QueryCursor API works correctly with tree-sitter 0.25.1+
and that the execute_query_captures() helper provides proper compatibility.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from mcp_server_tree_sitter.utils.tree_sitter_helpers import execute_query_captures
from mcp_server_tree_sitter.utils.tree_sitter_types import HAS_QUERY_CURSOR, Query, QueryCursor
from tests.test_helpers import register_project_tool, run_query


def test_query_cursor_available() -> None:
    """Test that QueryCursor is available in the current tree-sitter version."""
    assert HAS_QUERY_CURSOR, "QueryCursor should be available in tree-sitter 0.25.1+"

    # Verify we can import and use QueryCursor with a query
    try:
        from tree_sitter_language_pack import get_language

        language = get_language("python")
        query = language.query("(function_definition) @func")

        # QueryCursor requires query in constructor
        cursor = QueryCursor(query)
        assert cursor is not None, "Should be able to create QueryCursor instance"
    except ImportError:
        pytest.skip("tree-sitter-language-pack not available")
    except Exception as e:
        pytest.fail(f"Failed to use QueryCursor: {e}")


def test_execute_query_captures_with_python() -> None:
    """Test execute_query_captures() with Python code."""
    try:
        from tree_sitter_language_pack import get_language, get_parser
    except ImportError:
        pytest.skip("tree-sitter-language-pack not available")

    # Python test code
    python_code = """
def hello(name):
    print(f"Hello, {name}")

class Person:
    def __init__(self, name):
        self.name = name
"""

    # Get Python language and parser
    language = get_language("python")
    parser = get_parser("python")

    # Parse the code
    source_bytes = python_code.encode("utf-8")
    tree = parser.parse(source_bytes)

    # Create a query to find function definitions
    query_string = "(function_definition name: (identifier) @function.name)"
    query = language.query(query_string)

    # Execute query using the helper
    captures = execute_query_captures(query, tree.root_node, source_bytes)

    # Verify we got results
    assert captures is not None, "Should get captures"
    assert len(captures) > 0, "Should have at least one capture"

    # Extract function names
    function_names = []
    if isinstance(captures, dict):
        # Dictionary format
        for capture_name, nodes in captures.items():
            if "function.name" in capture_name or "name" in capture_name:
                for node in nodes:
                    text = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
                    function_names.append(text)
    else:
        # List format
        for match in captures:
            if isinstance(match, tuple) and len(match) == 2:
                node, capture_name = match
                if "function.name" in capture_name or "name" in capture_name:
                    text = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
                    function_names.append(text)

    # Verify we found the functions
    assert "hello" in function_names, "Should find 'hello' function"
    assert "__init__" in function_names, "Should find '__init__' method"


def test_execute_query_captures_with_typescript() -> None:
    """Test execute_query_captures() with TypeScript code (issue #25)."""
    try:
        from tree_sitter_language_pack import get_language, get_parser
    except ImportError:
        pytest.skip("tree-sitter-language-pack not available")

    # TypeScript test code with imports
    typescript_code = """
import { Component } from '@angular/core';
import * as utils from './utils';

export class MyComponent {
    constructor() {}
}
"""

    # Get TypeScript language and parser
    try:
        language = get_language("typescript")
        parser = get_parser("typescript")
    except Exception as e:
        pytest.skip(f"TypeScript language not available: {e}")

    # Parse the code
    source_bytes = typescript_code.encode("utf-8")
    tree = parser.parse(source_bytes)

    # Create a query to find imports (this was failing with the old template)
    query_string = "(import_statement) @import"
    query = language.query(query_string)

    # Execute query using the helper - this should not raise an error
    try:
        captures = execute_query_captures(query, tree.root_node, source_bytes)
        assert captures is not None, "Should get captures"
        # We should find at least the import statements
        if isinstance(captures, dict):
            assert len(captures) > 0, "Should have captures"
        else:
            assert len(list(captures)) > 0, "Should have captures"
    except Exception as e:
        pytest.fail(f"execute_query_captures() failed with TypeScript: {e}")


def test_execute_query_captures_with_go() -> None:
    """Test execute_query_captures() with Go code (issue #25 - user reported)."""
    try:
        from tree_sitter_language_pack import get_language, get_parser
    except ImportError:
        pytest.skip("tree-sitter-language-pack not available")

    # Go test code
    go_code = """
package main

import "fmt"

func hello(name string) {
    fmt.Printf("Hello, %s\\n", name)
}

type Person struct {
    Name string
}
"""

    # Get Go language and parser
    try:
        language = get_language("go")
        parser = get_parser("go")
    except Exception as e:
        pytest.skip(f"Go language not available: {e}")

    # Parse the code
    source_bytes = go_code.encode("utf-8")
    tree = parser.parse(source_bytes)

    # Create a query to find function declarations
    query_string = "(function_declaration name: (identifier) @function.name)"
    query = language.query(query_string)

    # Execute query using the helper
    try:
        captures = execute_query_captures(query, tree.root_node, source_bytes)
        assert captures is not None, "Should get captures"

        # Extract function names
        function_names = []
        if isinstance(captures, dict):
            for capture_name, nodes in captures.items():
                if "function.name" in capture_name or "name" in capture_name:
                    for node in nodes:
                        text = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
                        function_names.append(text)
        else:
            for match in captures:
                if isinstance(match, tuple) and len(match) == 2:
                    node, capture_name = match
                    if "function.name" in capture_name or "name" in capture_name:
                        text = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
                        function_names.append(text)

        assert "hello" in function_names, "Should find 'hello' function"
    except Exception as e:
        pytest.fail(f"execute_query_captures() failed with Go: {e}")


@pytest.fixture
def test_project_python(request) -> Generator[Dict[str, Any], None, None]:
    """Create a test project with Python files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        test_file = project_path / "test.py"
        with open(test_file, "w") as f:
            f.write("""
def process_data(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result

class DataProcessor:
    def __init__(self, data):
        self.data = data

    def process(self):
        return process_data(self.data)
""")

        test_name = request.node.name
        unique_id = abs(hash(test_name)) % 10000
        project_name = f"query_cursor_test_{unique_id}"

        try:
            register_project_tool(path=str(project_path), name=project_name)
        except Exception:
            import time
            project_name = f"query_cursor_test_{unique_id}_{int(time.time())}"
            register_project_tool(path=str(project_path), name=project_name)

        yield {"name": project_name, "path": str(project_path), "file": "test.py"}


def test_get_symbols_tool_with_query_cursor(test_project_python) -> None:
    """Test that get_symbols tool works with QueryCursor API."""
    from tests.test_helpers import get_symbols

    # Use get_symbols which internally uses execute_query_captures()
    result = get_symbols(
        project=test_project_python["name"],
        file_path=test_project_python["file"],
    )

    assert isinstance(result, dict), "Should return a dict"
    assert "functions" in result or "classes" in result, "Should extract functions or classes"

    # Check that we found the expected symbols
    if "functions" in result:
        function_names = [s["name"] for s in result["functions"]]
        assert "process_data" in function_names, "Should find process_data function"

    if "classes" in result:
        class_names = [s["name"] for s in result["classes"]]
        assert "DataProcessor" in class_names, "Should find DataProcessor class"


def test_run_query_tool_with_query_cursor(test_project_python) -> None:
    """Test that run_query tool works with QueryCursor API."""
    # Use run_query which internally uses execute_query_captures()
    query = "(function_definition name: (identifier) @name)"

    result = run_query(
        project=test_project_python["name"],
        query=query,
        file_path=test_project_python["file"],
        language="python",
    )

    assert isinstance(result, list), "Should return a list"
    assert len(result) > 0, "Should find functions"

    # Check that we got the expected structure
    function_names = []
    for capture in result:
        if capture.get("capture") and "name" in capture.get("capture", ""):
            function_names.append(capture.get("text"))

    assert "process_data" in function_names, "Should find process_data function"


def test_query_result_format_compatibility() -> None:
    """Test that execute_query_captures() handles different result formats."""
    try:
        from tree_sitter_language_pack import get_language, get_parser
    except ImportError:
        pytest.skip("tree-sitter-language-pack not available")

    python_code = "def test(): pass"

    language = get_language("python")
    parser = get_parser("python")
    source_bytes = python_code.encode("utf-8")
    tree = parser.parse(source_bytes)

    query_string = "(function_definition name: (identifier) @name)"
    query = language.query(query_string)

    # Execute query
    captures = execute_query_captures(query, tree.root_node, source_bytes)

    # Verify we can handle the result regardless of format
    assert captures is not None, "Should get captures"

    # Test that we can extract data from whatever format we get
    found_name = False
    if isinstance(captures, dict):
        # Dictionary format
        for capture_name, nodes in captures.items():
            if nodes:
                found_name = True
                break
    elif isinstance(captures, list):
        # List format
        if len(captures) > 0:
            found_name = True

    assert found_name, "Should be able to extract data from captures"
