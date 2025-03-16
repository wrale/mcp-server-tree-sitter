"""Query templates for JavaScript."""

TEMPLATES = {
    "functions": """
        (function_declaration
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (statement_block) @function.body) @function.def

        (arrow_function
            parameters: (formal_parameters) @function.params
            body: (_) @function.body) @function.def
    """,
    "classes": """
        (class_declaration
            name: (identifier) @class.name
            body: (class_body) @class.body) @class.def
    """,
    "imports": """
        (import_statement) @import

        (import_statement
            source: (string) @import.source
            specifier: (_) @import.specifier) @import.full
    """,
    "function_calls": """
        (call_expression
            function: (identifier) @call.function
            arguments: (arguments) @call.args) @call
    """,
    "assignments": """
        (variable_declarator
            name: (_) @assign.target
            value: (_) @assign.value) @assign
    """,
}
