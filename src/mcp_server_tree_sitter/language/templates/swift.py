"""Query templates for Swift language."""

TEMPLATES = {
    "functions": """
        (function_declaration
            name: (identifier) @function.name) @function.def

        (function_declaration
            name: (identifier) @function.name
            body: (code_block) @function.body) @function.def
    """,
    "classes": """
        (class_declaration
            name: (type_identifier) @class.name) @class.def

        (class_declaration
            name: (type_identifier) @class.name
            body: (class_body) @class.body) @class.def
    """,
    "structs": """
        (struct_declaration
            name: (type_identifier) @struct.name) @struct.def

        (struct_declaration
            name: (type_identifier) @struct.name
            body: (struct_body) @struct.body) @struct.def
    """,
    "imports": """
        (import_declaration) @import

        (import_declaration
            path: (identifier) @import.path) @import.simple

        (import_declaration
            path: (_) @import.path) @import.complex
    """,
    "protocols": """
        (protocol_declaration
            name: (type_identifier) @protocol.name) @protocol.def

        (protocol_declaration
            name: (type_identifier) @protocol.name
            body: (protocol_body) @protocol.body) @protocol.def
    """,
    "extensions": """
        (extension_declaration
            name: (type_identifier) @extension.name) @extension.def

        (extension_declaration
            name: (type_identifier) @extension.name
            body: (extension_body) @extension.body) @extension.def
    """,
}
