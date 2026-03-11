"""Position tests for get_enclosing_scope on C."""

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


class TestGetEnclosingScopeC:
    """Tests for get_enclosing_scope on C (function_definition, struct_specifier, translation_unit)."""

    MULTI_SCOPE_SOURCE_C = """int x = 42;

int foo(void) {
    return 1;
}

struct Bar {
    int z;
};

int bar(void) {
    return 2;
}
"""

    @pytest.fixture
    def project_with_multi_scope_c(self, tmp_path: Path) -> Generator[str, None, None]:
        test_file = tmp_path / "main.c"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_C, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_c_test", description="C enclosing scope")
        yield "enclosing_scope_c_test"

    def test_c_module_scope(self, project_with_multi_scope_c: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_c, "main.c", 0, 0, "int")
        assert_scope_is_module(scope, "int x = 42", "int foo", "struct Bar")

    def test_c_function_scope(self, project_with_multi_scope_c: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_c, "main.c", 2, 4, "foo")
        assert_scope_is_function(scope, "int foo(void)", "return 1", row=2)

    def test_c_struct_scope(self, project_with_multi_scope_c: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_c, "main.c", 6, 7, "Bar")
        assert_scope_is_class(scope, "struct Bar", "int z")

    def test_c_second_function_scope(self, project_with_multi_scope_c: str) -> None:
        scope = get_enclosing_scope_tool(project_with_multi_scope_c, "main.c", 10, 4, "bar")
        assert_scope_is_function(scope, "int bar(void)", "return 2", row=10)

    def test_c_outside_bounds(self, project_with_multi_scope_c: str) -> None:
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_c, "main.c", 99, 0, None))
