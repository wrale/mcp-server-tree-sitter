"""Query templates for Dart language."""

TEMPLATES = {
    "functions": """
        (program
            (function_signature
                name: (identifier) @function.name) @function.def)
    """,
    "classes": """
        (class_definition
            name: (identifier) @class.name) @class.def

        (class_definition
            name: (identifier) @class.name
            body: (class_body) @class.body) @class.def
    """,
    "imports": """
        (import_or_export
            (library_import
                (import_specification) @import.spec)) @import

        (import_or_export
            (library_export) @export) @export.stmt

        (part_directive) @part

        (part_of_directive) @part_of
    """,
    "enums": """
        (enum_declaration
            name: (identifier) @enum.name) @enum.def

        (enum_declaration
            name: (identifier) @enum.name
            body: (enum_body) @enum.body) @enum.def
    """,
    "mixins": """
        (mixin_declaration
            (identifier) @mixin.name) @mixin.def

        (mixin_declaration
            (identifier) @mixin.name
            (class_body) @mixin.body) @mixin.def
    """,
    "extensions": """
        (extension_declaration
            (identifier) @extension.name) @extension.def

        (extension_declaration
            (identifier) @extension.name
            body: (extension_body) @extension.body) @extension.def
    """,
    "typedefs": """
        (type_alias
            . (type_identifier) @typedef.name) @typedef.def
    """,
}
