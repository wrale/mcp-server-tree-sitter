"""Tests for canonical scope-kind → per-language node type mapping."""

from mcp_server_tree_sitter.language.scope_node_types import (
    ScopeKind,
    get_enclosure_node_types,
    get_scope_node_type,
    node_type_to_kind,
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


# --- Enclosure order ---


def test_python_enclosure_order():
    """Python returns function_definition, class_definition, module in that order."""
    result = get_enclosure_node_types("python")
    assert result == ["function_definition", "class_definition", "module"]


def test_javascript_enclosure_order():
    """JavaScript returns function_declaration, class_declaration, program in that order."""
    result = get_enclosure_node_types("javascript")
    assert result == ["function_declaration", "class_declaration", "program"]


def test_unknown_language_enclosure_returns_default():
    """Unknown language returns documented default and does not raise."""
    result = get_enclosure_node_types("unknown_lang")
    assert result == []


# --- node_type_to_kind ---


def test_node_type_to_kind_python():
    """Python: function_definition→FUNCTION, class_definition→CLASS, module→MODULE."""
    assert node_type_to_kind("python", "function_definition") == ScopeKind.FUNCTION
    assert node_type_to_kind("python", "class_definition") == ScopeKind.CLASS
    assert node_type_to_kind("python", "module") == ScopeKind.MODULE


def test_node_type_to_kind_javascript():
    """JavaScript: function_declaration→FUNCTION, class_declaration→CLASS, program→MODULE."""
    assert node_type_to_kind("javascript", "function_declaration") == ScopeKind.FUNCTION
    assert node_type_to_kind("javascript", "class_declaration") == ScopeKind.CLASS
    assert node_type_to_kind("javascript", "program") == ScopeKind.MODULE


def test_node_type_to_kind_unknown_returns_default():
    """Unknown language or unknown node type returns ScopeKind.MODULE and does not raise."""
    assert node_type_to_kind("unknown_lang", "function_definition") == ScopeKind.MODULE
    assert node_type_to_kind("python", "unknown_node_type") == ScopeKind.MODULE
