# Critical Next Steps

This document outlines the critical refactoring steps needed to address the remaining linting issues in the MCP Tree-sitter Server project.

## Current Status

We've made significant progress in fixing linting issues and implementing key features. The following work has been completed:

1. ✅ Created a dedicated tree-sitter type handling module (`utils/tree_sitter_types.py`)
2. ✅ Updated `cache/parser_cache.py` to use the new typing utilities
3. ✅ Updated `language/registry.py` to use the new typing utilities
4. ✅ Created file I/O utilities (`utils/file_io.py`)
5. ✅ Fixed analysis.py file operations
6. ✅ Created tree-sitter API helper functions (`utils/tree_sitter_helpers.py`)
7. ✅ Added TreeCursor protocol to `utils/tree_sitter_types.py`
8. ✅ Created cursor helper functions in `utils/tree_sitter_helpers.py`
9. ✅ Extended `cache/parser_cache.py` to track tree modification state
10. ✅ Implemented tree editing methods in `utils/tree_sitter_helpers.py`
11. ✅ Added support for changed_ranges detection
12. ✅ Created a context utility module (`utils/context/mcp_context.py`)
13. ✅ Added progress reporting infrastructure to long-running operations
14. ✅ Implemented context-aware methods for tools
15. ✅ Created `capabilities/server_capabilities.py` for capability declaration
16. ✅ Added resource subscription support
17. ✅ Added completion suggestions support

## Immediate Next Steps

The following tasks need to be addressed immediately:

1. 🔄 **Fix Type-checking Issues**
   - Run comprehensive type checking to verify all issues are resolved:
     ```bash
     make lint
     ```
   - Fix tree-sitter protocol type issues in helpers and parsers
   - Fix node type handling in cursor traversal
   - Fix type annotations for query captures in analysis tools

2. 🔄 **Update AST Traversal**
   - Update `models/ast.py` to use cursor-based tree traversal for efficiency
   - Apply the same type-safe patterns to other parts of the codebase that interact with tree-sitter or file I/O

3. 🔄 **Implement Testing**
   - Implement additional test cases for the new utilities to ensure they work correctly
   - Add tests for context utilities
   - Test incremental parsing with various code changes
   - Create test cases for tree cursor traversal

4. 🔄 **Enhance Claude Desktop Integration**
   - Complete environment variable handling
   - Enhance integration with Claude UX

Once these items are completed, CRITICAL-NEXT-STEPS.md can be deprecated.

## Implementation Details

### Tree-sitter Type Handling

The new tree-sitter types module provides:

- Protocol definitions for tree-sitter types (Language, Parser, Tree, etc.)
- Safe type casting functions to ensure type safety
- Dummy classes for type checking when tree-sitter is not available
- Import detection to handle cases with or without tree-sitter installed

### TreeCursor API Implementation

The TreeCursor API provides more efficient tree traversal:
- Efficient navigation through node children and siblings
- Reduced memory overhead compared to recursive traversal
- Better performance for large ASTs
- Field name access for structured navigation
- Collector pattern for gathering nodes matching criteria
- Type-safe cursor handling with proper protocol definitions

Example usage:

```python
def find_nodes_by_type(root_node: Node, node_type: str) -> List[Node]:
    def collector(node: Node, _field_name: Optional[str], _depth: int) -> Optional[Node]:
        if node.type == node_type:
            return node
        return None
    
    return collect_with_cursor(root_node, collector)
```

### Incremental Parsing

Incremental parsing support provides:
- Tree editing methods for efficient updates
- Cache tracking of modified trees
- Optimized re-parsing of changed tree sections
- Fallback to full parsing when needed
- Type-safe tree manipulation

### MCP Context Handling

Context handling provides:
- Progress reporting for long-running operations
- Context management with scoped progress tracking
- Integration with MCP's built-in progress reporting
- Fallback logging when MCP context is not available
- Structured messaging (info, warning, error)

Example usage:

```python
def analyze_project_structure(project_name: str, scan_depth: int = 3, mcp_ctx: Optional[Any] = None) -> Dict[str, Any]:
    # Create context for progress reporting
    ctx = MCPContext(mcp_ctx)
    
    with ctx.progress_scope(100, "Analyzing project structure") as progress:
        # Update language information (5%)
        project.scan_files(language_registry)
        progress.update(5)
        
        # More work...
        progress.update(15)
```

### File I/O Utilities

The file I/O utilities provide:

- Safe file reading functions with proper encoding handling
- Functions for reading both binary and text content
- Helper functions for working with file contents (e.g., counting comment lines)
- Language-specific utilities (e.g., getting comment prefixes)

### Tree-sitter API Helpers

The tree-sitter helpers module provides:

- Functions for safely creating and using parsers
- Functions for parsing files with caching
- Utilities for working with nodes and node text
- Tree traversal utilities

### Server Capabilities

The server capabilities implementation provides:
- Explicit capability declarations for MCP server
- Support for prompt and resource management events
- Contextual completion suggestions
- Structured logging integration

## Remaining Issues

Some mypy type checking issues remain to be fixed, primarily around tree-sitter API type handling:

1. Tree-sitter protocol type issues in helpers and parsers:
   ```
   src/mcp_server_tree_sitter/cache/parser_cache.py:265: error: "Parser" has no attribute "set_language"
   src/mcp_server_tree_sitter/utils/tree_sitter_helpers.py:40: error: "Parser" has no attribute "set_language"
   ```

2. Node type handling in cursor traversal:
   ```
   src/mcp_server_tree_sitter/utils/tree_sitter_helpers.py:227: error: Argument 1 has incompatible type "Node | None"
   src/mcp_server_tree_sitter/utils/tree_sitter_helpers.py:236: error: Item "None" of "Node | None" has no attribute "parent"
   ```

3. Type annotations for query captures in analysis tools:
   ```
   src/mcp_server_tree_sitter/tools/analysis.py:85: error: Unpacking a string is disallowed
   src/mcp_server_tree_sitter/tools/analysis.py:88: error: Cannot determine type of "capture_name"
   ```

## Conclusion

These changes create a more maintainable and type-safe codebase without compromising functionality. The modular approach allows for easier extension and testing of core functionality.

Once these immediate next steps are completed, we can move on to the additional feature improvements outlined in the ROADMAP.md document.
