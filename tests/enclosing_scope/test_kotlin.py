"""Position tests for get_enclosing_scope on Kotlin."""

import pytest

from tests.enclosing_scope.scope_assertions import (
    assert_scope_empty,
    assert_scope_is_class,
    assert_scope_is_function,
    assert_scope_is_function_or_method,
    assert_scope_is_module,
)
from tests.test_helpers import get_enclosing_scope_tool, register_project_tool


class TestGetEnclosingScopeKotlin:
    """Tests for get_enclosing_scope on Kotlin (function_declaration, class_declaration, kotlin_file)."""

    MULTI_SCOPE_SOURCE_KT = """val x = 42

fun foo(): Int {
    return 1
}

class Bar {
    var z = 0
    fun meth() {
        return
    }
}

fun bar(): Int {
    return 2
}
"""

    @pytest.fixture
    def project_with_multi_scope_kotlin(self, tmp_path):
        test_file = tmp_path / "main.kt"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_KT, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_kotlin_test", description="Kotlin enclosing scope")
        yield "enclosing_scope_kotlin_test"

    def test_kotlin_module_scope(self, project_with_multi_scope_kotlin):
        scope = get_enclosing_scope_tool(project_with_multi_scope_kotlin, "main.kt", 0, 0, "val")
        assert_scope_is_module(scope, "val x = 42", "fun foo", "class Bar")

    def test_kotlin_function_scope(self, project_with_multi_scope_kotlin):
        scope = get_enclosing_scope_tool(project_with_multi_scope_kotlin, "main.kt", 2, 4, "foo")
        assert_scope_is_function(scope, "fun foo()", "return 1", row=2)

    def test_kotlin_class_scope(self, project_with_multi_scope_kotlin):
        scope = get_enclosing_scope_tool(project_with_multi_scope_kotlin, "main.kt", 6, 6, "Bar")
        assert_scope_is_class(scope, "class Bar", "var z", "fun meth()")

    def test_kotlin_method_scope(self, project_with_multi_scope_kotlin):
        scope = get_enclosing_scope_tool(project_with_multi_scope_kotlin, "main.kt", 8, 8, "meth")
        assert_scope_is_function_or_method(scope, "fun meth()", "return", row=8)

    def test_kotlin_second_function_scope(self, project_with_multi_scope_kotlin):
        # Position inside bar() body (return 2)
        scope = get_enclosing_scope_tool(project_with_multi_scope_kotlin, "main.kt", 13, 4, "return")
        assert_scope_is_function(scope, "fun bar()", "return 2", row=13)

    def test_kotlin_outside_bounds(self, project_with_multi_scope_kotlin):
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_kotlin, "main.kt", 99, 0, None))

    def test_kotlin_getter_returns_function_scope(self, project_with_accessors_kotlin):
        """Position inside a Kotlin property get() → function scope (getter)."""
        scope = get_enclosing_scope_tool(project_with_accessors_kotlin, "props.kt", 2, 10, "0")
        assert_scope_is_function(scope, "get()", "= 0", row=2)

    def test_kotlin_setter_returns_function_scope(self, project_with_accessors_kotlin):
        """Position inside a Kotlin property set(value) body → function scope (setter)."""
        scope = get_enclosing_scope_tool(project_with_accessors_kotlin, "props.kt", 3, 18, "value")
        assert_scope_is_function(scope, "set(value)", "field = value", row=3)

    @pytest.fixture
    def project_with_accessors_kotlin(self, tmp_path):
        source = """class C {
    var x: Int
        get() = 0
        set(value) { field = value }
}
"""
        (tmp_path / "props.kt").write_text(source, encoding="utf-8")
        register_project_tool(
            str(tmp_path),
            name="enclosing_scope_kotlin_accessors_test",
            description="Kotlin getter/setter scope",
        )
        yield "enclosing_scope_kotlin_accessors_test"
