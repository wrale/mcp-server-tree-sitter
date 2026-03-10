"""Rust language data."""

from ..schema import LanguageDataBase


class Rust(LanguageDataBase):
    id = "rust"
    extensions = ["rs"]
    scope_node_types = {
        "function": ["function_item"],
        "class": ["struct_item", "impl_item", "trait_item"],
        "module": ["source_file"],
    }
    query_templates = {
        "functions": """
        (function_item
            name: (identifier) @function.name
            parameters: (parameters) @function.params
            body: (block) @function.body) @function.def
    """,
        "structs": """
        (struct_item
            name: (type_identifier) @struct.name
            body: (field_declaration_list) @struct.body) @struct.def
    """,
        "enums": """
        (enum_item
            name: (type_identifier) @enum.name
            body: (enum_variant_list) @enum.body) @enum.def
    """,
        "imports": """
        (use_declaration) @import

        (use_declaration
            (identifier) @import.name) @import.direct

        (use_declaration
            (scoped_identifier
                path: (_) @import.path
                name: (identifier) @import.name)) @import.scoped

        (use_declaration
            (scoped_use_list
                path: (_) @import.path)) @import.list
    """,
        "traits": """
        (trait_item
            name: (type_identifier) @trait.name) @trait.def
    """,
        "impls": """
        (impl_item
            trait: (_)? @impl.trait
            type: (_) @impl.type) @impl.def
    """,
    }
    node_type_descriptions = {}
