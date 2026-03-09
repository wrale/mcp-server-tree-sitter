"""Tests for canonical scope-kind → per-language node type mapping."""

from mcp_server_tree_sitter.language.scope_node_types import (
    ScopeKind,
    get_scope_node_type,
)


def test_python_function_returns_function_definition():
    """For language=python and kind=FUNCTION, assert node type is function_definition."""
    assert get_scope_node_type("python", ScopeKind.FUNCTION) == "function_definition"


def test_python_class_returns_class_definition():
    """For language=python and kind=CLASS, assert node type is class_definition."""
    assert get_scope_node_type("python", ScopeKind.CLASS) == "class_definition"


def test_python_module_returns_module():
    """For language=python and kind=MODULE, assert node type is module."""
    assert get_scope_node_type("python", ScopeKind.MODULE) == "module"


def test_javascript_function_returns_function_declaration():
    """For language=javascript and kind=FUNCTION, assert node type is function_declaration."""
    assert get_scope_node_type("javascript", ScopeKind.FUNCTION) == "function_declaration"


def test_javascript_class_returns_class_declaration():
    """For language=javascript and kind=CLASS, assert node type is class_declaration."""
    assert get_scope_node_type("javascript", ScopeKind.CLASS) == "class_declaration"


def test_javascript_module_returns_program():
    """For language=javascript and kind=MODULE, assert node type is program."""
    assert get_scope_node_type("javascript", ScopeKind.MODULE) == "program"


def test_unknown_language_returns_none():
    """For unknown language, getter returns None and does not raise."""
    result = get_scope_node_type("unknown_lang", ScopeKind.FUNCTION)
    assert result is None
