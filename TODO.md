# MCP Tree-sitter Server: TODO Board

This Kanban board tracks tasks specifically focused on improving partially working commands and implementing missing features.

## In Progress

### High Priority
---

#### Fix Similar Code Detection
- **Description**: Improve the `find_similar_code` command to reliably return results
- **Tasks**:
  - [ ] Debug why command completes but doesn't return results
  - [ ] Optimize similarity threshold and matching algorithm
  - [ ] Add more detailed logging for troubleshooting
  - [ ] Create comprehensive test cases with expected results
- **Acceptance Criteria**:
  - Command reliably returns similar code snippets when they exist
  - Appropriate feedback when no similar code is found
  - Documentation updated with examples and recommended thresholds
- **Complexity**: Medium
- **Dependencies**: None

#### Complete Tree Editing and Incremental Parsing
- **Description**: Extend AST functionality to support tree manipulation
- **Tasks**:
  - [ ] Implement tree editing operations (insert, delete, replace nodes)
  - [ ] Add incremental parsing to efficiently update trees after edits
  - [ ] Ensure node IDs remain consistent during tree manipulations
- **Acceptance Criteria**:
  - Trees can be modified through API calls
  - Incremental parsing reduces parse time for small changes
  - Proper error handling for invalid modifications
- **Complexity**: High
- **Dependencies**: None

### Medium Priority
---

#### Implement UTF-16 Support
- **Description**: Add encoding detection and support for UTF-16
- **Tasks**:
  - [ ] Implement encoding detection for input files
  - [ ] Add UTF-16 to UTF-8 conversion for parser compatibility
  - [ ] Handle position mapping between different encodings
- **Acceptance Criteria**:
  - Correctly parse and handle UTF-16 encoded files
  - Maintain accurate position information in different encodings
  - Test suite includes UTF-16 encoded files
- **Complexity**: Medium
- **Dependencies**: None

#### Add Read Callable Support
- **Description**: Implement custom read strategies for efficient large file handling
- **Tasks**:
  - [ ] Create streaming parser interface for large files
  - [ ] Implement memory-efficient parsing strategy
  - [ ] Add support for custom read handlers
- **Acceptance Criteria**:
  - Successfully parse files larger than memory constraints
  - Performance tests show acceptable parsing speed
  - Documentation on how to use custom read strategies
- **Complexity**: High
- **Dependencies**: None

## Ready for Review

### High Priority
---

#### Complete MCP Context Progress Reporting
- **Description**: Implement progress reporting for long-running operations
- **Tasks**:
  - [ ] Add progress tracking to all long-running operations
  - [ ] Implement progress callbacks in the MCP context
  - [ ] Update API to report progress percentage
- **Acceptance Criteria**:
  - Long-running operations report progress
  - Progress is visible to the user
  - Cancellation is possible for operations in progress
- **Complexity**: Low
- **Dependencies**: None

## Done

*No tasks completed yet*

## Backlog

### Low Priority
---

#### Add Image Handling Support
- **Description**: Implement support for returning images/visualizations from tools
- **Tasks**:
  - [ ] Create image generation utilities for AST visualization
  - [ ] Add support for returning images in MCP responses
  - [ ] Implement SVG or PNG export of tree structures
- **Acceptance Criteria**:
  - Tools can return visual representations of code structures
  - AST visualizations can be generated and returned
- **Complexity**: Medium
- **Dependencies**: None

---

## Task Metadata

### Priority Levels
- **High**: Critical for core functionality, should be addressed immediately
- **Medium**: Important for comprehensive feature set, address after high priority items
- **Low**: Nice to have, address when resources permit

### Complexity Levels
- **Low**: Estimated 1-2 days of work
- **Medium**: Estimated 3-5 days of work
- **High**: Estimated 1-2 weeks of work
