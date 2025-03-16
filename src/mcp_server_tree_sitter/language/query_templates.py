"""Query templates for common code patterns by language."""

from typing import Dict, Any, Optional

# Query templates for common code patterns by language
QUERY_TEMPLATES = {
    "python": {
        "functions": """
            (function_definition
                name: (identifier) @function.name
                parameters: (parameters) @function.params
                body: (block) @function.body) @function.def
        """,
        "classes": """
            (class_definition
                name: (identifier) @class.name
                body: (block) @class.body) @class.def
        """,
        "imports": """
            (import_statement
                name: (dotted_name) @import.module) @import
                
            (import_from_statement
                module_name: (dotted_name) @import.from
                name: (dotted_name) @import.item) @import
        """,
        "function_calls": """
            (call
                function: (identifier) @call.function
                arguments: (argument_list) @call.args) @call
        """,
        "assignments": """
            (assignment
                left: (_) @assign.target
                right: (_) @assign.value) @assign
        """,
    },
    "javascript": {
        "functions": """
            (function_declaration
                name: (identifier) @function.name
                parameters: (formal_parameters) @function.params
                body: (statement_block) @function.body) @function.def
                
            (arrow_function
                parameters: (formal_parameters) @function.params
                body: (_) @function.body) @function.def
        """,
        "classes": """
            (class_declaration
                name: (identifier) @class.name
                body: (class_body) @class.body) @class.def
        """,
        "imports": """
            (import_statement
                source: (string) @import.source
                specifier: (_) @import.specifier) @import
        """,
        "function_calls": """
            (call_expression
                function: (identifier) @call.function
                arguments: (arguments) @call.args) @call
        """,
        "assignments": """
            (variable_declarator
                name: (_) @assign.target
                value: (_) @assign.value) @assign
        """,
    },
    "typescript": {
        "functions": """
            (function_declaration
                name: (identifier) @function.name
                parameters: (formal_parameters) @function.params
                body: (statement_block) @function.body) @function.def
                
            (arrow_function
                parameters: (formal_parameters) @function.params
                body: (_) @function.body) @function.def
        """,
        "classes": """
            (class_declaration
                name: (identifier) @class.name
                body: (class_body) @class.body) @class.def
        """,
        "interfaces": """
            (interface_declaration
                name: (type_identifier) @interface.name
                body: (object_type) @interface.body) @interface.def
        """,
        "imports": """
            (import_statement
                source: (string) @import.source
                specifier: (_) @import.specifier) @import
        """,
    },
    "go": {
        "functions": """
            (function_declaration
                name: (identifier) @function.name
                parameters: (parameter_list) @function.params
                body: (block) @function.body) @function.def
        """,
        "structs": """
            (type_declaration
                (type_spec
                    name: (type_identifier) @struct.name
                    type: (struct_type) @struct.body)) @struct.def
        """,
        "imports": """
            (import_declaration
                (import_spec_list
                    (import_spec
                        path: (interpreted_string_literal) @import.path))) @import
        """,
    },
    "rust": {
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
            (use_declaration
                path: (path) @import.path) @import
        """,
    },
}


def get_query_template(language: str, template_name: str) -> Optional[str]:
    """
    Get a query template for a language.
    
    Args:
        language: Language identifier
        template_name: Template name
        
    Returns:
        Query string or None if not found
    """
    language_templates = QUERY_TEMPLATES.get(language)
    if language_templates:
        return language_templates.get(template_name)
    return None


def list_query_templates(language: str = None) -> Dict[str, Any]:
    """
    List available query templates.
    
    Args:
        language: Optional language to filter by
        
    Returns:
        Dictionary of templates by language
    """
    if language:
        return {language: QUERY_TEMPLATES.get(language, {})}
    return QUERY_TEMPLATES
