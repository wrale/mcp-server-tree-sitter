"""Position tests for get_enclosing_scope on C#."""

import pytest

from tests.enclosing_scope.scope_assertions import (
    assert_scope_empty,
    assert_scope_is_class,
    assert_scope_is_function,
    assert_scope_is_module,
)
from tests.test_helpers import get_enclosing_scope_tool, register_project_tool


class TestGetEnclosingScopeCSharp:
    """Tests for get_enclosing_scope on C# (method, constructor, class_declaration, compilation_unit)."""

    MULTI_SCOPE_SOURCE_CSHARP = """using System;

public class Test {
    int x = 42;

    public int Foo() {
        return 1;
    }

    public int Bar() {
        return 2;
    }
}
"""

    @pytest.fixture
    def project_with_multi_scope_csharp(self, tmp_path):
        test_file = tmp_path / "Test.cs"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_CSHARP, encoding="utf-8")
        register_project_tool(
            str(tmp_path),
            name="enclosing_scope_csharp_test",
            description="C# enclosing scope",
        )
        yield "enclosing_scope_csharp_test"

    def test_csharp_module_scope(self, project_with_multi_scope_csharp):
        scope = get_enclosing_scope_tool(
            project_with_multi_scope_csharp, "Test.cs", 0, 0, "using"
        )
        assert_scope_is_module(scope, "using System", "public class Test")

    def test_csharp_class_scope(self, project_with_multi_scope_csharp):
        scope = get_enclosing_scope_tool(
            project_with_multi_scope_csharp, "Test.cs", 2, 13, "Test"
        )
        assert_scope_is_class(scope, "public class Test", "int x", "Foo()", "Bar()")

    def test_csharp_field_in_class_scope(self, project_with_multi_scope_csharp):
        scope = get_enclosing_scope_tool(
            project_with_multi_scope_csharp, "Test.cs", 3, 8, "x"
        )
        assert_scope_is_class(scope, "public class Test", "int x", row=3)

    def test_csharp_method_scope(self, project_with_multi_scope_csharp):
        scope = get_enclosing_scope_tool(
            project_with_multi_scope_csharp, "Test.cs", 5, 16, "Foo"
        )
        assert_scope_is_function(scope, "public int Foo()", "return 1", row=5)

    def test_csharp_second_method_scope(self, project_with_multi_scope_csharp):
        scope = get_enclosing_scope_tool(
            project_with_multi_scope_csharp, "Test.cs", 9, 16, "Bar"
        )
        assert_scope_is_function(scope, "public int Bar()", "return 2", row=9)

    def test_csharp_outside_bounds(self, project_with_multi_scope_csharp):
        assert_scope_empty(
            get_enclosing_scope_tool(
                project_with_multi_scope_csharp, "Test.cs", 99, 0, None
            )
        )

    def test_csharp_constructor_returns_function_scope(self, project_with_constructor_csharp):
        """Position inside a C# constructor body → function scope (constructor_declaration)."""
        scope = get_enclosing_scope_tool(
            project_with_constructor_csharp, "Box.cs", 4, 8, "this"
        )
        assert_scope_is_function(scope, "public Box(int n)", "this.n = n", row=4)

    @pytest.fixture
    def project_with_constructor_csharp(self, tmp_path):
        source = """public class Box {
    private int n;

    public Box(int n) {
        this.n = n;
    }
}
"""
        (tmp_path / "Box.cs").write_text(source, encoding="utf-8")
        register_project_tool(
            str(tmp_path),
            name="enclosing_scope_csharp_ctor_test",
            description="C# constructor scope",
        )
        yield "enclosing_scope_csharp_ctor_test"
