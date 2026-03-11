"""Position tests for get_enclosing_scope on Java."""

from collections.abc import Generator
from pathlib import Path

import pytest

from tests.enclosing_scope.scope_assertions import (
    assert_scope_empty,
    assert_scope_is_class,
    assert_scope_is_function,
    assert_scope_is_module,
)
from tests.test_helpers import get_enclosing_scope_tool, register_project_tool


class TestGetEnclosingScopeJava:
    """Tests for get_enclosing_scope on Java (method, constructor, class_declaration, program)."""

    MULTI_SCOPE_SOURCE_JAVA = """import java.util.List;

public class Test {
    int x = 42;

    public int foo() {
        return 1;
    }

    public int bar() {
        return 2;
    }
}
"""

    @pytest.fixture
    def project_with_multi_scope_java(self, tmp_path: Path) -> Generator[str, None, None]:
        test_file = tmp_path / "Test.java"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_JAVA, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_java_test", description="Java enclosing scope")
        yield "enclosing_scope_java_test"

    def test_java_module_scope(self, project_with_multi_scope_java: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 0, 0, "import")
        assert_scope_is_module(scope, "import java.util.List", "public class Test")

    def test_java_class_scope(self, project_with_multi_scope_java: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 2, 13, "Test")
        assert_scope_is_class(scope, "public class Test", "int x", "foo()", "bar()")

    def test_java_field_in_class_scope(self, project_with_multi_scope_java: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 4, 8, "x")
        assert_scope_is_class(scope, "public class Test", "int x", row=4)

    def test_java_method_scope(self, project_with_multi_scope_java: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 6, 16, "foo")
        assert_scope_is_function(scope, "public int foo()", "return 1", row=6)

    def test_java_second_method_scope(self, project_with_multi_scope_java: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 10, 16, "bar")
        assert_scope_is_function(scope, "public int bar()", "return 2", row=10)

    def test_java_outside_bounds(self, project_with_multi_scope_java: str) -> None:
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 99, 0, None))

    def test_java_constructor_returns_function_scope(self, project_with_constructor_java: str) -> None:
        """Position inside a Java constructor body → function scope (constructor is constructor_declaration)."""
        # Position inside constructor body: line 4 is "        this.n = n;" (0-based)
        scope = get_enclosing_scope_tool(project_with_constructor_java, "Box.java", 4, 14, "this")
        assert_scope_is_function(scope, "public Box(int n)", "this.n = n", row=4)

    @pytest.fixture
    def project_with_constructor_java(self, tmp_path: Path) -> Generator[str, None, None]:
        source = """public class Box {
    private int n;

    public Box(int n) {
        this.n = n;
    }
}
"""
        (tmp_path / "Box.java").write_text(source, encoding="utf-8")
        register_project_tool(
            str(tmp_path),
            name="enclosing_scope_java_ctor_test",
            description="Java constructor scope",
        )
        yield "enclosing_scope_java_ctor_test"
