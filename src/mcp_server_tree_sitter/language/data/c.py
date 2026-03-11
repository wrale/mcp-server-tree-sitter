"""C language data."""

from ..schema import LanguageDataBase


class C(LanguageDataBase):
    id = "c"
    extensions = ["c", "h"]
    scope_node_types = {
        "function": ["function_definition"],
        "class": ["struct_specifier"],
        "module": ["translation_unit"],
    }
    query_templates = {
        "functions": """
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @function.name)) @function.def

        (declaration
            declarator: (function_declarator
                declarator: (identifier) @function.name)) @function.decl
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
            path: (string_literal) @import.system) @import.system

        (preproc_include
            path: (system_lib_string) @import.system) @import.system
    """,
        "macros": """
        (preproc_function_def
            name: (identifier) @macro.name) @macro.def
    """,
    }
    default_symbol_types = ["functions", "structs", "imports"]
    node_type_descriptions = {}
