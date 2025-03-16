# Contributing to MCP Tree-sitter Server

Thank you for your interest in contributing to MCP Tree-sitter Server! This guide will help you understand our development process and coding standards.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/organization/mcp-server-tree-sitter.git
   cd mcp-server-tree-sitter
   ```

2. Install with development dependencies:
   ```bash
   make install-dev
   ```

3. Install language parsers (optional):
   ```bash
   make install-languages
   ```

## Code Style and Standards

We follow a strict set of coding standards to maintain consistency throughout the codebase:

### Python Style

- We use [Black](https://black.readthedocs.io/) for code formatting with a line length of 88 characters
- We use [Ruff](https://github.com/charliermarsh/ruff) for linting
- We use [MyPy](https://mypy.readthedocs.io/) for static type checking

### Exception Handling

- Use specific exception types rather than catching generic exceptions when possible
- When re-raising exceptions, use the `from` clause to preserve the stack trace:
  ```python
  try:
      # Some code
  except SomeError as e:
      raise CustomError("Meaningful message") from e
  ```

### Testing

- Write tests for all new functionality
- Run tests before submitting:
  ```bash
  make test
  ```

### Documentation

- Document all functions, classes, and modules using docstrings
- Follow the Google Python Style Guide for docstrings
- Include type hints for all function parameters and return values

## Development Workflow

1. Create a branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure they pass linting and tests:
   ```bash
   make format
   make lint
   make test
   ```

3. Commit your changes with a clear message describing the change

4. Submit a pull request to the main repository

## Running the Server

You can run the server in different modes:

- For development and testing:
  ```bash
  make mcp-dev
  ```

- For direct execution:
  ```bash
  make mcp-run
  ```

- To install in Claude Desktop:
  ```bash
  make mcp-install
  ```

## Project Architecture

The project follows a modular architecture:

- `config.py` - Configuration management
- `language/` - Tree-sitter language handling
- `models/` - Data models for AST and projects
- `cache/` - Caching mechanisms
- `resources/` - MCP resources (files, AST)
- `tools/` - MCP tools (search, analysis, etc.)
- `utils/` - Utility functions
- `prompts/` - MCP prompts
- `server.py` - FastMCP server implementation

## Seeking Help

If you have questions or need help, please open an issue or contact the maintainers.
