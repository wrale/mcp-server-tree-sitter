"""Position tests for get_enclosing_scope on Python."""

import pytest

from tests.enclosing_scope.scope_assertions import (
    assert_scope_empty,
    assert_scope_is_class,
    assert_scope_is_function,
    assert_scope_is_function_or_method,
    assert_scope_is_module,
)
from tests.test_helpers import get_enclosing_scope_tool, register_project_tool


class TestGetEnclosingScopePython:
    """Tests for get_enclosing_scope tool on Python. Positions are first character of a token (0-based row, column)."""

    # Fixed source: predictable 0-based line numbers.
    # Line 0: import os
    # Line 1: (blank)
    # Line 2: X = 42  (module level, outside any class/function)
    # Line 3: (blank)
    # Line 4: def foo():
    # Line 5:     return 1
    # Line 6: (blank)
    # Line 7: class Bar:
    # Line 8:     z = 0
    # Line 9:     def meth(self):
    # Line 10:        pass
    # Line 11: (blank)
    # Line 12: def bar():  (top-level function outside class)
    # Line 13:     return 2
    MULTI_SCOPE_SOURCE = """import os

X = 42

def foo():
    return 1

class Bar:
    z = 0
    def meth(self):
        pass

def bar():
    return 2
"""

    @pytest.fixture
    def project_with_multi_scope(self, tmp_path):
        """Register a temp project with test.py containing module, function, class, and method."""
        test_file = tmp_path / "test.py"
        test_file.write_text(self.MULTI_SCOPE_SOURCE, encoding="utf-8")
        register_project_tool(
            str(tmp_path),
            name="enclosing_scope_api_test",
            description="Test project for get_enclosing_scope API",
        )
        yield "enclosing_scope_api_test"

    def test_position_at_import_returns_module_scope(self, project_with_multi_scope):
        """Position at first char of 'import' (0, 0) → module scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 0, 0, "import")
        assert_scope_is_module(scope, "import os", "def foo()", "class Bar")

    def test_position_at_module_level_assignment_returns_module_scope(self, project_with_multi_scope):
        """Position at first char of 'X' (2, 0) in X = 42 → module scope (code outside class/function)."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 2, 0, "X")
        assert_scope_is_module(scope, "X = 42", "import os", "def foo()", "def bar()")

    def test_position_at_function_name_returns_function_scope(self, project_with_multi_scope):
        """Position at first char of 'foo' (4, 4) → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 4, 4, "foo")
        assert_scope_is_function(scope, "def foo()", "return 1", row=4)

    def test_position_at_return_inside_foo_returns_function_scope(self, project_with_multi_scope):
        """Position at first char of 'return' (5, 4) inside foo → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 5, 4, "return")
        assert_scope_is_function(scope, "def foo()", "return 1", row=5)

    def test_position_at_class_keyword_returns_class_scope(self, project_with_multi_scope):
        """Position at first char of 'class' (7, 0) → class scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 7, 0, "class")
        assert_scope_is_class(scope, "class Bar:", "z = 0", "def meth(self):")

    def test_position_at_class_name_returns_class_scope(self, project_with_multi_scope):
        """Position at first char of 'Bar' (7, 6) → class scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 7, 6, "Bar")
        assert_scope_is_class(scope, "class Bar:")

    def test_position_in_class_body_not_in_method_returns_class_scope(self, project_with_multi_scope):
        """Position at first char of 'z' (8, 4) in class body → class scope, not method."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 8, 4, "z")
        assert_scope_is_class(scope, "class Bar:", "z = 0", row=8)

    def test_position_at_method_name_returns_method_scope(self, project_with_multi_scope):
        """Position at first char of 'meth' (9, 8) → method scope (kind function)."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 9, 8, "meth")
        assert_scope_is_function_or_method(scope, "meth", "pass")

    def test_position_at_pass_inside_method_returns_method_scope(self, project_with_multi_scope):
        """Position at first char of 'pass' (10, 8) inside meth → method scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 10, 8, "pass")
        assert_scope_is_function_or_method(scope, "def meth(self):", "pass", row=10)

    def test_position_at_def_inside_class_returns_function_scope(self, project_with_multi_scope):
        """Position at first char of inner 'def' (9, 4) → method/function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 9, 4, "def")
        assert_scope_is_function_or_method(scope, "def meth(self):", "pass")

    def test_position_at_second_top_level_function_returns_function_scope(self, project_with_multi_scope):
        """Position at first char of 'bar' (12, 4) → function scope (top-level bar, outside class)."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 12, 4, "bar")
        assert_scope_is_function(scope, "def bar()", "return 2", row=12)

    def test_position_at_return_inside_bar_returns_function_scope(self, project_with_multi_scope):
        """Position at first char of 'return' (13, 4) inside bar → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 13, 4, "return")
        assert_scope_is_function(scope, "def bar()", "return 2", row=13)

    def test_position_outside_file_boundaries_returns_empty_scope(self, project_with_multi_scope):
        """Position beyond last line (outside file) → empty dict, no scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 99, 0, None)
        assert_scope_empty(scope)
