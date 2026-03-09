"""Canonical scope kind → per-language tree-sitter node type mapping.

Single source of truth for which node type means function/class/module per language.
Used by enclosure logic (find_enclosing_scope) to be language-agnostic.

Supported languages: python, javascript.

To add a new language:
  1. Add the language id and node type names to SCOPE_NODE_TYPES for each ScopeKind.
  2. Use the actual tree-sitter grammar node type names (e.g. from language/templates/ or the grammar).
  3. Ensure "module" maps to that language's root or top-level container node type (e.g. "program" for JS).
"""

from enum import Enum
from typing import Optional


class ScopeKind(str, Enum):
    """Canonical scope kinds for enclosure lookup. Use instead of raw strings to avoid typos."""

    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"


# Node type names must match tree-sitter grammar (see language/templates/ and grammars).
SCOPE_NODE_TYPES: dict[str, dict[str, str]] = {
    ScopeKind.FUNCTION.value: {
        "python": "function_definition",
        "javascript": "function_declaration",
    },
    ScopeKind.CLASS.value: {
        "python": "class_definition",
        "javascript": "class_declaration",
    },
    ScopeKind.MODULE.value: {
        "python": "module",
        "javascript": "program",
    },
}


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
