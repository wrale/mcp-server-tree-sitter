"""Integration tests for get_enclosing_scope_for_path."""

from pathlib import Path
from typing import Any, Tuple

import pytest

from mcp_server_tree_sitter.api import (
    get_language_registry,
    get_project_registry,
    get_tree_cache,
)
from mcp_server_tree_sitter.language.registry import LanguageRegistry
from mcp_server_tree_sitter.models.ast import find_enclosing_scope
from mcp_server_tree_sitter.tools.ast_operations import get_enclosing_scope_for_path
from tests.enclosing_scope.scope_assertions import (
    assert_scope_is_class,
    assert_scope_is_function,
    assert_scope_is_module,
)
from tests.test_helpers import register_project_tool


class TestFindEnclosingScope:
    """Tests for find_enclosing_scope helper."""

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
    def python_tree_and_source(self) -> Tuple[Any, bytes]:
        """Parse PYTHON_SOURCE with Python and return (tree, source_bytes)."""
        registry = LanguageRegistry()
        parser = registry.get_parser("python")
        tree = parser.parse(self.PYTHON_SOURCE)
        return tree, self.PYTHON_SOURCE

    def test_position_inside_function_returns_function_scope(self, python_tree_and_source: Tuple[Any, bytes]) -> None:
        """Position inside function body → kind function, text contains function, start_line <= row <= end_line."""
        tree, source_bytes = python_tree_and_source
        root = tree.root_node
        row, col, label = 3, 4, "foo"
        result = find_enclosing_scope(root, source_bytes, row, col, label, "python")
        assert_scope_is_function(result, "def foo()", "return 1", row=row)

    def test_position_on_import_returns_module_scope(self, python_tree_and_source: Tuple[Any, bytes]) -> None:
        """Position on import line → kind is module/namespace, text includes the import."""
        tree, source_bytes = python_tree_and_source
        root = tree.root_node
        result = find_enclosing_scope(root, source_bytes, 0, 0, "import", "python")
        assert_scope_is_module(result, "import", "def foo()", "return 1", "class Bar")

    def test_position_in_class_body_not_in_method_returns_class_scope(
        self, python_tree_and_source: Tuple[Any, bytes]
    ) -> None:
        """Position inside class body but not inside a method → kind is class, text contains class definition."""
        tree, source_bytes = python_tree_and_source
        root = tree.root_node
        result = find_enclosing_scope(root, source_bytes, 6, 4, "z", "python")
        assert_scope_is_class(result, "class Bar")


class TestEnclosingScopeForPath:
    # Fixed source: def hello(): on line 0, return on line 1 (0-based).
    # Position (1, 4) is inside the function body.
    PROJECT_SOURCE = """def hello():
        return 1
    """

    @pytest.fixture
    def project_with_python_file(self, tmp_path: Path) -> dict[str, Any]:
        """Register a temporary project with test.py containing one function."""
        root = tmp_path
        test_py = root / "test.py"
        test_py.write_text(self.PROJECT_SOURCE, encoding="utf-8")
        name = "enclosing_scope_integration_test"
        register_project_tool(path=str(root), name=name)
        return {"name": name, "root": root}

    def test_get_enclosing_scope_for_path_returns_scope_dict(self, project_with_python_file: dict[str, Any]) -> None:
        """Register temp project with test.py; call get_enclosing_scope_for_path; assert result has kind,
        text, start_line, end_line and position inside function gives function scope."""
        project_registry = get_project_registry()
        project = project_registry.get_project(project_with_python_file["name"])
        language_registry = get_language_registry()
        tree_cache = get_tree_cache()

        # Position (1, 4) is inside "    return 1" (inside hello body)
        result = get_enclosing_scope_for_path(project, "test.py", 1, 4, "return", language_registry, tree_cache)

        assert_scope_is_function(result, "def hello", "return 1", row=1)
