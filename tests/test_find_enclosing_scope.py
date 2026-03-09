"""Tests for find_enclosing_scope helper (Task 3)."""

import pytest

from mcp_server_tree_sitter.language.registry import LanguageRegistry
from mcp_server_tree_sitter.models.ast import find_enclosing_scope

# Fixed source so line numbers are predictable (0-based).
# Line 0: import
# Line 3: def foo
# Line 4:   return (inside foo)
# Line 6: class Bar
# Line 7:   z = 0 (inside class, not in a method)
# Line 8:   def meth
PYTHON_SOURCE = b"""import os

def foo():
    return 1

class Bar:
    z = 0
    def meth(self):
        pass
"""


@pytest.fixture
def python_tree_and_source():
    """Parse PYTHON_SOURCE with Python and return (tree, source_bytes)."""
    registry = LanguageRegistry()
    parser = registry.get_parser("python")
    tree = parser.parse(PYTHON_SOURCE)
    return tree, PYTHON_SOURCE


def test_position_inside_function_returns_function_scope(python_tree_and_source):
    """T3.1: Position inside function body → dict has five keys, kind function/method, name matches, text contains function, start_line <= row <= end_line."""
    tree, source_bytes = python_tree_and_source
    root = tree.root_node
    # Row 3 is "    return 1" (inside foo body)
    row, col = 3, 4
    result = find_enclosing_scope(root, source_bytes, row, col, "python")
    assert set(result.keys()) == {"kind", "name", "text", "start_line", "end_line"}
    assert result["kind"] in ("function", "method")
    assert result["name"] == "foo"
    assert "def foo()" in result["text"] and "return 1" in result["text"]
    assert result["start_line"] <= row <= result["end_line"]


def test_position_on_import_returns_module_scope(python_tree_and_source):
    """T3.2: Position on import line → kind is module/namespace, text includes the import."""
    tree, source_bytes = python_tree_and_source
    root = tree.root_node
    result = find_enclosing_scope(root, source_bytes, 0, 5, "python")
    assert result["kind"] in ("module", "namespace")
    assert "import" in result["text"]


def test_position_in_class_body_not_in_method_returns_class_scope(python_tree_and_source):
    """T3.3: Position inside class body but not inside a method → kind is class, text contains class definition."""
    tree, source_bytes = python_tree_and_source
    root = tree.root_node
    # Row 6 is "    z = 0" (inside Bar, not inside meth)
    result = find_enclosing_scope(root, source_bytes, 6, 4, "python")
    assert result["kind"] == "class"
    assert "class Bar" in result["text"]
