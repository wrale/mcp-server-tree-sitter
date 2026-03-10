"""Position tests for get_enclosing_scope on TypeScript."""

import pytest

from tests.enclosing_scope.scope_assertions import (
    assert_scope_empty,
    assert_scope_is_class,
    assert_scope_is_function,
    assert_scope_is_function_or_method,
    assert_scope_is_module,
)
from tests.test_helpers import get_enclosing_scope_tool, register_project_tool


class TestGetEnclosingScopeTypeScript:
    """Tests for get_enclosing_scope on TypeScript. Same structure as JavaScript
    (program, function_declaration, method_definition, class_declaration)."""

    MULTI_SCOPE_SOURCE_TS = """const X = 42;

function foo(): number {
  return 1;
}

class Bar {
  z = 0;
  meth(): void {
    return;
  }
}

function bar(): number {
  return 2;
}
"""

    @pytest.fixture
    def project_with_multi_scope_ts(self, tmp_path):
        test_file = tmp_path / "test.ts"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_TS, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_ts_test", description="TypeScript enclosing scope")
        yield "enclosing_scope_ts_test"

    def test_ts_module_scope(self, project_with_multi_scope_ts):
        scope = get_enclosing_scope_tool(project_with_multi_scope_ts, "test.ts", 0, 0, "const")
        assert_scope_is_module(scope, "const X = 42", "function foo", "class Bar")

    def test_ts_function_scope(self, project_with_multi_scope_ts):
        scope = get_enclosing_scope_tool(project_with_multi_scope_ts, "test.ts", 2, 9, "foo")
        assert_scope_is_function(scope, "function foo()", "return 1", row=2)

    def test_ts_class_scope(self, project_with_multi_scope_ts):
        scope = get_enclosing_scope_tool(project_with_multi_scope_ts, "test.ts", 6, 6, "Bar")
        assert_scope_is_class(scope, "class Bar", "z = 0")

    def test_ts_method_scope(self, project_with_multi_scope_ts):
        scope = get_enclosing_scope_tool(project_with_multi_scope_ts, "test.ts", 8, 2, "meth")
        assert_scope_is_function_or_method(scope, "meth()", "return", row=8)

    def test_ts_top_level_function_scope(self, project_with_multi_scope_ts):
        scope = get_enclosing_scope_tool(project_with_multi_scope_ts, "test.ts", 13, 9, "bar")
        assert_scope_is_function(scope, "function bar()", "return 2", row=13)

    def test_ts_outside_bounds(self, project_with_multi_scope_ts):
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_ts, "test.ts", 99, 0, None))

    def test_ts_constructor_returns_function_scope(self, project_with_constructor_ts):
        """Position inside a TS class constructor() body → function scope (constructor is method_definition)."""
        scope = get_enclosing_scope_tool(project_with_constructor_ts, "box.ts", 2, 8, "this")
        assert_scope_is_function_or_method(scope, "constructor", "this.n = n", row=2)

    @pytest.fixture
    def project_with_constructor_ts(self, tmp_path):
        source = """class Box {
    constructor(n: number) {
        this.n = n;
    }
}
"""
        (tmp_path / "box.ts").write_text(source, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_ts_ctor_test", description="TS constructor scope")
        yield "enclosing_scope_ts_ctor_test"
