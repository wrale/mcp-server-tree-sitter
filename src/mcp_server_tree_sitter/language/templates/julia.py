"""Query templates for Julia language."""

TEMPLATES = {
    "functions": """
        (function_definition
            name: (identifier) @function.name) @function.def

        (function_definition
            name: (identifier) @function.name
            parameters: (parameter_list) @function.params
            body: (block) @function.body) @function.def

        (short_function_definition
            name: (identifier) @function.name) @function.short_def
    """,
    "modules": """
        (module_definition
            name: (identifier) @module.name
            body: (block) @module.body) @module.def
    """,
    "structs": """
        (struct_definition
            name: (identifier) @struct.name
            body: (block) @struct.body) @struct.def

        (mutable_struct_definition
            name: (identifier) @struct.name
            body: (block) @struct.body) @struct.mutable_def
    """,
    "imports": """
        (import_statement) @import

        (import_statement
            name: (identifier) @import.name) @import.simple

        (using_statement) @using

        (using_statement
            name: (identifier) @using.name) @using.simple

        (import_statement
            name: (dot_expression) @import.qualified) @import.qualified
    """,
    "macros": """
        (macro_definition
            name: (identifier) @macro.name
            body: (block) @macro.body) @macro.def
    """,
    "abstractTypes": """
        (abstract_definition
            name: (identifier) @abstract.name) @abstract.def
    """,
}
