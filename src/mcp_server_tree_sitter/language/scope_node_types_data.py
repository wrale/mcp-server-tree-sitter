"""Data: canonical scope kind (string) → per-language tree-sitter node type names.

Keys must match ScopeKind enum values ("function", "class", "module").
Node type names must match tree-sitter grammar (see language/templates/ and grammars).
Each language maps to a list of node type names (one or more per kind).

To add a new language: add the language id and list of node type(s) to each key below.
"""

# kind value -> { language_id -> list of node_type_names }
SCOPE_NODE_TYPES: dict[str, dict[str, list[str]]] = {
    "function": {
        "python": ["function_definition"],
        "javascript": ["function_declaration", "method_definition"],
        "typescript": ["function_declaration", "method_definition"],
        "rust": ["function_item"],
        "go": ["function_declaration", "method_declaration"],
        "c": ["function_definition"],
        "cpp": ["function_definition", "method_definition"],
        "java": ["method_declaration", "constructor_declaration"],
        "csharp": [
            "method_declaration",
            "constructor_declaration",
            "local_function_statement",
        ],
        "swift": ["function_declaration", "computed_getter", "computed_setter"],
        "kotlin": ["function_declaration", "getter", "setter"],
        "julia": ["function_definition"],
    },
    "class": {
        "python": ["class_definition"],
        "javascript": ["class_declaration"],
        "typescript": ["class_declaration"],
        "rust": ["struct_item", "impl_item", "trait_item"],
        "go": ["type_declaration"],
        "c": ["struct_specifier"],
        "cpp": ["class_specifier", "struct_specifier"],
        "java": ["class_declaration", "interface_declaration"],
        "csharp": ["class_declaration", "struct_declaration", "interface_declaration"],
        "swift": ["class_declaration", "struct_declaration"],
        "kotlin": ["class_declaration", "interface_declaration"],
        "julia": ["struct_definition", "mutable_struct_definition"],
    },
    "module": {
        "python": ["module"],
        "javascript": ["program"],
        "typescript": ["program"],
        "rust": ["source_file"],
        "go": ["source_file"],
        "c": ["translation_unit"],
        "cpp": ["translation_unit"],
        "java": ["program"],
        "csharp": ["compilation_unit"],
        "swift": ["source_file"],
        "kotlin": ["kotlin_file"],
        "julia": ["source_file"],
    },
}
