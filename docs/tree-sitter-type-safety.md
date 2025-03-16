# Tree-sitter Type Safety Guide

This document explains our approach to type safety when interfacing with the tree-sitter library and why certain type-checking suppressions are necessary.

## Background

The MCP Tree-sitter Server maintains type safety through Python's type hints and mypy verification. However, when interfacing with external libraries like tree-sitter, we encounter challenges:

1. Tree-sitter's Python bindings have inconsistent API signatures across versions
2. Tree-sitter objects don't always match our protocol definitions
3. The library may work at runtime but fail static type checking

## Type Suppression Strategy

We use targeted `# type: ignore` comments to handle specific scenarios where mypy can't verify correctness, but our runtime code handles the variations properly.

### Examples of Necessary Type Suppressions

#### Parser Interface Variations

Some versions of tree-sitter use `set_language()` while others use `language` as the attribute/method:

```python
try:
    parser.set_language(safe_language)  # type: ignore
except AttributeError:
    if hasattr(parser, 'language'):
        # Use the language method if available
        parser.language = safe_language  # type: ignore
    else:
        # Fallback to setting the attribute directly
        parser.language = safe_language  # type: ignore
```

#### Node Handling Safety

For cursor navigation and tree traversal, we need to handle potential `None` values:

```python
def visit(node: Optional[Node], field_name: Optional[str], depth: int) -> bool:
    if node is None:
        return False
    # Continue with node operations...
```

## Guidelines for Using Type Suppressions

1. **Be specific**: Always use `# type: ignore` on the exact line with the issue, not for entire blocks or files
2. **Add comments**: Explain why the suppression is necessary
3. **Try alternatives first**: Only use suppressions after trying to fix the actual type issue
4. **Include runtime checks**: Always pair suppressions with runtime checks (try/except, if hasattr, etc.)

## Our Pattern for Library Compatibility

We follow a consistent pattern for tree-sitter API compatibility:

1. **Define Protocols**: Use Protocol classes to define expected interfaces
2. **Safe Type Casting**: Use wrapper functions like `ensure_node()` to safely cast objects
3. **Feature Detection**: Use `hasattr()` checks before accessing attributes
4. **Fallback Mechanisms**: Provide multiple ways to accomplish the same task
5. **Graceful Degradation**: Handle missing features by providing simplified alternatives

## Testing Approach

Even with type suppressions, we ensure correctness through:

1. Comprehensive test coverage for different tree-sitter operations
2. Tests with and without tree-sitter installed to verify fallback mechanisms
3. Runtime verification of object capabilities before operations

## When to Update Type Suppressions

Review and potentially remove type suppressions when:

1. Upgrading minimum supported tree-sitter version
2. Refactoring the interface to the tree-sitter library
3. Adding new wrapper functions that can handle type variations
4. Improving Protocol definitions to better match runtime behavior

By following these guidelines, we maintain a balance between static type safety and runtime flexibility when working with the tree-sitter library.
