"""Query templates for Go."""

TEMPLATES = {
    "functions": """
        (function_declaration
            name: (identifier) @function.name
            parameters: (parameter_list) @function.params
            body: (block) @function.body) @function.def

        (method_declaration
            name: (field_identifier) @method.name
            parameters: (parameter_list) @method.params
            body: (block) @method.body) @method.def
    """,
    "structs": """
        (type_declaration
            (type_spec
                name: (type_identifier) @struct.name
                type: (struct_type) @struct.body)) @struct.def

        (type_declaration
            (type_spec
                name: (type_identifier) @type.name
                type: (_) @type.body)) @type.def
    """,
    "imports": """
        (import_declaration) @import

        (import_declaration
            (import_spec_list
                (import_spec) @import.spec)) @import.list

        (import_declaration
            (import_spec_list
                (import_spec
                    path: (_) @import.path))) @import.path_list

        (import_declaration
            (import_spec
                path: (_) @import.path)) @import.single
    """,
    "interfaces": """
        (type_declaration
            (type_spec
                name: (type_identifier) @interface.name
                type: (interface_type) @interface.body)) @interface.def
    """,
}
