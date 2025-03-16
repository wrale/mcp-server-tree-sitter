# Critical Next Steps

This document outlines the critical refactoring steps needed to address the remaining linting issues in the MCP Tree-sitter Server project.

## Current Status

We've made significant progress in fixing linting issues throughout the codebase. All ruff checks now pass, but several mypy type checking issues remain. These issues are primarily related to:

1. Tree-sitter library imports and type handling
2. File I/O operations in the analysis tools

## Remaining Issues

### 1. Tree-sitter Type Handling

The most significant remaining issues involve the way the tree-sitter library is imported and how types are handled when the library is not available:

```
src/mcp_server_tree_sitter/cache/parser_cache.py:16: error: Cannot assign to a type
src/mcp_server_tree_sitter/cache/parser_cache.py:16: error: Incompatible types in assignment
src/mcp_server_tree_sitter/cache/parser_cache.py:18: error: Name "TSLanguage" already defined
src/mcp_server_tree_sitter/cache/parser_cache.py:21: error: Name "TSParser" already defined
src/mcp_server_tree_sitter/cache/parser_cache.py:189: error: "Parser" has no attribute "set_language"
src/mcp_server_tree_sitter/language/registry.py:21: error: Name "TSLanguage" already defined
src/mcp_server_tree_sitter/language/registry.py:24: error: Name "TSParser" already defined
```

### 2. File I/O Type Issues in Analysis Tools

```
src/mcp_server_tree_sitter/tools/analysis.py:420: error: Incompatible types in assignment
src/mcp_server_tree_sitter/tools/analysis.py:445: error: Argument 1 to "startswith" of "bytes" has incompatible type "str"
```

## Refactoring Plan

### Phase 1: Tree-sitter Library Structure Refactoring

1. Create a dedicated module for tree-sitter type handling:

```python
# src/mcp_server_tree_sitter/utils/tree_sitter_types.py
from typing import Any, Protocol, TypeVar, cast

# Define protocols for tree-sitter types
class LanguageProtocol(Protocol):
    """Protocol for Tree-sitter Language class."""
    pass

class ParserProtocol(Protocol):
    """Protocol for Tree-sitter Parser class."""
    def set_language(self, language: Any) -> None: ...

class TreeProtocol(Protocol):
    """Protocol for Tree-sitter Tree class."""
    @property
    def root_node(self) -> Any: ...

# Type variables for type safety
T = TypeVar('T')

# Try to import actual tree-sitter types
try:
    from tree_sitter import Language as _Language
    from tree_sitter import Parser as _Parser
    from tree_sitter import Tree as _Tree
    
    # Export actual types if available
    Language = _Language
    Parser = _Parser
    Tree = _Tree
    HAS_TREE_SITTER = True
except ImportError:
    # Create stub classes if tree-sitter is not available
    HAS_TREE_SITTER = False
    
    class DummyLanguage:
        """Dummy implementation when tree-sitter is not available."""
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass
    
    class DummyParser:
        """Dummy implementation when tree-sitter is not available."""
        def set_language(self, language: Any) -> None:
            pass
        
    class DummyTree:
        """Dummy implementation when tree-sitter is not available."""
        @property
        def root_node(self) -> Any:
            return None
    
    # Export dummy types for type checking
    Language = DummyLanguage
    Parser = DummyParser
    Tree = DummyTree

# Helper function to safely cast to tree-sitter types
def ensure_language(obj: Any) -> 'Language':
    """Safely cast to Language type."""
    return cast(Language, obj)

def ensure_parser(obj: Any) -> 'Parser':
    """Safely cast to Parser type."""
    return cast(Parser, obj)

def ensure_tree(obj: Any) -> 'Tree':
    """Safely cast to Tree type."""
    return cast(Tree, obj)
```

2. Update imports in affected files:

```python
# In cache/parser_cache.py and language/registry.py
from ..utils.tree_sitter_types import Language, Parser, Tree, ensure_language, ensure_parser, ensure_tree, HAS_TREE_SITTER
```

### Phase 2: File I/O Operations Refactoring

1. Create utilities for safe file operations:

```python
# src/mcp_server_tree_sitter/utils/file_io.py
from io import TextIOWrapper
from pathlib import Path
from typing import BinaryIO, List, Tuple, Union, Optional

def read_text_file(path: Union[str, Path]) -> List[str]:
    """
    Safely read a text file with proper encoding handling.
    
    Args:
        path: Path to the file
    
    Returns:
        List of lines from the file
    """
    with open(str(path), "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()

def read_binary_file(path: Union[str, Path]) -> bytes:
    """
    Safely read a binary file.
    
    Args:
        path: Path to the file
    
    Returns:
        File contents as bytes
    """
    with open(str(path), "rb") as f:
        return f.read()

def get_file_content_and_lines(path: Union[str, Path]) -> Tuple[bytes, List[str]]:
    """
    Get both binary content and text lines from a file.
    
    Args:
        path: Path to the file
    
    Returns:
        Tuple of (binary_content, text_lines)
    """
    binary_content = read_binary_file(path)
    text_lines = read_text_file(path)
    return binary_content, text_lines

def is_line_comment(line: str, comment_prefix: str) -> bool:
    """
    Check if a line is a comment.
    
    Args:
        line: The line to check
        comment_prefix: Comment prefix character(s)
    
    Returns:
        True if the line is a comment
    """
    return line.strip().startswith(comment_prefix)

def count_comment_lines(lines: List[str], comment_prefix: str) -> int:
    """
    Count comment lines in a file.
    
    Args:
        lines: List of lines to check
        comment_prefix: Comment prefix character(s)
    
    Returns:
        Number of comment lines
    """
    return sum(1 for line in lines if is_line_comment(line, comment_prefix))
```

2. Update the analysis tools to use these utilities.

### Phase 3: Fix Tree-sitter API Issues

Create proper wrappers around tree-sitter API to avoid type issues:

```python
# src/mcp_server_tree_sitter/utils/tree_sitter_helpers.py
from typing import Any, Dict, List, Optional, Tuple

from .tree_sitter_types import Language, Parser, Tree, ensure_language, ensure_parser, ensure_tree

def create_parser(language_obj: Any) -> Parser:
    """
    Create a parser configured for a specific language.
    
    Args:
        language_obj: Language object
    
    Returns:
        Configured Parser
    """
    parser = Parser()
    safe_language = ensure_language(language_obj)
    parser.set_language(safe_language)
    return parser

def parse_source(parser: Parser, source: bytes) -> Tree:
    """
    Parse source code using a configured parser.
    
    Args:
        parser: Configured Parser object
        source: Source code as bytes
    
    Returns:
        Parsed Tree
    """
    safe_parser = ensure_parser(parser)
    tree = safe_parser.parse(source)
    return ensure_tree(tree)
```

## Priority Order

1. **HIGH**: Create tree-sitter types utility module
2. **HIGH**: Update cache/parser_cache.py to use the new typing utilities
3. **HIGH**: Update language/registry.py to use the new typing utilities
4. **MEDIUM**: Create file I/O utilities
5. **MEDIUM**: Fix analysis.py file operations
6. **MEDIUM**: Create tree-sitter API helper functions
7. **LOW**: Apply comprehensive testing of the refactored components

## Potential Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking tree-sitter functionality | High | Create thorough tests for each refactored component before and after changes |
| Introducing new type errors | Medium | Test with mypy after each phase of the refactoring |
| Performance degradation from additional wrappers | Low | Perform benchmark tests before and after changes |

## Conclusion

The remaining linting issues require a structured approach to refactoring that addresses the core design patterns for handling external dependencies and type safety. By following this plan, we can create a more maintainable and type-safe codebase without compromising functionality.

Once these changes are implemented, we should achieve 100% compliance with both ruff and mypy linting standards, resulting in a more robust and maintainable codebase.
