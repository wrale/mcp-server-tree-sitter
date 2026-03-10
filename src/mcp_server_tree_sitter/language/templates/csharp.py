"""Query templates for C# language."""

TEMPLATES = {
    "functions": """
        (method_declaration
            (identifier) @function.name
            (parameter_list) @function.params
            (block)? @function.body) @function.def

        (constructor_declaration
            (identifier) @constructor.name
            (parameter_list) @constructor.params
            (block) @constructor.body) @constructor.def

        (local_function_statement
            (identifier) @function.name
            (parameter_list) @function.params
            (block) @function.body) @function.def
    """,
    "classes": """
        (class_declaration
            (identifier) @class.name
            (declaration_list) @class.body) @class.def
    """,
    "structs": """
        (struct_declaration
            (identifier) @struct.name
            (declaration_list) @struct.body) @struct.def
    """,
    "interfaces": """
        (interface_declaration
            (identifier) @interface.name
            (declaration_list) @interface.body) @interface.def
    """,
    "enums": """
        (enum_declaration
            (identifier) @enum.name
            (enum_member_declaration_list) @enum.body) @enum.def
    """,
    "imports": """
        (using_directive) @import

        (using_directive
            (qualified_name) @import.name) @import.qualified
    """,
}
