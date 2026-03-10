"""Position tests for get_enclosing_scope on JavaScript."""

import pytest

from tests.enclosing_scope.scope_assertions import (
    assert_scope_empty,
    assert_scope_is_class,
    assert_scope_is_function,
    assert_scope_is_function_or_method,
    assert_scope_is_module,
)
from tests.test_helpers import get_enclosing_scope_tool, register_project_tool


class TestGetEnclosingScopeJavaScript:
    """Tests for get_enclosing_scope tool on JavaScript. Positions are first character of a token (0-based)."""

    # Fixed source: predictable 0-based line numbers.
    # Line 0: const X = 42;  (module level)
    # Line 1: (blank)
    # Line 2: function foo() {
    # Line 3:   return 1;
    # Line 4: }
    # Line 5: (blank)
    # Line 6: class Bar {
    # Line 7:   z = 0;
    # Line 8:   meth() {
    # Line 9:     return;
    # Line 10:   }
    # Line 11: }
    # Line 12: (blank)
    # Line 13: function bar() {
    # Line 14:   return 2;
    # Line 15: }
    MULTI_SCOPE_SOURCE_JS = """const X = 42;

function foo() {
  return 1;
}

class Bar {
  z = 0;
  meth() {
    return;
  }
}

function bar() {
  return 2;
}
"""

    @pytest.fixture
    def project_with_multi_scope_js(self, tmp_path):
        """Register a temp project with test.js containing program, function, class, and method."""
        test_file = tmp_path / "test.js"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_JS, encoding="utf-8")
        register_project_tool(
            str(tmp_path),
            name="enclosing_scope_js_test",
            description="Test project for get_enclosing_scope API (JavaScript)",
        )
        yield "enclosing_scope_js_test"

    def test_js_position_at_const_returns_module_scope(self, project_with_multi_scope_js):
        """Position at first char of 'const' (0, 0) → module scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 0, 0, "const")
        assert_scope_is_module(scope, "const X = 42", "function foo", "class Bar", "function bar")

    def test_js_position_at_module_level_variable_returns_module_scope(self, project_with_multi_scope_js):
        """Position at first char of 'X' (0, 6) in const X = 42 → module scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 0, 6, "X")
        assert_scope_is_module(scope, "const X = 42", "function foo", "class Bar", "function bar")

    def test_js_position_at_foo_returns_function_scope(self, project_with_multi_scope_js):
        """Position at first char of 'foo' (2, 9) → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 2, 9, "foo")
        assert_scope_is_function(scope, "function foo()", "return 1", row=2)

    def test_js_position_at_return_inside_foo_returns_function_scope(self, project_with_multi_scope_js):
        """Position at first char of 'return' (3, 2) inside foo → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 3, 2, "return")
        assert_scope_is_function(scope, "function foo()", "return 1", row=3)

    def test_js_position_at_class_returns_class_scope(self, project_with_multi_scope_js):
        """Position at first char of 'class' (6, 0) → class scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 6, 0, "class")
        assert_scope_is_class(scope, "class Bar", "z = 0", "meth()")

    def test_js_position_at_Bar_returns_class_scope(self, project_with_multi_scope_js):
        """Position at first char of 'Bar' (6, 6) → class scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 6, 6, "Bar")
        assert_scope_is_class(scope, "class Bar")

    def test_js_position_in_class_body_not_in_method_returns_class_scope(self, project_with_multi_scope_js):
        """Position at first char of 'z' (7, 2) in class body → class scope, not method."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 7, 2, "z")
        assert_scope_is_class(scope, "class Bar", "z = 0", row=7)

    def test_js_position_at_meth_returns_method_scope(self, project_with_multi_scope_js):
        """Position at first char of 'meth' (8, 2) → method scope (kind function)."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 8, 2, "meth")
        assert_scope_is_function_or_method(scope, "meth()", "return", row=8)

    def test_js_position_at_return_inside_meth_returns_method_scope(self, project_with_multi_scope_js):
        """Position at first char of 'return' (9, 4) inside meth → method scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 9, 4, "return")
        assert_scope_is_function_or_method(scope, "meth()", "return", row=9)

    def test_js_position_at_bar_returns_function_scope(self, project_with_multi_scope_js):
        """Position at first char of 'bar' (13, 9) → function scope (top-level, outside class)."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 13, 9, "bar")
        assert_scope_is_function(scope, "function bar()", "return 2", row=13)

    def test_js_position_at_return_inside_bar_returns_function_scope(self, project_with_multi_scope_js):
        """Position at first char of 'return' (14, 2) inside bar → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 14, 2, "return")
        assert_scope_is_function(scope, "function bar()", "return 2", row=14)

    def test_js_position_outside_file_boundaries_returns_empty_scope(self, project_with_multi_scope_js):
        """Position beyond last line (outside file) → empty dict, no scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 99, 0, None)
        assert_scope_empty(scope)

    def test_js_constructor_returns_function_scope(self, project_with_constructor_js):
        """Position inside a JS class constructor() body → function scope (constructor is method_definition)."""
        # Position inside constructor body block (line with "this.n = n;")
        scope = get_enclosing_scope_tool(project_with_constructor_js, "box.js", 2, 8, "this")
        assert_scope_is_function_or_method(scope, "constructor", "this.n = n", row=2)

    @pytest.fixture
    def project_with_constructor_js(self, tmp_path):
        source = """class Box {
    constructor(n) {
        this.n = n;
    }
}
"""
        (tmp_path / "box.js").write_text(source, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_js_ctor_test", description="JS constructor scope")
        yield "enclosing_scope_js_ctor_test"
