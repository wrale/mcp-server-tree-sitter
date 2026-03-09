"""Canonical scope kind → per-language tree-sitter node type mapping.

Single source of truth for which node type means function/class/module per language.
Used by enclosure logic (find_enclosing_scope) to be language-agnostic.

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

    Args:
        language: Language id (e.g. "python", "javascript").
        kind: Canonical scope kind (use ScopeKind enum).

    Returns:
        Node type name for that language, or None if unknown language.
    """
    kinds = SCOPE_NODE_TYPES.get(kind.value, {})
    return kinds.get(language)


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

    Args:
        language: Language id (e.g. "python", "javascript").

    Returns:
        List of node type names in enclosure order. For unknown language, returns empty list.
    """
    result: List[str] = []
    for kind in _ENCLOSURE_ORDER:
        node_type = get_scope_node_type(language, kind)
        if node_type is not None:
            result.append(node_type)
    return result
