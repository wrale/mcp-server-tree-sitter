"""Position tests for get_enclosing_scope on Rust."""

import pytest

from tests.enclosing_scope.scope_assertions import (
    assert_scope_empty,
    assert_scope_is_class,
    assert_scope_is_function,
    assert_scope_is_module,
)
from tests.test_helpers import get_enclosing_scope_tool, register_project_tool


class TestGetEnclosingScopeRust:
    """Tests for get_enclosing_scope on Rust (function_item, struct_item, impl_item, source_file)."""

    MULTI_SCOPE_SOURCE_RS = """fn main() {
    let x = 1;
}

struct Foo {
    a: i32,
}

impl Foo {
    fn bar(&self) -> i32 {
        42
    }
}
"""

    @pytest.fixture
    def project_with_multi_scope_rust(self, tmp_path):
        test_file = tmp_path / "main.rs"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_RS, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_rust_test", description="Rust enclosing scope")
        yield "enclosing_scope_rust_test"

    def test_rust_module_scope(self, project_with_multi_scope_rust):
        # Position on blank line between main and struct so we're in source_file but not inside a declaration
        scope = get_enclosing_scope_tool(project_with_multi_scope_rust, "main.rs", 3, 0, None)
        assert_scope_is_module(scope, "fn main()", "struct Foo", "impl Foo")

    def test_rust_function_scope(self, project_with_multi_scope_rust):
        scope = get_enclosing_scope_tool(project_with_multi_scope_rust, "main.rs", 0, 3, "main")
        assert_scope_is_function(scope, "fn main()", "let x", row=0)

    def test_rust_struct_scope(self, project_with_multi_scope_rust):
        scope = get_enclosing_scope_tool(project_with_multi_scope_rust, "main.rs", 4, 7, "Foo")
        assert_scope_is_class(scope, "struct Foo", "a: i32")

    def test_rust_impl_scope(self, project_with_multi_scope_rust):
        scope = get_enclosing_scope_tool(project_with_multi_scope_rust, "main.rs", 8, 5, "Foo")
        assert_scope_is_class(scope, "impl Foo", "fn bar")

    def test_rust_method_scope(self, project_with_multi_scope_rust):
        scope = get_enclosing_scope_tool(project_with_multi_scope_rust, "main.rs", 9, 8, "bar")
        assert_scope_is_function(scope, "fn bar", "42", row=9)

    def test_rust_outside_bounds(self, project_with_multi_scope_rust):
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_rust, "main.rs", 99, 0, None))
