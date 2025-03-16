# MCP Tree-sitter Server Diagnostics

This document describes the diagnostic testing approach for the MCP Tree-sitter Server project.

## Overview

The diagnostics suite consists of targeted pytest tests that isolate and document specific issues in the codebase. These tests are designed to:

1. Document current behavior with proper pass/fail results
2. Isolate failure points to specific functions or modules
3. Provide detailed error information and stack traces
4. Create a foundation for developing targeted fixes

The diagnostic framework combines standard pytest behavior with enhanced diagnostic capabilities:
- Tests properly pass or fail based on assertions
- Comprehensive diagnostic data is captured for debugging
- Diagnostic information is saved to JSON for further analysis

## Running Diagnostics

The Makefile includes several targets for running diagnostics:

```bash
# Run all diagnostic tests
make test-diagnostics

# CI-friendly version (won't fail the build on diagnostic issues)
make test-diagnostics-ci
```

For running diagnostics alongside regular tests:

```bash
# Run both regular tests and diagnostics
make test-all
```

## Using the Diagnostic Framework

### Basic Test Structure

```python
import pytest
from mcp_server_tree_sitter.testing import diagnostic

@pytest.mark.diagnostic  # Mark the test as producing diagnostic data
def test_some_feature(diagnostic):  # Use the diagnostic fixture
    # Add details to diagnostic data
    diagnostic.add_detail("key", "value")
    
    try:
        # Test your functionality
        result = some_functionality()
        
        # Use standard assertions - the test will fail if they don't pass
        assert result is not None, "Result should not be None"
        
    except Exception as e:
        # Record the error in diagnostic data
        diagnostic.add_error("ErrorType", str(e))
        
        # Add any artifacts you want to save
        diagnostic.add_artifact("error_artifact", {"error": str(e)})
        
        # Re-raise to fail the test
        raise
```

### Diagnostic Operations

The `diagnostic` fixture provides several methods:

- `add_detail(key, value)`: Add a key-value pair to diagnostic details
- `add_error(error_type, message, traceback=None)`: Add an error
- `add_artifact(name, content)`: Add an artifact (e.g., JSON data)
- `finalize(status="completed")`: Mark the diagnostic as complete

## Key Issues Identified

Based on initial testing, several core issues have been identified:

### 1. Language Registry Issues
- `list_languages()` returns empty lists despite languages being available
- Language detection through `install_language()` works, but languages don't appear in available lists

### 2. AST Parsing Failures
- `get_ast()` fails with errors when attempting to build the tree
- Core AST parsing functionality appears non-operational

### 3. "Too Many Values to Unpack" Errors
- Several analysis functions fail with "too many values to unpack (expected 2)"
- Affects `get_symbols()`, `get_dependencies()`, and `analyze_complexity()`
- Likely related to query captures handling

### 4. Tree-sitter Language Pack Integration
- Basic language detection works, but integration with tree-sitter queries may be incomplete
- Language pack integration appears partially complete but with core functionality issues

## Diagnostic Results

The diagnostic tests generate detailed JSON result files in the `diagnostic_results` directory with timestamps. These files contain valuable information for debugging:

- Error messages and stack traces
- Current behavior documentation
- Environment and configuration details
- Detailed information about tree-sitter integration

In addition, the test output includes a diagnostic summary:
```
============================== Diagnostic Summary ==============================
Collected 4 diagnostics, 2 with errors
-------------------------------- Error Details ---------------------------------
- /path/to/test.py::test_function
  Error 1: ErrorType: Error message
```

## Recommended Debugging Approach

1. Run the diagnostic tests to verify current issues
   ```
   make test-diagnostics
   ```

2. Examine the diagnostic results in the terminal output and the `diagnostic_results` directory

3. Review specific error patterns to identify the root cause:
   - For unpacking errors, check the query capture processing code
   - For AST parsing, examine the tree-sitter integration layer
   - For language registry issues, check the initialization sequence

4. Make targeted fixes to address specific issues, using the diagnostic tests to verify repairs

5. After fixes, run both diagnostics and regular tests to ensure no regressions
   ```
   make test-all
   ```

## Issue Priority

Based on dependencies between components, the recommended fix priority is:

1. **Language Registry Issues** - Fix language listing to enable proper language detection
2. **AST Parsing** - Fix core parsing functionality which many other features depend on
3. **Query Handling** - Address unpacking errors in query captures to enable analysis tools
4. **Incremental Improvements** - After core functionality works, implement additional features

## Integrating with Development Workflow

Diagnostics should be run:
- After any significant changes to core tree-sitter integration code
- Before submitting pull requests that touch language or AST handling
- When investigating specific failures in higher-level functionality
- As part of debugging for issues reported by users

## Continuous Integration

For CI environments, the diagnostic tests have special considerations:

### CI-Friendly Targets

The Makefile includes CI-friendly targets that won't fail the build due to known issues:

- `make test-diagnostics-ci`: Runs diagnostics but always returns success

### CI Setup Recommendations

1. **Primary CI Pipeline**: Use `make test` for regression testing of working functionality
   ```yaml
   test:
     script:
       - make test
   ```

2. **Diagnostic Job**: Add a separate, optional job for diagnostics
   ```yaml
   diagnostics:
     script:
       - make test-diagnostics-ci
     artifacts:
       paths:
         - diagnostic_results/
     allow_failure: true
   ```

## Benefits of the Pytest-based Approach

The pytest-based diagnostic framework offers significant advantages:

1. **Unified framework**: All tests use pytest with consistent behavior
2. **Clear pass/fail**: Tests fail when they should, making issues obvious
3. **Rich diagnostics**: Detailed diagnostic information is still collected
4. **Standard integration**: Works with pytest's fixtures, plugins, and reporting

## Future Improvements

In the future, we plan to:

1. Enhance the diagnostic plugin with more features
2. Integrate with CI/CD pipelines for better reporting
3. Add automatic visualization of diagnostic data
4. Improve the organization of diagnostic tests
