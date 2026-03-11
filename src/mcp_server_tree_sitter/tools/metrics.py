"""Code metrics computation (lines, comments, cyclomatic complexity)."""

from typing import Any, Dict, List

from ..language.loader import get_language_data
from ..utils.file_io import get_comment_prefix
from ..utils.tree_sitter_helpers import ensure_node
from ..utils.tree_sitter_types import Node, Tree


def count_lines_and_comments(lines: List[str], language: str) -> Dict[str, Any]:
    """
    Count lines, empty lines, and comment lines for a file.

    Args:
        lines: List of lines (e.g. from read_text_file).
        language: Language identifier for comment detection.

    Returns:
        Dict with line_count, empty_lines, comment_lines, code_lines, comment_ratio.
    """
    line_count = len(lines)
    empty_lines = sum(1 for line in lines if line.strip() == "")
    comment_lines = 0

    comment_prefix = get_comment_prefix(language)
    if comment_prefix:
        comment_lines = sum(1 for line in lines if line.strip().startswith(comment_prefix))

    code_lines = line_count - empty_lines - comment_lines
    comment_ratio = comment_lines / line_count if line_count > 0 else 0

    return {
        "line_count": line_count,
        "empty_lines": empty_lines,
        "comment_lines": comment_lines,
        "code_lines": code_lines,
        "comment_ratio": comment_ratio,
    }


def compute_cyclomatic_complexity(tree: Tree, language: str) -> int:
    """
    Compute cyclomatic complexity from the syntax tree by counting decision points.
    Decision node types come from language data (complexity_nodes).

    Args:
        tree: Parsed tree-sitter tree.
        language: Language identifier.

    Returns:
        Cyclomatic complexity (base 1 + decision points).
    """
    complexity = 1  # Base complexity

    lang_data = get_language_data(language)
    decision_types = list(lang_data.complexity_nodes) if lang_data else []
    if not decision_types:
        return complexity

    def count_nodes(node: Node, types: List[str]) -> int:
        safe_node = ensure_node(node)
        count = 0
        if safe_node.type in types:
            count += 1
        for child in safe_node.children:
            count += count_nodes(child, types)
        return count

    complexity += count_nodes(tree.root_node, decision_types)
    return complexity
