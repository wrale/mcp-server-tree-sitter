"""Query templates for C++ language."""

TEMPLATES = {
    "functions": """
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @function.name)) @function.def

        (declaration
            declarator: (function_declarator
                declarator: (identifier) @function.name)) @function.decl

        (method_definition
            declarator: (function_declarator
                declarator: (field_identifier) @method.name)) @method.def
    """,
    "classes": """
        (class_specifier
            name: (type_identifier) @class.name) @class.def
    """,
    "structs": """
        (struct_specifier
            name: (type_identifier) @struct.name) @struct.def

        (union_specifier
            name: (type_identifier) @union.name) @union.def

        (enum_specifier
            name: (type_identifier) @enum.name) @enum.def
    """,
    "imports": """
        (preproc_include) @import

        (preproc_include
            path: (string_literal) @import.path) @import.user

        (preproc_include
            path: (system_lib_string) @import.path) @import.system

        (namespace_definition
            name: (namespace_identifier) @import.namespace) @import.namespace_def
    """,
    "templates": """
        (template_declaration) @template.def

        (template_declaration
            declaration: (class_specifier
                name: (type_identifier) @template.class)) @template.class_def
    """,
}
