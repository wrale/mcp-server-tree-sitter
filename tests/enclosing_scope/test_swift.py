"""Position tests for get_enclosing_scope on Swift."""

import pytest

from tests.enclosing_scope.scope_assertions import (
    assert_scope_empty,
    assert_scope_is_class,
    assert_scope_is_function,
    assert_scope_is_function_or_method,
    assert_scope_is_module,
)
from tests.test_helpers import get_enclosing_scope_tool, register_project_tool


class TestGetEnclosingScopeSwift:
    """Tests for get_enclosing_scope on Swift
    (function_declaration, class_declaration, struct_declaration, source_file)."""

    MULTI_SCOPE_SOURCE_SWIFT = """let x = 42

func foo() -> Int {
    return 1
}

class Bar {
    var z = 0
    func meth() {
        return
    }
}

func bar() -> Int {
    return 2
}
"""

    @pytest.fixture
    def project_with_multi_scope_swift(self, tmp_path):
        test_file = tmp_path / "main.swift"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_SWIFT, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_swift_test", description="Swift enclosing scope")
        yield "enclosing_scope_swift_test"

    def test_swift_module_scope(self, project_with_multi_scope_swift):
        scope = get_enclosing_scope_tool(project_with_multi_scope_swift, "main.swift", 0, 0, "let")
        assert_scope_is_module(scope, "let x = 42", "func foo", "class Bar")

    def test_swift_function_scope(self, project_with_multi_scope_swift):
        scope = get_enclosing_scope_tool(project_with_multi_scope_swift, "main.swift", 2, 5, "foo")
        assert_scope_is_function(scope, "func foo()", "return 1", row=2)

    def test_swift_class_scope(self, project_with_multi_scope_swift):
        scope = get_enclosing_scope_tool(project_with_multi_scope_swift, "main.swift", 6, 6, "Bar")
        assert_scope_is_class(scope, "class Bar", "var z", "func meth()")

    def test_swift_method_scope(self, project_with_multi_scope_swift):
        scope = get_enclosing_scope_tool(project_with_multi_scope_swift, "main.swift", 8, 9, "meth")
        assert_scope_is_function_or_method(scope, "func meth()", "return", row=8)

    def test_swift_second_function_scope(self, project_with_multi_scope_swift):
        # Position inside bar() body (return 2)
        scope = get_enclosing_scope_tool(project_with_multi_scope_swift, "main.swift", 13, 4, "return")
        assert_scope_is_function(scope, "func bar()", "return 2", row=13)

    def test_swift_outside_bounds(self, project_with_multi_scope_swift):
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_swift, "main.swift", 99, 0, None))

    def test_swift_getter_returns_function_scope(self, project_with_accessors_swift):
        """Position inside a Swift computed property get block → function scope (computed_getter)."""
        scope = get_enclosing_scope_tool(project_with_accessors_swift, "props.swift", 2, 14, "return")
        assert_scope_is_function(scope, "get", "return 0", row=2)

    def test_swift_setter_returns_function_scope(self, project_with_accessors_swift):
        """Position inside a Swift computed property set block → function scope (computed_setter)."""
        scope = get_enclosing_scope_tool(project_with_accessors_swift, "props.swift", 3, 10, "x")
        assert_scope_is_function(scope, "set", "x = newValue", row=3)

    @pytest.fixture
    def project_with_accessors_swift(self, tmp_path):
        source = """struct S {
    var x: Int {
        get { return 0 }
        set { x = newValue }
    }
}
"""
        (tmp_path / "props.swift").write_text(source, encoding="utf-8")
        register_project_tool(
            str(tmp_path),
            name="enclosing_scope_swift_accessors_test",
            description="Swift getter/setter scope",
        )
        yield "enclosing_scope_swift_accessors_test"
