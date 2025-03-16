"""Query templates for TypeScript."""

TEMPLATES = {
    "functions": """
        (function_declaration
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (statement_block) @function.body) @function.def

        (arrow_function
            parameters: (formal_parameters) @function.params
            body: (_) @function.body) @function.def

        (method_definition
            name: (property_identifier) @method.name
            parameters: (formal_parameters) @method.params
            body: (statement_block) @method.body) @method.def
    """,
    "classes": """
        (class_declaration
            name: (type_identifier) @class.name
            body: (class_body) @class.body) @class.def
    """,
    "interfaces": """
        (interface_declaration
            name: (type_identifier) @interface.name
            body: (object_type) @interface.body) @interface.def

        (type_alias_declaration
            name: (type_identifier) @alias.name
            value: (_) @alias.value) @alias.def
    """,
    "imports": """
        (import_statement) @import

        (import_statement
            source: (string) @import.source) @import.source_only

        (import_statement
            source: (string) @import.source
            specifier: (named_imports
                (import_specifier
                    name: (identifier) @import.name))) @import.named

        (import_statement
            source: (string) @import.source
            specifier: (namespace_import
                name: (identifier) @import.namespace)) @import.namespace
    """,
}
