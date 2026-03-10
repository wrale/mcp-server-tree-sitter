"""Java language data."""

from ..schema import LanguageDataBase


class Java(LanguageDataBase):
    id = "java"
    extensions = ["java"]
    scope_node_types = {
        "function": ["method_declaration", "constructor_declaration"],
        "class": ["class_declaration", "interface_declaration"],
        "module": ["program"],
    }
    query_templates = {
        "functions": """
        (method_declaration
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (block) @function.body) @function.def

        (constructor_declaration
            name: (identifier) @constructor.name
            parameters: (formal_parameters) @constructor.params
            body: (block) @constructor.body) @constructor.def
    """,
        "classes": """
        (class_declaration
            name: (identifier) @class.name
            body: (class_body) @class.body) @class.def
    """,
        "interfaces": """
        (interface_declaration
            name: (identifier) @interface.name
            body: (class_body) @interface.body) @interface.def
    """,
        "imports": """
        (import_declaration) @import

        (import_declaration
            name: (qualified_name) @import.name) @import.qualified

        (import_declaration
            name: (qualified_name
                name: (identifier) @import.class)) @import.class

        (import_declaration
            asterisk: "*") @import.wildcard
    """,
        "annotations": """
        (annotation
            name: (identifier) @annotation.name) @annotation

        (annotation_type_declaration
            name: (identifier) @annotation.type_name) @annotation.type
    """,
        "enums": """
        (enum_declaration
            name: (identifier) @enum.name
            body: (enum_body) @enum.body) @enum.def
    """,
    }
    node_type_descriptions = {}
