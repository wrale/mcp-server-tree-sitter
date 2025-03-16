# Makefile for mcp-server-tree-sitter
# Uses uv as the package manager

# Package information
PACKAGE := mcp_server_tree_sitter
PACKAGE_PATH := src/$(PACKAGE)

# uv commands
UV := uv

# Default target
.PHONY: all
all: install

# Installation targets
.PHONY: install
install:
	$(UV) pip install -e .

.PHONY: install-dev
install-dev:
	$(UV) pip install -e ".[dev]"

.PHONY: install-languages
install-languages:
	$(UV) pip install -e ".[languages]"

.PHONY: install-all
install-all:
	$(UV) pip install -e ".[dev,languages]"

# Testing targets
.PHONY: test
test:
	$(UV) run pytest

.PHONY: test-coverage
test-coverage:
	$(UV) run pytest --cov=$(PACKAGE) --cov-report=term --cov-report=html

# Linting and formatting targets
.PHONY: lint
lint:
	$(UV) run ruff check $(PACKAGE_PATH) tests/
	$(UV) run mypy $(PACKAGE_PATH)

.PHONY: format
format:
	$(UV) run black $(PACKAGE_PATH) tests/
	$(UV) run ruff check --fix $(PACKAGE_PATH) tests/

# Cleaning targets
.PHONY: clean
clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

# Building and packaging
.PHONY: build
build:
	$(UV) run python -m build

# Run the server
.PHONY: run
run:
	$(UV) run python -m $(PACKAGE)

# MCP specific targets
.PHONY: mcp-dev
mcp-dev:
	$(UV) run mcp dev $(PACKAGE).server

.PHONY: mcp-run
mcp-run:
	$(UV) run mcp run $(PACKAGE).server

.PHONY: mcp-install
mcp-install:
	$(UV) run mcp install $(PACKAGE).server:mcp --name "tree_sitter"

# Example targets
.PHONY: run-example-basic
run-example-basic:
	$(UV) run python examples/basic_usage.py $(PROJECT_PATH)

.PHONY: run-example-query
run-example-query:
	$(UV) run python examples/query_explorer.py $(PROJECT_PATH) --language $(LANGUAGE)

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all                   : Default target, install the package"
	@echo "  install               : Install the package"
	@echo "  install-dev           : Install the package with development dependencies"
	@echo "  install-languages     : Install language parsers"
	@echo "  install-all           : Install with development dependencies and language parsers"
	@echo "  test                  : Run tests"
	@echo "  test-coverage         : Run tests with coverage report"
	@echo "  lint                  : Run linting checks"
	@echo "  format                : Format code"
	@echo "  clean                 : Clean build artifacts"
	@echo "  build                 : Build distribution packages"
	@echo "  run                   : Run the server directly"
	@echo "  mcp-dev               : Run the server with MCP Inspector"
	@echo "  mcp-run               : Run the server with MCP"
	@echo "  mcp-install           : Install the server in Claude Desktop"
	@echo "  run-example-basic     : Run the basic usage example (set PROJECT_PATH=/path/to/project)"
	@echo "  run-example-query     : Run the query explorer example (set PROJECT_PATH and LANGUAGE)"
	@echo "  help                  : Show this help message"
