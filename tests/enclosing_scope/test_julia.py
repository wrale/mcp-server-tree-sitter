"""Position tests for get_enclosing_scope on Julia."""

import pytest

from tests.enclosing_scope.scope_assertions import (
    assert_scope_empty,
    assert_scope_is_class,
    assert_scope_is_function,
    assert_scope_is_module,
)
from tests.test_helpers import get_enclosing_scope_tool, register_project_tool


class TestGetEnclosingScopeJulia:
    """Tests for get_enclosing_scope on Julia (function_definition, struct_definition, source_file)."""

    MULTI_SCOPE_SOURCE_JL = """const x = 42

function foo()
    return 1
end

struct Bar
    z
end

function bar()
    return 2
end
"""

    @pytest.fixture
    def project_with_multi_scope_julia(self, tmp_path):
        test_file = tmp_path / "main.jl"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_JL, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_julia_test", description="Julia enclosing scope")
        yield "enclosing_scope_julia_test"

    def test_julia_module_scope(self, project_with_multi_scope_julia):
        scope = get_enclosing_scope_tool(project_with_multi_scope_julia, "main.jl", 0, 0, "const")
        assert_scope_is_module(scope, "const x = 42", "function foo", "struct Bar")

    def test_julia_function_scope(self, project_with_multi_scope_julia):
        scope = get_enclosing_scope_tool(project_with_multi_scope_julia, "main.jl", 2, 9, "foo")
        assert_scope_is_function(scope, "function foo()", "return 1", row=2)

    def test_julia_struct_scope(self, project_with_multi_scope_julia):
        scope = get_enclosing_scope_tool(project_with_multi_scope_julia, "main.jl", 6, 7, "Bar")
        assert_scope_is_class(scope, "struct Bar", "z")

    def test_julia_second_function_scope(self, project_with_multi_scope_julia):
        scope = get_enclosing_scope_tool(project_with_multi_scope_julia, "main.jl", 10, 9, "bar")
        assert_scope_is_function(scope, "function bar()", "return 2", row=10)

    def test_julia_outside_bounds(self, project_with_multi_scope_julia):
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_julia, "main.jl", 99, 0, None))
