"""Type handling utilities for tree-sitter.

This module provides type definitions and safety wrappers for
the tree-sitter library to ensure type safety with or without
the library installed.

Any is not used; types are expressed via Protocol and type aliases.
Where tree-sitter's C binding would force untyped APIs (e.g. Query),
we use minimal Protocols (e.g. QueryProtocol) so call sites stay typed.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

# Define protocols for tree-sitter types (order: Query, Language, Tree, Node, Cursor for refs)


class QueryProtocol(Protocol):
    """Protocol for tree-sitter Query (C binding; no typed Python API). Return type of Language.query()."""

    pass


class LanguageProtocol(Protocol):
    """Protocol for Tree-sitter Language class."""

    def query(self, query_string: str) -> QueryProtocol: ...


class ParserProtocol(Protocol):
    """Protocol for Tree-sitter Parser class."""

    def set_language(self, language: LanguageProtocol) -> None: ...
    def language(self, language: LanguageProtocol) -> None: ...  # Alternative name for set_language
    def parse(self, bytes_input: bytes) -> "TreeProtocol": ...


class TreeProtocol(Protocol):
    """Protocol for Tree-sitter Tree class."""

    @property
    def root_node(self) -> "NodeProtocol": ...


class NodeProtocol(Protocol):
    """Protocol for Tree-sitter Node class."""

    @property
    def children(self) -> list["NodeProtocol"]: ...
    @property
    def named_children(self) -> list["NodeProtocol"]: ...
    @property
    def child_count(self) -> int: ...
    @property
    def named_child_count(self) -> int: ...
    @property
    def start_point(self) -> tuple[int, int]: ...
    @property
    def end_point(self) -> tuple[int, int]: ...
    @property
    def start_byte(self) -> int: ...
    @property
    def end_byte(self) -> int: ...
    @property
    def type(self) -> str: ...
    @property
    def is_named(self) -> bool: ...
    @property
    def parent(self) -> "NodeProtocol" | None: ...
    @property
    def children_by_field_name(self) -> dict[str, list["NodeProtocol"]]: ...

    def walk(self) -> "CursorProtocol": ...


class CursorProtocol(Protocol):
    """Protocol for Tree-sitter Cursor class (TreeCursor)."""

    @property
    def node(self) -> "NodeProtocol": ...

    def goto_first_child(self) -> bool: ...
    def goto_next_sibling(self) -> bool: ...
    def goto_parent(self) -> bool: ...


# Type variables for type safety
T = TypeVar("T")

# Try to import actual tree-sitter types
try:
    from tree_sitter import Language as _Language
    from tree_sitter import Node as _Node
    from tree_sitter import Parser as _Parser
    from tree_sitter import Tree as _Tree
    from tree_sitter import TreeCursor as _TreeCursor

    # Export actual types if available
    Language = _Language
    Parser = _Parser
    Tree = _Tree
    Node = _Node
    TreeCursor = _TreeCursor
    HAS_TREE_SITTER = True
except ImportError:
    # Create stub classes if tree-sitter is not available
    HAS_TREE_SITTER = False

    class DummyQuery:
        """Dummy Query when tree-sitter is not available (satisfies QueryProtocol)."""

        pass

    class DummyLanguage:
        """Dummy implementation when tree-sitter is not available."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def query(self, query_string: str) -> QueryProtocol:
            """Dummy query method."""
            return DummyQuery()

    class DummyParser:
        """Dummy implementation when tree-sitter is not available."""

        def set_language(self, language: LanguageProtocol) -> None:
            """Dummy set_language method."""
            pass

        def language(self, language: LanguageProtocol) -> None:
            """Dummy language method (alternative to set_language)."""
            pass

        def parse(self, bytes_input: bytes) -> "DummyTree":
            """Dummy parse method."""
            return DummyTree()

    class DummyNode:
        """Dummy implementation when tree-sitter is not available."""

        @property
        def children(self) -> list["DummyNode"]:
            return []

        @property
        def named_children(self) -> list["DummyNode"]:
            return []

        @property
        def child_count(self) -> int:
            return 0

        @property
        def named_child_count(self) -> int:
            return 0

        @property
        def start_point(self) -> tuple[int, int]:
            return (0, 0)

        @property
        def end_point(self) -> tuple[int, int]:
            return (0, 0)

        @property
        def start_byte(self) -> int:
            return 0

        @property
        def end_byte(self) -> int:
            return 0

        @property
        def type(self) -> str:
            return ""

        @property
        def is_named(self) -> bool:
            return False

        @property
        def parent(self) -> "DummyNode" | None:
            return None

        @property
        def children_by_field_name(self) -> dict[str, list["DummyNode"]]:
            return {}

        def walk(self) -> "DummyTreeCursor":
            return DummyTreeCursor()

    class DummyTreeCursor:
        """Dummy implementation when tree-sitter is not available."""

        @property
        def node(self) -> DummyNode:
            return DummyNode()

        def goto_first_child(self) -> bool:
            return False

        def goto_next_sibling(self) -> bool:
            return False

        def goto_parent(self) -> bool:
            return False

    class DummyTree:
        """Dummy implementation when tree-sitter is not available."""

        @property
        def root_node(self) -> DummyNode:
            return DummyNode()

    # Export dummy types for type checking (conditional assignment)
    Language = DummyLanguage
    Parser = DummyParser
    Tree = DummyTree
    Node = DummyNode
    TreeCursor = DummyTreeCursor


# Helper functions: take object and narrow via isinstance (no Any; inputs are from our API or C).
def ensure_language(obj: object) -> "Language":
    """Safely cast to Language type."""
    if not isinstance(obj, Language):
        raise TypeError(f"Expected Language type, got {type(obj).__name__}")
    return obj


def ensure_parser(obj: object) -> "Parser":
    """Safely cast to Parser type."""
    if not isinstance(obj, Parser):
        raise TypeError(f"Expected Parser type, got {type(obj).__name__}")
    return obj


def ensure_tree(obj: object) -> "Tree":
    """Safely cast to Tree type."""
    if not isinstance(obj, Tree):
        raise TypeError(f"Expected Tree type, got {type(obj).__name__}")
    return obj


def ensure_node(obj: object) -> "Node":
    """Safely cast to Node type."""
    if not isinstance(obj, Node):
        raise TypeError(f"Expected Node type, got {type(obj).__name__}")
    return obj


def ensure_cursor(obj: object) -> "TreeCursor":
    """Safely cast to TreeCursor type."""
    if not isinstance(obj, TreeCursor):
        raise TypeError(f"Expected TreeCursor type, got {type(obj).__name__}")
    return obj
