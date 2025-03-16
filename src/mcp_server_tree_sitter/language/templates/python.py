"""Query templates for Python."""

TEMPLATES = {
    "functions": """
        (function_definition
            name: (identifier) @function.name
            parameters: (parameters) @function.params
            body: (block) @function.body) @function.def
    """,
    "classes": """
        (class_definition
            name: (identifier) @class.name
            body: (block) @class.body) @class.def
    """,
    "imports": """
        (import_statement
            name: (dotted_name) @import.module) @import

        (import_from_statement
            module_name: (dotted_name) @import.from
            name: (dotted_name) @import.item) @import
    """,
    "function_calls": """
        (call
            function: (identifier) @call.function
            arguments: (argument_list) @call.args) @call
    """,
    "assignments": """
        (assignment
            left: (_) @assign.target
            right: (_) @assign.value) @assign
    """,
}
