"""Query templates for Kotlin language."""

TEMPLATES = {
    "functions": """
        (function_declaration
            name: (simple_identifier) @function.name) @function.def

        (function_declaration
            name: (simple_identifier) @function.name
            function_body: (function_body) @function.body) @function.def
    """,
    "classes": """
        (class_declaration
            name: (simple_identifier) @class.name) @class.def

        (class_declaration
            name: (simple_identifier) @class.name
            class_body: (class_body) @class.body) @class.def
    """,
    "interfaces": """
        (interface_declaration
            name: (simple_identifier) @interface.name) @interface.def

        (interface_declaration
            name: (simple_identifier) @interface.name
            class_body: (class_body) @interface.body) @interface.def
    """,
    "imports": """
        (import_header) @import

        (import_header
            identifier: (identifier) @import.id) @import.simple

        (import_header
            identifier: (dot_qualified_expression) @import.qualified) @import.qualified

        (import_header
            import_alias: (import_alias
                name: (simple_identifier) @import.alias)) @import.aliased
    """,
    "properties": """
        (property_declaration
            variable_declaration: (variable_declaration
                simple_identifier: (simple_identifier) @property.name)) @property.def
    """,
    "dataClasses": """
        (class_declaration
            type: (type_modifiers
                (type_modifier
                    "data" @data_class.modifier))
            name: (simple_identifier) @data_class.name) @data_class.def
    """,
}
