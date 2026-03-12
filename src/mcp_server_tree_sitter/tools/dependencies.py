"""Dependency discovery (imports/includes) from source files."""

from collections import defaultdict

from ..exceptions import SecurityError
from ..language.import_enrichers import get_dependency_module_enricher
from ..language.query_templates import get_query_template
from ..language.registry import LanguageRegistry
from ..models.project import Project
from ..utils.security import validate_file_access
from ..utils.tree_sitter_helpers import (
    ensure_language,
    ensure_node,
    get_node_text,
    parse_with_cached_tree,
    run_query_captures,
)
from ..utils.tree_sitter_types import Node


def find_dependencies(
    project: Project,
    file_path: str,
    language_registry: LanguageRegistry,
) -> dict[str, list[str]]:
    """
    Find dependencies of a file.

    Args:
        project: Project object
        file_path: Path to the file relative to project root
        language_registry: Language registry object

    Returns:
        Dictionary of dependencies (imports, includes, etc.)
    """
    abs_path = project.get_file_path(file_path)

    try:
        validate_file_access(abs_path, project.root_path)
    except SecurityError as e:
        raise SecurityError(f"Access denied: {e}") from e

    language = language_registry.language_for_file(file_path)
    if not language:
        raise ValueError(f"Could not detect language for {file_path}")

    query_string = get_query_template(language, "imports")
    if not query_string:
        raise ValueError(f"Import query not available for {language}")

    try:
        language_obj = language_registry.get_language(language)
        safe_lang = ensure_language(language_obj)

        tree, source_bytes = parse_with_cached_tree(abs_path, language, safe_lang)

        matches = run_query_captures(safe_lang, query_string, tree.root_node)

        imports: dict[str, list[str]] = defaultdict(list)
        module_imports: set[str] = set()

        def process_import_node(node: Node, capture_name: str) -> None:
            try:
                safe_node = ensure_node(node)
                text = get_node_text(safe_node, source_bytes)

                category = capture_name.split(".", 1)[1] if capture_name.startswith("import.") else "import"

                text_str = text.decode("utf-8") if isinstance(text, bytes) else text
                imports[category].append(text_str)

                if category == "from":
                    parts = text_str.split()
                    if parts:
                        module_imports.add(parts[0].strip())
                elif category == "module":
                    module_imports.add(text_str.strip())
                elif category == "item" and text and getattr(safe_node, "parent", None):
                    parent = safe_node.parent
                    if parent is not None:
                        for child in parent.children:
                            if getattr(child, "type", None) == "dotted_name" and child != safe_node:
                                mn = get_node_text(child, source_bytes)
                                module_imports.add(mn.decode("utf-8") if isinstance(mn, bytes) else mn)
                                break
                elif "import" in text_str:
                    parts = text_str.split()
                    if len(parts) > 1 and parts[0] == "from":
                        module_imports.add(str(parts[1].strip()))
                    elif "from" in text_str and "import" in text_str:
                        from_parts = text_str.split("from", 1)[1].split("import", 1)
                        if from_parts:
                            module_imports.add(from_parts[0].strip())
                    elif parts and parts[0] == "import":
                        for module in " ".join(parts[1:]).split(","):
                            module_imports.add(module.strip().split(" as ")[0].strip())
            except Exception:
                pass

        if isinstance(matches, dict):
            for capture_name, nodes in matches.items():
                for node in nodes:
                    process_import_node(node, capture_name)
        else:
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    node, capture_name = match
                elif hasattr(match, "node") and hasattr(match, "capture_name"):
                    node, capture_name = match.node, match.capture_name
                elif isinstance(match, dict) and "node" in match and "capture" in match:
                    node, capture_name = match["node"], match["capture"]
                else:
                    continue
                process_import_node(node, capture_name)

        if module_imports:
            imports["module"] = list(set(imports.get("module", []) + list(module_imports)))

        enricher = get_dependency_module_enricher(language)
        if enricher:
            enricher(module_imports, safe_lang, tree, source_bytes)
            if module_imports:
                imports["module"] = list(set(imports.get("module", []) + list(module_imports)))

        return dict(imports)

    except Exception as e:
        raise ValueError(f"Error finding dependencies in {file_path}: {e}") from e
