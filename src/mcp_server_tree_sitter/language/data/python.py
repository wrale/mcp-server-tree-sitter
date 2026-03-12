"""Python language data."""

from typing import Any, Dict

from ...utils.tree_sitter_helpers import get_node_text, run_query_captures
from ..import_enrichers import (
    node_location,
    register_dependency_module_enricher,
    register_symbol_import_enricher,
)
from ..schema import LanguageDataBase


def _enrich_symbol_imports(
    symbols: Dict[str, list],
    safe_lang: Any,  # noqa: ANN401 (tree-sitter Language)
    tree: Any,  # noqa: ANN401 (tree-sitter Tree)
    source_bytes: bytes,
) -> None:
    """Add aliased import entries to symbols['imports'] (e.g. from X import Y as Z)."""
    aliased_query = """
    (import_from_statement
        module_name: (dotted_name) @import.from
        name: (aliased_import)) @import
    """
    for capture_name, nodes in run_query_captures(safe_lang, aliased_query, tree.root_node).items():
        for node in nodes:
            if capture_name == "import.from":
                symbols["imports"].append(
                    {
                        "name": get_node_text(node, source_bytes),
                        "type": "imports",
                        "location": node_location(node),
                    }
                )
    alias_query = "(aliased_import) @alias"
    for capture_name, nodes in run_query_captures(safe_lang, alias_query, tree.root_node).items():
        for node in nodes:
            if capture_name != "alias":
                continue
            _raw = get_node_text(node, source_bytes)
            alias_text = _raw.decode("utf-8") if isinstance(_raw, bytes) else _raw
            module_name = ""
            if node.parent and node.parent.parent:
                for child in node.parent.parent.children:
                    if getattr(child, "type", None) == "dotted_name":
                        _mod = get_node_text(child, source_bytes)
                        module_name = _mod.decode("utf-8") if isinstance(_mod, bytes) else _mod
                        break
            symbols["imports"].append({"name": alias_text, "type": "imports", "location": node_location(node)})
            if module_name:
                loc = node_location(node)
                mod_loc = {"start": {"row": loc["start"]["row"], "column": 0}, "end": dict(loc["end"])}
                symbols["imports"].append({"name": module_name, "type": "imports", "location": mod_loc})


def _enrich_dependency_modules(
    module_imports: set[str],
    safe_lang: Any,  # noqa: ANN401 (tree-sitter Language)
    tree: Any,  # noqa: ANN401 (tree-sitter Tree)
    source_bytes: bytes,
) -> None:
    """Add module names from aliased imports to module_imports (e.g. from X import Y as Z)."""
    aliased_query = "(aliased_import) @alias"
    for _cap, nodes in run_query_captures(safe_lang, aliased_query, tree.root_node).items():
        for aliased_node in nodes:
            if aliased_node.parent and aliased_node.parent.parent:
                for child in aliased_node.parent.parent.children:
                    if getattr(child, "type", None) == "dotted_name":
                        mn = get_node_text(child, source_bytes)
                        if mn:
                            module_imports.add(mn.decode("utf-8") if isinstance(mn, bytes) else mn)
                        break


class Python(LanguageDataBase):
    id = "python"
    extensions = ["py"]
    scope_node_types = {
        "function": ["function_definition"],
        "class": ["class_definition"],
        "module": ["module"],
    }
    query_templates = {
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

        ;; Handle aliased imports with 'as' keyword
        (import_from_statement
            module_name: (dotted_name) @import.from
            name: (aliased_import
                name: (dotted_name) @import.item
                alias: (identifier) @import.alias)) @import
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
    }
    default_symbol_types = ["functions", "classes", "imports"]
    complexity_nodes = [
        "if_statement",
        "for_statement",
        "while_statement",
        "try_statement",
    ]
    node_type_descriptions = {
        "module": "The root node of a Python file",
        "function_definition": "A function definition with name and params",
        "class_definition": "A class definition with name and body",
        "import_statement": "An import statement",
        "import_from_statement": "A from ... import ... statement",
        "assignment": "An assignment statement",
        "call": "A function call with function name and arguments",
        "identifier": "An identifier (name)",
        "string": "A string literal",
        "integer": "An integer literal",
        "float": "A floating-point literal",
        "block": "A block of code (indented statements)",
        "if_statement": "An if statement with condition and body",
        "for_statement": "A for loop with target, iterable, and body",
        "while_statement": "A while loop with condition and body",
    }


# Register import enrichers so symbol extraction and dependency discovery pick up aliased imports
register_symbol_import_enricher(Python.id, _enrich_symbol_imports)
register_dependency_module_enricher(Python.id, _enrich_dependency_modules)
