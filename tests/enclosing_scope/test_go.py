"""Position tests for get_enclosing_scope on Go."""

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


class TestGetEnclosingScopeGo:
    """Tests for get_enclosing_scope on Go (function_declaration, method_declaration, type_declaration, source_file)."""

    MULTI_SCOPE_SOURCE_GO = """package p

const X = 42

func foo() int {
	return 1
}

type Bar struct {
	Z int
}

func (b Bar) meth() int {
	return 0
}

func bar() int {
	return 2
}
"""

    @pytest.fixture
    def project_with_multi_scope_go(self, tmp_path: Path) -> Generator[str, None, None]:
        test_file = tmp_path / "main.go"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_GO, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_go_test", description="Go enclosing scope")
        yield "enclosing_scope_go_test"

    def test_go_module_scope(self, project_with_multi_scope_go: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 0, 0, "package")
        assert_scope_is_module(scope, "package p", "func foo", "type Bar")

    def test_go_function_scope(self, project_with_multi_scope_go: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 4, 5, "foo")
        assert_scope_is_function(scope, "func foo()", "return 1", row=4)

    def test_go_type_scope(self, project_with_multi_scope_go: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 8, 5, "Bar")
        assert_scope_is_class(scope, "type Bar struct", "Z int")

    def test_go_method_scope(self, project_with_multi_scope_go: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 12, 14, "meth")
        assert_scope_is_function_or_method(scope, "meth()", "return 0", row=12)

    def test_go_top_level_function_scope(self, project_with_multi_scope_go: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 16, 5, "bar")
        assert_scope_is_function(scope, "func bar()", "return 2", row=16)

    def test_go_outside_bounds(self, project_with_multi_scope_go: str) -> None:
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 99, 0, None))
