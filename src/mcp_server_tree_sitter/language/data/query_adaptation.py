"""Query adaptation: (from_language, to_language) -> { node_type -> node_type }.

Used by adapt_query_for_language to rewrite tree-sitter node type names when
translating a query from one language to another. Keys are (from_lang_id, to_lang_id).
"""

# (from_language, to_language) -> { source_node_type: target_node_type }
QUERY_ADAPTATION: dict[tuple[str, str], dict[str, str]] = {
    ("python", "javascript"): {
        "function_definition": "function_declaration",
        "class_definition": "class_declaration",
        "block": "statement_block",
        "parameters": "formal_parameters",
        "argument_list": "arguments",
        "import_statement": "import_statement",
        "call": "call_expression",
    },
    ("javascript", "python"): {
        "function_declaration": "function_definition",
        "class_declaration": "class_definition",
        "statement_block": "block",
        "formal_parameters": "parameters",
        "arguments": "argument_list",
        "call_expression": "call",
    },
}
