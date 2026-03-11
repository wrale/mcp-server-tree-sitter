"""JavaScript language data."""

from ..schema import LanguageDataBase


class JavaScript(LanguageDataBase):
    id = "javascript"
    extensions = ["js", "jsx"]
    scope_node_types = {
        "function": ["function_declaration", "method_definition"],
        "class": ["class_declaration"],
        "module": ["program"],
    }
    query_templates = {
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
            source: (string) @import.source) @import
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
    }
    default_symbol_types = ["functions", "classes", "imports"]
    complexity_nodes = [
        "if_statement",
        "for_statement",
        "while_statement",
        "try_statement",
    ]
    node_type_descriptions = {
        "program": "The root node of a JavaScript file",
        "function_declaration": "A function declaration with name and params",
        "arrow_function": "An arrow function with parameters and body",
        "class_declaration": "A class declaration with name and body",
        "import_statement": "An import statement",
        "export_statement": "An export statement",
        "variable_declaration": "A variable declaration",
        "call_expression": "A function call with function and arguments",
        "identifier": "An identifier (name)",
        "string": "A string literal",
        "number": "A numeric literal",
        "statement_block": "A block of statements",
        "if_statement": "An if statement with condition and consequence",
        "for_statement": "A for loop",
        "while_statement": "A while loop with condition and body",
    }
