"""Integration tests for get_enclosing_scope_for_path."""

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from mcp_server_tree_sitter.api import (
    get_language_registry,
    get_project_registry,
    get_tree_cache,
)
from mcp_server_tree_sitter.tools.ast_operations import get_enclosing_scope_for_path
from tests.test_helpers import register_project_tool, get_enclosing_scope_tool

from mcp_server_tree_sitter.language.registry import LanguageRegistry
from mcp_server_tree_sitter.models.ast import find_enclosing_scope


# --- Helpers for scope assertions (shared by Python and JavaScript tests) ---

SCOPE_KEYS = {"kind", "text", "start_line", "end_line"}


def assert_scope_has_keys(scope: Dict[str, Any]) -> None:
    """Assert the scope dict has exactly the expected keys."""
    assert set(scope.keys()) == SCOPE_KEYS, f"Expected keys {SCOPE_KEYS}, got {set(scope.keys())}"


def assert_scope_is_module(scope: Dict[str, Any], *text_contains: str) -> None:
    """Assert scope is module and optional text snippets are present."""
    assert_scope_has_keys(scope)
    assert scope["kind"] == "module", f"Expected kind 'module', got {scope.get('kind')}"
    for snippet in text_contains:
        assert snippet in scope["text"], f"Expected '{snippet}' in scope text"


def assert_scope_is_function(
    scope: Dict[str, Any],
    *text_contains: str,
    row: Optional[int] = None,
) -> None:
    """Assert scope is function and optional text snippets are present; optionally check row in range."""
    assert_scope_has_keys(scope)
    assert scope["kind"] == "function", f"Expected kind 'function', got {scope.get('kind')}"
    for snippet in text_contains:
        assert snippet in scope["text"], f"Expected '{snippet}' in scope text"
    if row is not None:
        assert scope["start_line"] <= row <= scope["end_line"], (
            f"Expected {row} in [start_line, end_line] = [{scope['start_line']}, {scope['end_line']}]"
        )


def assert_scope_is_function_or_method(
    scope: Dict[str, Any],
    *text_contains: str,
    row: Optional[int] = None,
) -> None:
    """Assert scope is function or method and optional text snippets are present."""
    assert_scope_has_keys(scope)
    assert scope["kind"] in ("function", "method"), f"Expected kind function/method, got {scope.get('kind')}"
    for snippet in text_contains:
        assert snippet in scope["text"], f"Expected '{snippet}' in scope text"
    if row is not None:
        assert scope["start_line"] <= row <= scope["end_line"]


def assert_scope_is_class(scope: Dict[str, Any], *text_contains: str, row: Optional[int] = None) -> None:
    """Assert scope is class and optional text snippets are present."""
    assert_scope_has_keys(scope)
    assert scope["kind"] == "class", f"Expected kind 'class', got {scope.get('kind')}"
    for snippet in text_contains:
        assert snippet in scope["text"], f"Expected '{snippet}' in scope text"
    if row is not None:
        assert scope["start_line"] <= row <= scope["end_line"]


def assert_scope_empty(scope: Dict[str, Any]) -> None:
    """Assert scope is empty (e.g. position outside file)."""
    assert scope == {}, f"Expected empty dict, got {scope}"


class TestGetEnclosingScope:
    """Tests for get_enclosing_scope tool. Positions are first character of a token (0-based row, column)."""

    # Fixed source: predictable 0-based line numbers.
    # Line 0: import os
    # Line 1: (blank)
    # Line 2: X = 42  (module level, outside any class/function)
    # Line 3: (blank)
    # Line 4: def foo():
    # Line 5:     return 1
    # Line 6: (blank)
    # Line 7: class Bar:
    # Line 8:     z = 0
    # Line 9:     def meth(self):
    # Line 10:        pass
    # Line 11: (blank)
    # Line 12: def bar():  (top-level function outside class)
    # Line 13:     return 2
    MULTI_SCOPE_SOURCE = """import os

X = 42

def foo():
    return 1

class Bar:
    z = 0
    def meth(self):
        pass

def bar():
    return 2
"""

    @pytest.fixture
    def project_with_multi_scope(self, tmp_path):
        """Register a temp project with test.py containing module, function, class, and method."""
        test_file = tmp_path / "test.py"
        test_file.write_text(self.MULTI_SCOPE_SOURCE, encoding="utf-8")
        register_project_tool(
            str(tmp_path),
            name="enclosing_scope_api_test",
            description="Test project for get_enclosing_scope API",
        )
        yield "enclosing_scope_api_test"

    def test_position_at_import_returns_module_scope(self, project_with_multi_scope):
        """Position at first char of 'import' (0, 0) → module scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 0, 0, "import")
        assert_scope_is_module(scope, "import os", "def foo()", "class Bar")

    def test_position_at_module_level_assignment_returns_module_scope(self, project_with_multi_scope):
        """Position at first char of 'X' (2, 0) in X = 42 → module scope (code outside class/function)."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 2, 0, "X")
        assert_scope_is_module(scope, "X = 42", "import os", "def foo()", "def bar()")

    def test_position_at_function_name_returns_function_scope(self, project_with_multi_scope):
        """Position at first char of 'foo' (4, 4) → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 4, 4, "foo")
        assert_scope_is_function(scope, "def foo()", "return 1", row=4)

    def test_position_at_return_inside_foo_returns_function_scope(self, project_with_multi_scope):
        """Position at first char of 'return' (5, 4) inside foo → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 5, 4, "return")
        assert_scope_is_function(scope, "def foo()", "return 1", row=5)

    def test_position_at_class_keyword_returns_class_scope(self, project_with_multi_scope):
        """Position at first char of 'class' (7, 0) → class scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 7, 0, "class")
        assert_scope_is_class(scope, "class Bar:", "z = 0", "def meth(self):")

    def test_position_at_class_name_returns_class_scope(self, project_with_multi_scope):
        """Position at first char of 'Bar' (7, 6) → class scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 7, 6, "Bar")
        assert_scope_is_class(scope, "class Bar:")

    def test_position_in_class_body_not_in_method_returns_class_scope(self, project_with_multi_scope):
        """Position at first char of 'z' (8, 4) in class body → class scope, not method."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 8, 4, "z")
        assert_scope_is_class(scope, "class Bar:", "z = 0", row=8)

    def test_position_at_method_name_returns_method_scope(self, project_with_multi_scope):
        """Position at first char of 'meth' (9, 8) → method scope (kind function)."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 9, 8, "meth")
        assert_scope_is_function_or_method(scope, "meth", "pass")

    def test_position_at_pass_inside_method_returns_method_scope(self, project_with_multi_scope):
        """Position at first char of 'pass' (10, 8) inside meth → method scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 10, 8, "pass")
        assert_scope_is_function_or_method(scope, "def meth(self):", "pass", row=10)

    def test_position_at_def_inside_class_returns_function_scope(self, project_with_multi_scope):
        """Position at first char of inner 'def' (9, 4) → method/function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 9, 4, "def")
        assert_scope_is_function_or_method(scope, "def meth(self):", "pass")

    def test_position_at_second_top_level_function_returns_function_scope(self, project_with_multi_scope):
        """Position at first char of 'bar' (12, 4) → function scope (top-level bar, outside class)."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 12, 4, "bar")
        assert_scope_is_function(scope, "def bar()", "return 2", row=12)

    def test_position_at_return_inside_bar_returns_function_scope(self, project_with_multi_scope):
        """Position at first char of 'return' (13, 4) inside bar → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 13, 4, "return")
        assert_scope_is_function(scope, "def bar()", "return 2", row=13)

    def test_position_outside_file_boundaries_returns_empty_scope(self, project_with_multi_scope):
        """Position beyond last line (outside file) → empty dict, no scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope, "test.py", 99, 0, None)
        assert_scope_empty(scope)


class TestGetEnclosingScopeJavaScript:
    """Tests for get_enclosing_scope tool on JavaScript. Positions are first character of a token (0-based)."""

    # Fixed source: predictable 0-based line numbers.
    # Line 0: const X = 42;  (module level)
    # Line 1: (blank)
    # Line 2: function foo() {
    # Line 3:   return 1;
    # Line 4: }
    # Line 5: (blank)
    # Line 6: class Bar {
    # Line 7:   z = 0;
    # Line 8:   meth() {
    # Line 9:     return;
    # Line 10:   }
    # Line 11: }
    # Line 12: (blank)
    # Line 13: function bar() {
    # Line 14:   return 2;
    # Line 15: }
    MULTI_SCOPE_SOURCE_JS = """const X = 42;

function foo() {
  return 1;
}

class Bar {
  z = 0;
  meth() {
    return;
  }
}

function bar() {
  return 2;
}
"""

    @pytest.fixture
    def project_with_multi_scope_js(self, tmp_path):
        """Register a temp project with test.js containing program, function, class, and method."""
        test_file = tmp_path / "test.js"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_JS, encoding="utf-8")
        register_project_tool(
            str(tmp_path),
            name="enclosing_scope_js_test",
            description="Test project for get_enclosing_scope API (JavaScript)",
        )
        yield "enclosing_scope_js_test"

    def test_js_position_at_const_returns_module_scope(self, project_with_multi_scope_js):
        """Position at first char of 'const' (0, 0) → module scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 0, 0, "const")
        assert_scope_is_module(scope, "const X = 42", "function foo", "class Bar", "function bar")

    def test_js_position_at_module_level_variable_returns_module_scope(self, project_with_multi_scope_js):
        """Position at first char of 'X' (0, 6) in const X = 42 → module scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 0, 6, "X")
        assert_scope_is_module(scope, "const X = 42", "function foo", "class Bar", "function bar")

    def test_js_position_at_foo_returns_function_scope(self, project_with_multi_scope_js):
        """Position at first char of 'foo' (2, 9) → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 2, 9, "foo")
        assert_scope_is_function(scope, "function foo()", "return 1", row=2)

    def test_js_position_at_return_inside_foo_returns_function_scope(self, project_with_multi_scope_js):
        """Position at first char of 'return' (3, 2) inside foo → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 3, 2, "return")
        assert_scope_is_function(scope, "function foo()", "return 1", row=3)

    def test_js_position_at_class_returns_class_scope(self, project_with_multi_scope_js):
        """Position at first char of 'class' (6, 0) → class scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 6, 0, "class")
        assert_scope_is_class(scope, "class Bar", "z = 0", "meth()")

    def test_js_position_at_Bar_returns_class_scope(self, project_with_multi_scope_js):
        """Position at first char of 'Bar' (6, 6) → class scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 6, 6, "Bar")
        assert_scope_is_class(scope, "class Bar")

    def test_js_position_in_class_body_not_in_method_returns_class_scope(self, project_with_multi_scope_js):
        """Position at first char of 'z' (7, 2) in class body → class scope, not method."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 7, 2, "z")
        assert_scope_is_class(scope, "class Bar", "z = 0", row=7)

    def test_js_position_at_meth_returns_method_scope(self, project_with_multi_scope_js):
        """Position at first char of 'meth' (8, 2) → method scope (kind function)."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 8, 2, "meth")
        assert_scope_is_function_or_method(scope, "meth()", "return", row=8)

    def test_js_position_at_return_inside_meth_returns_method_scope(self, project_with_multi_scope_js):
        """Position at first char of 'return' (9, 4) inside meth → method scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 9, 4, "return")
        assert_scope_is_function_or_method(scope, "meth()", "return", row=9)

    def test_js_position_at_bar_returns_function_scope(self, project_with_multi_scope_js):
        """Position at first char of 'bar' (13, 9) → function scope (top-level, outside class)."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 13, 9, "bar")
        assert_scope_is_function(scope, "function bar()", "return 2", row=13)

    def test_js_position_at_return_inside_bar_returns_function_scope(self, project_with_multi_scope_js):
        """Position at first char of 'return' (14, 2) inside bar → function scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 14, 2, "return")
        assert_scope_is_function(scope, "function bar()", "return 2", row=14)

    def test_js_position_outside_file_boundaries_returns_empty_scope(self, project_with_multi_scope_js):
        """Position beyond last line (outside file) → empty dict, no scope."""
        scope = get_enclosing_scope_tool(project_with_multi_scope_js, "test.js", 99, 0, None)
        assert_scope_empty(scope)

    def test_js_constructor_returns_function_scope(self, project_with_constructor_js):
        """Position inside a JS class constructor() body → function scope (constructor is method_definition)."""
        # Position inside constructor body block (line with "this.n = n;")
        scope = get_enclosing_scope_tool(project_with_constructor_js, "box.js", 2, 8, "this")
        assert_scope_is_function_or_method(scope, "constructor", "this.n = n", row=2)

    @pytest.fixture
    def project_with_constructor_js(self, tmp_path):
        source = """class Box {
    constructor(n) {
        this.n = n;
    }
}
"""
        (tmp_path / "box.js").write_text(source, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_js_ctor_test", description="JS constructor scope")
        yield "enclosing_scope_js_ctor_test"


class TestGetEnclosingScopeTypeScript:
    """Tests for get_enclosing_scope on TypeScript. Same structure as JavaScript (program, function_declaration, method_definition, class_declaration)."""

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
    def project_with_multi_scope_go(self, tmp_path):
        test_file = tmp_path / "main.go"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_GO, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_go_test", description="Go enclosing scope")
        yield "enclosing_scope_go_test"

    def test_go_module_scope(self, project_with_multi_scope_go):
        scope = get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 0, 0, "package")
        assert_scope_is_module(scope, "package p", "func foo", "type Bar")

    def test_go_function_scope(self, project_with_multi_scope_go):
        scope = get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 4, 5, "foo")
        assert_scope_is_function(scope, "func foo()", "return 1", row=4)

    def test_go_type_scope(self, project_with_multi_scope_go):
        scope = get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 8, 5, "Bar")
        assert_scope_is_class(scope, "type Bar struct", "Z int")

    def test_go_method_scope(self, project_with_multi_scope_go):
        scope = get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 12, 14, "meth")
        assert_scope_is_function_or_method(scope, "meth()", "return 0", row=12)

    def test_go_top_level_function_scope(self, project_with_multi_scope_go):
        scope = get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 16, 5, "bar")
        assert_scope_is_function(scope, "func bar()", "return 2", row=16)

    def test_go_outside_bounds(self, project_with_multi_scope_go):
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_go, "main.go", 99, 0, None))


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
    def project_with_multi_scope_c(self, tmp_path):
        test_file = tmp_path / "main.c"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_C, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_c_test", description="C enclosing scope")
        yield "enclosing_scope_c_test"

    def test_c_module_scope(self, project_with_multi_scope_c):
        scope = get_enclosing_scope_tool(project_with_multi_scope_c, "main.c", 0, 0, "int")
        assert_scope_is_module(scope, "int x = 42", "int foo", "struct Bar")

    def test_c_function_scope(self, project_with_multi_scope_c):
        scope = get_enclosing_scope_tool(project_with_multi_scope_c, "main.c", 2, 4, "foo")
        assert_scope_is_function(scope, "int foo(void)", "return 1", row=2)

    def test_c_struct_scope(self, project_with_multi_scope_c):
        scope = get_enclosing_scope_tool(project_with_multi_scope_c, "main.c", 6, 7, "Bar")
        assert_scope_is_class(scope, "struct Bar", "int z")

    def test_c_second_function_scope(self, project_with_multi_scope_c):
        scope = get_enclosing_scope_tool(project_with_multi_scope_c, "main.c", 10, 4, "bar")
        assert_scope_is_function(scope, "int bar(void)", "return 2", row=10)

    def test_c_outside_bounds(self, project_with_multi_scope_c):
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_c, "main.c", 99, 0, None))


class TestGetEnclosingScopeCpp:
    """Tests for get_enclosing_scope on C++ (function_definition, method_definition, class_specifier, translation_unit)."""

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
    def project_with_multi_scope_cpp(self, tmp_path):
        test_file = tmp_path / "main.cpp"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_CPP, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_cpp_test", description="C++ enclosing scope")
        yield "enclosing_scope_cpp_test"

    def test_cpp_module_scope(self, project_with_multi_scope_cpp):
        scope = get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 0, 0, "int")
        assert_scope_is_module(scope, "int x = 42", "int foo()", "class Bar")

    def test_cpp_function_scope(self, project_with_multi_scope_cpp):
        scope = get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 2, 4, "foo")
        assert_scope_is_function(scope, "int foo()", "return 1", row=2)

    def test_cpp_class_scope(self, project_with_multi_scope_cpp):
        scope = get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 6, 6, "Bar")
        assert_scope_is_class(scope, "class Bar", "int z", "meth()")

    def test_cpp_method_scope(self, project_with_multi_scope_cpp):
        scope = get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 9, 8, "meth")
        assert_scope_is_function_or_method(scope, "int meth()", "return 0", row=9)

    def test_cpp_second_function_scope(self, project_with_multi_scope_cpp):
        scope = get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 15, 4, "bar")
        assert_scope_is_function(scope, "int bar()", "return 2", row=15)

    def test_cpp_outside_bounds(self, project_with_multi_scope_cpp):
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_cpp, "main.cpp", 99, 0, None))

    def test_cpp_constructor_returns_function_scope(self, project_with_constructor_destructor_cpp):
        """Position inside a C++ constructor body → function scope (grammar aliases it to function_definition)."""
        scope = get_enclosing_scope_tool(project_with_constructor_destructor_cpp, "box.cpp", 4, 8, "n")
        assert_scope_is_function(scope, "Box(", "n = 0", row=4)

    def test_cpp_destructor_returns_function_scope(self, project_with_constructor_destructor_cpp):
        """Position inside a C++ destructor body → function scope (grammar aliases it to function_definition)."""
        scope = get_enclosing_scope_tool(project_with_constructor_destructor_cpp, "box.cpp", 8, 4, "delete")
        assert_scope_is_function(scope, "~Box()", "delete", row=8)

    @pytest.fixture
    def project_with_constructor_destructor_cpp(self, tmp_path):
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
        register_project_tool(str(tmp_path), name="enclosing_scope_cpp_ctor_test", description="C++ constructor/destructor scope")
        yield "enclosing_scope_cpp_ctor_test"


class TestGetEnclosingScopeJava:
    """Tests for get_enclosing_scope on Java (method_declaration, constructor_declaration, class_declaration, program)."""

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
    def project_with_multi_scope_java(self, tmp_path):
        test_file = tmp_path / "Test.java"
        test_file.write_text(self.MULTI_SCOPE_SOURCE_JAVA, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_java_test", description="Java enclosing scope")
        yield "enclosing_scope_java_test"

    def test_java_module_scope(self, project_with_multi_scope_java):
        scope = get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 0, 0, "import")
        assert_scope_is_module(scope, "import java.util.List", "public class Test")

    def test_java_class_scope(self, project_with_multi_scope_java):
        scope = get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 2, 13, "Test")
        assert_scope_is_class(scope, "public class Test", "int x", "foo()", "bar()")

    def test_java_field_in_class_scope(self, project_with_multi_scope_java):
        scope = get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 4, 8, "x")
        assert_scope_is_class(scope, "public class Test", "int x", row=4)

    def test_java_method_scope(self, project_with_multi_scope_java):
        scope = get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 6, 16, "foo")
        assert_scope_is_function(scope, "public int foo()", "return 1", row=6)

    def test_java_second_method_scope(self, project_with_multi_scope_java):
        scope = get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 10, 16, "bar")
        assert_scope_is_function(scope, "public int bar()", "return 2", row=10)

    def test_java_outside_bounds(self, project_with_multi_scope_java):
        assert_scope_empty(get_enclosing_scope_tool(project_with_multi_scope_java, "Test.java", 99, 0, None))

    def test_java_constructor_returns_function_scope(self, project_with_constructor_java):
        """Position inside a Java constructor body → function scope (constructor is constructor_declaration)."""
        # Position inside constructor body: line 4 is "        this.n = n;" (0-based)
        scope = get_enclosing_scope_tool(project_with_constructor_java, "Box.java", 4, 14, "this")
        assert_scope_is_function(scope, "public Box(int n)", "this.n = n", row=4)

    @pytest.fixture
    def project_with_constructor_java(self, tmp_path):
        source = """public class Box {
    private int n;

    public Box(int n) {
        this.n = n;
    }
}
"""
        (tmp_path / "Box.java").write_text(source, encoding="utf-8")
        register_project_tool(str(tmp_path), name="enclosing_scope_java_ctor_test", description="Java constructor scope")
        yield "enclosing_scope_java_ctor_test"


class TestGetEnclosingScopeSwift:
    """Tests for get_enclosing_scope on Swift (function_declaration, class_declaration, struct_declaration, source_file)."""

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
        register_project_tool(str(tmp_path), name="enclosing_scope_swift_accessors_test", description="Swift getter/setter scope")
        yield "enclosing_scope_swift_accessors_test"


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
        register_project_tool(str(tmp_path), name="enclosing_scope_kotlin_accessors_test", description="Kotlin getter/setter scope")
        yield "enclosing_scope_kotlin_accessors_test"


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


class TestFindEnclosingScope:
    """Tests for find_enclosing_scope helper."""

    # Fixed source so line numbers are predictable (0-based).
    # Line 0: import
    # Line 3: def foo
    # Line 4:   return (inside foo)
    # Line 6: class Bar
    # Line 7:   z = 0 (inside class, not in a method)
    # Line 8:   def meth
    PYTHON_SOURCE = b"""import os

    def foo():
        return 1

    class Bar:
        z = 0
        def meth(self):
            pass
    """

    @pytest.fixture
    def python_tree_and_source(self):
        """Parse PYTHON_SOURCE with Python and return (tree, source_bytes)."""
        registry = LanguageRegistry()
        parser = registry.get_parser("python")
        tree = parser.parse(self.PYTHON_SOURCE)
        return tree, self.PYTHON_SOURCE

    def test_position_inside_function_returns_function_scope(self, python_tree_and_source):
        """Position inside function body → kind function, text contains function, start_line <= row <= end_line."""
        tree, source_bytes = python_tree_and_source
        root = tree.root_node
        row, col, label = 3, 4, "foo"
        result = find_enclosing_scope(root, source_bytes, row, col, label, "python")
        assert_scope_is_function(result, "def foo()", "return 1", row=row)

    def test_position_on_import_returns_module_scope(self, python_tree_and_source):
        """Position on import line → kind is module/namespace, text includes the import."""
        tree, source_bytes = python_tree_and_source
        root = tree.root_node
        result = find_enclosing_scope(root, source_bytes, 0, 0, "import", "python")
        assert_scope_is_module(result, "import", "def foo()", "return 1", "class Bar")

    def test_position_in_class_body_not_in_method_returns_class_scope(self, python_tree_and_source):
        """Position inside class body but not inside a method → kind is class, text contains class definition."""
        tree, source_bytes = python_tree_and_source
        root = tree.root_node
        result = find_enclosing_scope(root, source_bytes, 6, 4, "z", "python")
        assert_scope_is_class(result, "class Bar")


class TestEnclosingScopeForPath:

    # Fixed source: def hello(): on line 0, return on line 1 (0-based).
    # Position (1, 4) is inside the function body.
    PROJECT_SOURCE = """def hello():
        return 1
    """


    @pytest.fixture
    def project_with_python_file(self):
        """Register a temporary project with test.py containing one function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            test_py = root / "test.py"
            test_py.write_text(self.PROJECT_SOURCE, encoding="utf-8")
            name = "enclosing_scope_integration_test"
            register_project_tool(path=str(root), name=name)
            yield {"name": name, "root": root}


    def test_get_enclosing_scope_for_path_returns_scope_dict(self, project_with_python_file):
        """Register temp project with test.py; call get_enclosing_scope_for_path; assert result has kind,
        text, start_line, end_line and position inside function gives function scope."""
        project_registry = get_project_registry()
        project = project_registry.get_project(project_with_python_file["name"])
        language_registry = get_language_registry()
        tree_cache = get_tree_cache()

        # Position (1, 4) is inside "    return 1" (inside hello body)
        result = get_enclosing_scope_for_path(
            project, "test.py", 1, 4, "return", language_registry, tree_cache
        )

        assert_scope_is_function(result, "def hello", "return 1", row=1)
