"""Canonical scope kind → per-language tree-sitter node type mapping.

Single source of truth for which node type means function/class/module per language.
Used by enclosure logic (find_enclosing_scope) to be language-agnostic.
"""

from enum import Enum
from typing import Optional


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
    raise NotImplementedError("Scope node type mapping not implemented")
