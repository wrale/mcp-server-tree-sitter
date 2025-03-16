"""Common prompt templates for code analysis."""

from typing import Dict, List, Optional

# Language-specific common patterns
LANGUAGE_PATTERNS = {
    "python": {
        "docstring": """
        Docstrings should follow PEP 257 conventions:
        - Use triple double quotes (''')
        - First line should be a summary of the function/class
        - Add a blank line after the summary for detailed descriptions
        - Document parameters using Args: section
        - Document return values using Returns: section
        - Document exceptions using Raises: section

        Example:
        ```python
        def example_function(param1, param2):
            \"\"\"Summary of what the function does.

            More detailed description of the function behavior, edge cases,
            algorithm details, etc.

            Args:
                param1: Description of param1
                param2: Description of param2

            Returns:
                Description of return value

            Raises:
                ValueError: When an invalid parameter is passed
            \"\"\"
            pass
        ```
        """,
        "imports": """
        Import conventions in Python:
        1. Standard library imports first
        2. Related third-party imports
        3. Local application/library specific imports
        4. Separate each group with a blank line
        5. Use absolute imports when possible
        6. Sort imports alphabetically within each group

        Example:
        ```python
        import os
        import sys

        import numpy as np
        import pandas as pd

        from myproject.utils import helper
        from . import local_module
        ```
        """,
        "error_handling": """
        Error handling best practices in Python:
        1. Be specific about the exceptions you catch
        2. Use context managers (with statements) for resource management
        3. Create custom exceptions for application-specific errors
        4. Provide helpful error messages
        5. Avoid bare except clauses

        Example:
        ```python
        try:
            with open(filename, 'r') as f:
                data = f.read()
        except FileNotFoundError:
            logger.error(f"File {filename} not found")
            raise CustomFileError(f"Could not find {filename}")
        except IOError as e:
            logger.error(f"IO error reading {filename}: {e}")
            raise CustomFileError(f"Failed to read {filename}")
        ```
        """,
    },
    "javascript": {
        "commenting": """
        Commenting best practices in JavaScript:
        1. Use JSDoc for documenting functions, classes, and modules
        2. Add inline comments for complex logic
        3. Keep comments up-to-date with code changes

        Example:
        ```javascript
        /**
         * Calculates the total price including tax
         *
         * @param {number} price - The base price
         * @param {number} taxRate - The tax rate as a decimal (e.g., 0.07 for 7%)
         * @returns {number} The total price including tax
         */
        function calculateTotal(price, taxRate) {
          // Round to 2 decimal places
          return Math.round((price * (1 + taxRate)) * 100) / 100;
        }
        ```
        """,
        "error_handling": """
        Error handling best practices in JavaScript:
        1. Use try/catch blocks for synchronous code
        2. Use promises or async/await for asynchronous error handling
        3. Create custom error classes by extending Error
        4. Always include helpful error messages

        Example:
        ```javascript
        // Async/await error handling
        async function fetchUserData(userId) {
          try {
            const response = await fetch(`/api/users/${userId}`);
            if (!response.ok) {
              throw new APIError(`Failed to fetch user: ${response.statusText}`);
            }
            return await response.json();
          } catch (error) {
            console.error(`Error fetching user ${userId}:`, error);
            throw error;
          }
        }

        // Custom error class
        class APIError extends Error {
          constructor(message) {
            super(message);
            this.name = 'APIError';
          }
        }
        ```
        """,
    },
    "typescript": {
        "type_definitions": """
        TypeScript type definition best practices:
        1. Prefer interfaces for object shapes that will be implemented
        2. Use type aliases for unions, intersections, and complex types
        3. Make properties readonly when they shouldn't change
        4. Use strict null checking
        5. Provide descriptive names for types

        Example:
        ```typescript
        // Interface for objects with implementation
        interface User {
          readonly id: number;
          name: string;
          email: string;
          settings?: UserSettings;
        }

        // Type alias for union
        type Status = 'pending' | 'active' | 'inactive';

        // Function with type annotations
        function processUser(user: User, status: Status): boolean {
          // Implementation
          return true;
        }
        ```
        """,
    },
    "go": {
        "error_handling": """
        Error handling best practices in Go:
        1. Return errors rather than using exceptions
        2. Check errors immediately after function calls
        3. Use the errors package for simple errors
        4. Use fmt.Errorf for formatting error messages
        5. Create custom error types for complex cases

        Example:
        ```go
        import (
            "errors"
            "fmt"
        )

        // Simple error
        var ErrNotFound = errors.New("item not found")

        // Function returning an error
        func FindItem(id string) (Item, error) {
            item, ok := storage[id]
            if !ok {
                return Item{}, ErrNotFound
            }
            return item, nil
        }

        // Error checking
        item, err := FindItem("123")
        if err != nil {
            if errors.Is(err, ErrNotFound) {
                // Handle not found case
            } else {
                // Handle other errors
            }
            return
        }
        ```
        """,
    },
}

# Generic code review patterns
REVIEW_PATTERNS = {
    "performance": """
    Performance considerations:
    1. Avoid unnecessary computations inside loops
    2. Be mindful of memory allocations
    3. Check for O(n²) algorithms that could be O(n) or O(log n)
    4. Cache expensive results that will be reused
    5. Prefer early returns to reduce nesting and improve performance
    6. Be cautious with recursion to avoid stack overflow
    7. Use appropriate data structures for operations (e.g., sets for lookups)
    """,
    "security": """
    Security considerations:
    1. Validate all user inputs
    2. Avoid string concatenation for SQL queries (use parameterized queries)
    3. Sanitize outputs to prevent XSS attacks
    4. Use secure functions for cryptographic operations
    5. Don't hardcode sensitive information like passwords or API keys
    6. Implement proper authentication and authorization
    7. Be careful with file path handling to prevent path traversal
    8. Check for OWASP Top 10 vulnerabilities
    """,
    "maintainability": """
    Maintainability considerations:
    1. Follow consistent naming conventions
    2. Keep functions and methods small and focused
    3. Limit function parameters (consider objects/structs for many parameters)
    4. Use meaningful variable and function names
    5. Add appropriate comments and documentation
    6. Follow the DRY (Don't Repeat Yourself) principle
    7. Use appropriate design patterns
    8. Follow SOLID principles
    9. Add tests for key functionality
    """,
    "error_handling": """
    Error handling considerations:
    1. Handle all possible error cases
    2. Provide meaningful error messages
    3. Use appropriate error handling mechanisms for the language
    4. Log errors with contextual information
    5. Avoid swallowing exceptions without handling them
    6. Return useful error information to callers
    7. Consider error recovery strategies
    """,
}


def get_language_pattern(language: str, pattern_name: str) -> str:
    """Get a language-specific pattern."""
    language_patterns = LANGUAGE_PATTERNS.get(language, {})
    return language_patterns.get(pattern_name, "No pattern found")


def get_review_pattern(pattern_name: str) -> str:
    """Get a generic code review pattern."""
    return REVIEW_PATTERNS.get(pattern_name, "No pattern found")


def get_available_patterns(language: Optional[str] = None) -> Dict[str, List[str]]:
    """Get available patterns."""
    if language:
        return {
            "language_patterns": list(LANGUAGE_PATTERNS.get(language, {}).keys()),
            "review_patterns": list(REVIEW_PATTERNS.keys()),
        }

    return {
        "languages": list(LANGUAGE_PATTERNS.keys()),
        "review_patterns": list(REVIEW_PATTERNS.keys()),
    }
