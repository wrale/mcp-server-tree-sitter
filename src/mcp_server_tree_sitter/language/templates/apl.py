"""Query templates for APL language."""

TEMPLATES = {
    "functions": """
        (function_definition
            name: (identifier) @function.name
            body: (block) @function.body) @function.def
    """,
    "namespaces": """
        (namespace_declaration
            name: (identifier) @namespace.name) @namespace.def
    """,
    "variables": """
        (assignment
            left: (identifier) @variable.name) @variable.def
    """,
    "imports": """
        (import_statement
            module: (identifier) @import.module) @import
    """,
    "operators": """
        (operator_definition
            operator: (_) @operator.sym
            body: (block) @operator.body) @operator.def
    """,
    "classes": """
        (class_definition
            name: (identifier) @class.name
            body: (block) @class.body) @class.def
    """,
}
