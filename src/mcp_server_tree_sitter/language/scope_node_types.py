"""Canonical scope kind → per-language tree-sitter node type mapping.

Single source of truth for which node type means function/class/module per language.
The enclosure order (get_enclosure_node_types) and kind mapping (node_type_to_kind) from
this module are used by the core helper find_enclosing_scope when walking up the AST
to find the enclosing scope and resolve its kind.

Supported languages: python, javascript.

To add a new language: edit SCOPE_NODE_TYPES in scope_node_types_data.py.
"""

from enum import Enum
from typing import List, Optional

from .scope_node_types_data import SCOPE_NODE_TYPES


class ScopeKind(str, Enum):
    """Canonical scope kinds for enclosure lookup. Use instead of raw strings to avoid typos."""

    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"


def get_scope_node_type(language: str, kind: ScopeKind) -> Optional[str]:
    """
    Return the tree-sitter node type name for a canonical scope kind in a language.
    When a language maps to a list of node types (e.g. function_declaration + method_definition),
    returns the first one (used for enclosure order).

    Args:
        language: Language id (e.g. "python", "javascript").
        kind: Canonical scope kind (use ScopeKind enum).

    Returns:
        Node type name for that language, or None if unknown language.
    """
    node_types = SCOPE_NODE_TYPES.get(kind.value, {}).get(language)
    if not node_types:
        return None
    return node_types[0]


# Enclosure order: most specific first (function, class, module). Built from SCOPE_NODE_TYPES.
_ENCLOSURE_ORDER: List[ScopeKind] = [
    ScopeKind.FUNCTION,
    ScopeKind.CLASS,
    ScopeKind.MODULE,
]


def get_enclosure_node_types(language: str) -> List[str]:
    """
    Return the ordered list of node types that count as enclosing scopes (most specific first).

    Used when walking up the AST to find the enclosing scope: function, then class, then module.
    When a kind maps to multiple node types (e.g. function_declaration + method_definition),
    all are included in order so the most specific scope is found first.

    Args:
        language: Language id (e.g. "python", "javascript").

    Returns:
        List of node type names in enclosure order. For unknown language, returns empty list.
    """
    result: List[str] = []
    for kind in _ENCLOSURE_ORDER:
        node_types = SCOPE_NODE_TYPES.get(kind.value, {}).get(language)
        if node_types:
            result.extend(node_types)
    return result


def node_type_to_kind(language: str, node_type: str) -> ScopeKind:
    """
    Return the canonical scope kind for a node type in a language.

    Used when resolving the enclosing scope node to the return kind. Callers can use .value for the string (e.g. in API responses).

    Args:
        language: Language id (e.g. "python", "javascript").
        node_type: Tree-sitter node type name (e.g. "function_definition").

    Returns:
        ScopeKind. For unknown language or unknown node type, returns ScopeKind.MODULE.
    """
    for kind in _ENCLOSURE_ORDER:
        node_types = SCOPE_NODE_TYPES.get(kind.value, {}).get(language)
        if node_types and node_type in node_types:
            return kind
    return ScopeKind.MODULE
