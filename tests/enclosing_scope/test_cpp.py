"""Position tests for get_enclosing_scope on C++."""

from collections.abc import Generator
from pathlib import Path

import pytest

from tests.enclosing_scope.scope_assertions import (
    assert_scope_empty,
    assert_scope_is_class,
    assert_scope_is_function,
    assert_scope_is_function_or_method,
    assert_scope_is_module,
)
from tests.test_helpers import get_enclosing_scope_tool, register_project_tool


class TestGetEnclosingScopeCpp:
    """Tests for get_enclosing_scope on C++ (function, method, class_specifier, translation_unit)."""

    MULTI_SCOPE_SOURCE_CPP = """int x = 42;

int foo() {
    return 1;
}

class Bar {
    int z;
public:
    int meth() {
        return 0;
    }
};

int bar() {
    return 2;
}
"""

    @pytest.fixture
    def project_with_multi_scope_cpp(self, tmp_path: Path) -> Generator[str, None, None]:
        test_file = tmp_path / "main.cpp"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_CPP, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_cpp_test", description="C++ enclosing scope")
        yield "enclosing_scope_cpp_test"

    def test_cpp_module_scope(self, project_with_multi_scope_cpp: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 0, 0, "int")
        assert_scope_is_module(scope, "int x = 42", "int foo()", "class Bar")

    def test_cpp_function_scope(self, project_with_multi_scope_cpp: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 2, 4, "foo")
        assert_scope_is_function(scope, "int foo()", "return 1", row=2)

    def test_cpp_class_scope(self, project_with_multi_scope_cpp: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 6, 6, "Bar")
        assert_scope_is_class(scope, "class Bar", "int z", "meth()")

    def test_cpp_method_scope(self, project_with_multi_scope_cpp: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 9, 8, "meth")
        assert_scope_is_function_or_method(scope, "int meth()", "return 0", row=9)

    def test_cpp_second_function_scope(self, project_with_multi_scope_cpp: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 15, 4, "bar")
        assert_scope_is_function(scope, "int bar()", "return 2", row=15)

    def test_cpp_outside_bounds(self, project_with_multi_scope_cpp: str) -> None:
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 99, 0, None))

    def test_cpp_constructor_returns_function_scope(self, project_with_constructor_destructor_cpp: str) -> None:
        """Position inside a C++ constructor body → function scope (grammar aliases it to function_definition)."""
        scope = get_enclosing_scope_tool(project_with_constructor_destructor_cpp, "box.cpp", 4, 8, "n")
        assert_scope_is_function(scope, "Box(", "n = 0", row=4)

    def test_cpp_destructor_returns_function_scope(self, project_with_constructor_destructor_cpp: str) -> None:
        """Position inside a C++ destructor body → function scope (grammar aliases it to function_definition)."""
        scope = get_enclosing_scope_tool(project_with_constructor_destructor_cpp, "box.cpp", 8, 4, "delete")
        assert_scope_is_function(scope, "~Box()", "delete", row=8)

    @pytest.fixture
    def project_with_constructor_destructor_cpp(self, tmp_path: Path) -> Generator[str, None, None]:
        source = """class Box {
public:
    int n;
    Box() {
        n = 0;
    }
    ~Box() {
        delete[] p;
    }
};
"""
        (tmp_path / "box.cpp").write_text(source, encoding="utf-8")
        register_project_tool(
            str(tmp_path),
            name="enclosing_scope_cpp_ctor_test",
            description="C++ constructor/destructor scope",
        )
        yield "enclosing_scope_cpp_ctor_test"
