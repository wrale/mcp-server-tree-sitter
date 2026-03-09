"""Data: canonical scope kind (string) → per-language tree-sitter node type names.

Keys must match ScopeKind enum values ("function", "class", "module").
Node type names must match tree-sitter grammar (see language/templates/ and grammars).

To add a new language: add the language id and node type to each key below.
"""

# kind value -> { language_id -> node_type_name }
SCOPE_NODE_TYPES: dict[str, dict[str, str]] = {
    "function": {
        "python": "function_definition",
        "javascript": "function_declaration",
    },
    "class": {
        "python": "class_definition",
        "javascript": "class_declaration",
    },
    "module": {
        "python": "module",
        "javascript": "program",
    },
}
