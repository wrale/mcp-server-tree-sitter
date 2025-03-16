"""Type handling utilities for tree-sitter.

This module provides type definitions and safety wrappers for
the tree-sitter library to ensure type safety with or without
the library installed.
"""

from typing import Any, Protocol, TypeVar, cast


# Define protocols for tree-sitter types
class LanguageProtocol(Protocol):
    """Protocol for Tree-sitter Language class."""

    def query(self, query_string: str) -> Any: ...


class ParserProtocol(Protocol):
    """Protocol for Tree-sitter Parser class."""

    def set_language(self, language: Any) -> None: ...
    def language(self, language: Any) -> None: ...  # Alternative name for set_language
    def parse(self, bytes_input: bytes) -> Any: ...


class TreeProtocol(Protocol):
    """Protocol for Tree-sitter Tree class."""

    @property
    def root_node(self) -> Any: ...


class NodeProtocol(Protocol):
    """Protocol for Tree-sitter Node class."""

    @property
    def children(self) -> list[Any]: ...
    @property
    def named_children(self) -> list[Any]: ...
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
    def parent(self) -> Any: ...
    @property
    def children_by_field_name(self) -> dict[str, list[Any]]: ...

    def walk(self) -> Any: ...


class CursorProtocol(Protocol):
    """Protocol for Tree-sitter Cursor class."""

    @property
    def node(self) -> Any: ...

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

    class DummyLanguage:
        """Dummy implementation when tree-sitter is not available."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def query(self, query_string: str) -> Any:
            """Dummy query method."""
            return None

    class DummyParser:
        """Dummy implementation when tree-sitter is not available."""

        def set_language(self, language: Any) -> None:
            """Dummy set_language method."""
            pass

        def language(self, language: Any) -> None:
            """Dummy language method (alternative to set_language)."""
            pass

        def parse(self, bytes_input: bytes) -> Any:
            """Dummy parse method."""
            return None

    class DummyNode:
        """Dummy implementation when tree-sitter is not available."""

        @property
        def children(self) -> list[Any]:
            return []

        @property
        def named_children(self) -> list[Any]:
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
        def parent(self) -> Any:
            return None

        @property
        def children_by_field_name(self) -> dict[str, list[Any]]:
            return {}

        def walk(self) -> Any:
            return DummyTreeCursor()

    class DummyTreeCursor:
        """Dummy implementation when tree-sitter is not available."""

        @property
        def node(self) -> Any:
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
        def root_node(self) -> Any:
            return DummyNode()

    # Export dummy types for type checking
    # Declare dummy types for when tree-sitter is not available
    Language = DummyLanguage  # type: ignore
    Parser = DummyParser  # type: ignore
    Tree = DummyTree  # type: ignore
    Node = DummyNode  # type: ignore
    TreeCursor = DummyTreeCursor  # type: ignore


# Helper function to safely cast to tree-sitter types
def ensure_language(obj: Any) -> "Language":
    """Safely cast to Language type."""
    return cast(Language, obj)


def ensure_parser(obj: Any) -> "Parser":
    """Safely cast to Parser type."""
    return cast(Parser, obj)


def ensure_tree(obj: Any) -> "Tree":
    """Safely cast to Tree type."""
    return cast(Tree, obj)


def ensure_node(obj: Any) -> "Node":
    """Safely cast to Node type."""
    return cast(Node, obj)


def ensure_cursor(obj: Any) -> "TreeCursor":
    """Safely cast to TreeCursor type."""
    return cast(TreeCursor, obj)
