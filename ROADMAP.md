# MCP Tree-sitter Server Roadmap

This document outlines the planned improvements and future features for the MCP Tree-sitter Server project.

CRITICAL: When a task is done, update this document to mark it done. However, you must ensure it is done for all files/subjects present in the repo. DO NOT mark a task done simply because a subset of the targeted files/subjects have been handled. Mark it [WIP] in that case.

## Short-term Goals

### Code Quality
- ✅ Fix linting issues identified by ruff
- ✅ Improve exception handling using proper `from` clause
- ✅ Remove unused variables and improve code organization
- ✅ Implement TreeCursor API support with proper type handling
- ✅ Add incremental parsing support
- ✅ Add MCP Progress Reporting
- ✅ Add Server Capabilities Declaration
- [ ] Add mcp server start flag(s) for enabling (allow list approach) and disabling (block list approach) a list of features. Only one approach may be applied at a time. The default should be minimal allowed, for now. Add meta features such as stable, wip, advanced, basic
- ✅ Add mcp server start flag(s) for ensuring language packs are installed - Resolved by tree-sitter-language-pack integration
- [ ] Add mcp server start flag(s) for ensuring project is configured beforehand.
- [ ] Achieve 100% type hinting coverage (and ensure this is enforced by our linting)
- [ ] Improve docstring coverage and quality (Don't thrash on updating docs that are already good) (HOLD pending other work)
- [ ] Split files until the longest .py file is less than 500 lines (unless that breaks functionality, in which case do not)

### Testing
- ✅ Create and maintain tests for AST functionality, query execution, and symbol extraction
- 🔄 [WIP] Create additional tests for context utilities, incremental parsing, and cursor traversal
- [ ] Increase unit test coverage to 100% and begin enforcing that in pre-commit and CI
- [ ] Add integration tests for MCP server functionality (HOLD pending other work)
- [ ] Create automated testing workflow with GitHub Actions (unit, integration, static, etc) (HOLD pending other work)

### Documentation (HOLD)
- ✅ Create CONTRIBUTING.md with developer guidelines
- 🔄 [WIP] Create a docs/user-guide.md with more examples and clearer installation instructions. Link to it from README.md
- [ ] Add detailed API documentation in docs/api-guide.md
- 🔄 [WIP] Create usage tutorials and examples -- focus only on Claude Desktop for now.

## Medium-term Goals (HOLD)

### Feature Improvements
- ✅ Add support for more tree-sitter languages by implementing https://github.com/Goldziher/tree-sitter-language-pack/
- ✅ Add support for query execution with proper result handling
- [ ] Improve query building tools with more sophisticated matching options (HOLD because we could cripple the codebase with complexity)
- [ ] Implement more advanced code analysis metrics (HOLD because we could cripple the codebase with complexity)
- [ ] Enhance caching system with better invalidation strategy (HOLD because we could cripple the codebase with complexity)

### User Experience
- [ ] Create a web-based UI for visualizing ASTs and running queries (HOLD because Claude's experience is more important)
- [ ] Add CLI commands for common operations (HOLD because Claude runs commands by a different channel)
- [✅] Implement progress reporting for long-running operations
- [ ] Add configuration presets for different use cases (HOLD because we could cripple the codebase with complexity)

### Security
- [ ] Add comprehensive input validation (HOLD because we could cripple the codebase with complexity)
- [ ] Implement access control for multi-user environments (HOLD because we could cripple the codebase with complexity)
- [ ] Add sandbox mode for running untrusted queries (HOLD because we could cripple the codebase with complexity)

## Long-term Goals (HOLD)

### Advanced Features
- [ ] Implement semantic analysis capabilities (HOLD because we need stability first)
- [ ] Add code transformation tools (HOLD because we need stability first)
- [ ] Support cross-language analysis (HOLD because we need stability first)

### Integration
- [ ] Create plugins for popular IDEs (VS Code, IntelliJ) (HOLD because we need stability first)
- [ ] Implement integration with CI/CD pipelines (HOLD because we need stability first)
- [ ] Add support for other LLM frameworks beyond MCP (HOLD because we need stability first)

### Performance
- [ ] Optimize for large codebases (> 1M LOC) (HOLD because we need stability first)
- [ ] Implement distributed analysis for very large projects (HOLD because we need stability first)
- [ ] Add streaming responses for large result sets (HOLD because we need stability first)

## Completed Implementations

### MCP Context Handling
- Added `utils/context/mcp_context.py` with progress tracking capabilities
- Implemented `MCPContext` class with progress reporting
- Created `ProgressScope` for structured operation tracking
- Added context information passing to analysis tools

### TreeCursor API Support
- Enhanced `utils/tree_sitter_types.py` with TreeCursor protocol
- Added efficient cursor-based tree traversal in `utils/tree_sitter_helpers.py`
- Implemented collector pattern using cursors to efficiently find nodes

### Incremental Parsing
- Added support for tree editing in `utils/tree_sitter_helpers.py`
- Enhanced cache to track tree modifications in `cache/parser_cache.py`
- Implemented changed_ranges detection for optimization

### Server Capabilities Declaration
- Created `capabilities/server_capabilities.py` for capability declaration
- Implemented required MCP server capabilities
- Added support for completion suggestions
- Added structured logging integration

## Features and Ideas

Below are some ideas and feature requests being considered:

1. **Semantic Diff**: Show semantic differences between code versions rather than just text diffs (HOLD because we need stability first)
2. **Code Quality Metrics**: Integrate with code quality metrics and linters (HOLD because we need stability first)
3. **Interactive Query Builder**: Visual tool to build and test tree-sitter queries (HOLD because we need stability first)
4. **Code Completion**: Use tree-sitter for more intelligent code completion suggestions (HOLD because we need stability first)
5. **Visualization Export**: Export AST visualizations to various formats (SVG, PNG, etc.) (HOLD because we need stability first)
