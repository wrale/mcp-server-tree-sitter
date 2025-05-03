# Makefile for mcp-server-tree-sitter
# Uses uv as the package manager

# Package information
PACKAGE := mcp_server_tree_sitter
PACKAGE_PATH := src/$(PACKAGE)

# Environment variables
PYTHONPATH ?= $(shell pwd)/src
export PYTHONPATH

# Installation method (uv or uvx)
INSTALL_METHOD ?= uv

# uv commands
UV := uv

# Default target
.PHONY: all help
help: show-help

all: install

# Installation targets
.PHONY: install
install:
	$(UV) pip install -e .

.PHONY: install-dev
install-dev:
	$(UV) pip install -e ".[dev]"

.PHONY: install-all
install-all:
	$(UV) pip install -e ".[dev]"

.PHONY: install-global
install-global:
	python -m pip install -e ".[dev]"

# Pre-commit preparation
.PHONY: prepare
prepare: clean format lint test-ci ensure-diagnostic-dir verify

# CI-like test target that better simulates CI environment
.PHONY: test-ci
test-ci:
	# Use CI=true to help tests detect when they're in a CI-like environment
	CI=true $(MAKE) test-with-args
	CI=true $(UV) run pytest tests/test_diagnostics/ -v

# Testing targets
.PHONY: test
test:
	# Regular test target
	$(UV) run pytest

# Run tests with explicit cli args to catch arg parsing conflicts
.PHONY: test-with-args
test-with-args:
	$(UV) run pytest tests -- tests

.PHONY: test-diagnostics
test-diagnostics: ensure-diagnostic-dir
	$(UV) run pytest tests/test_diagnostics/ -v

.PHONY: test-diagnostics-ci
test-diagnostics-ci: ensure-diagnostic-dir
	$(UV) run pytest tests/test_diagnostics/ -v || echo "Diagnostic tests completed with issues - see diagnostic_results directory"

.PHONY: test-coverage
test-coverage:
	$(UV) run pytest --cov=$(PACKAGE) --cov-report=term --cov-report=html

# Matrix testing support
.PHONY: test-matrix
test-matrix:
	@echo "Running tests with $(INSTALL_METHOD) installation method"
ifeq ($(INSTALL_METHOD),uv)
	$(MAKE) install-dev
	$(MAKE) test-all
else ifeq ($(INSTALL_METHOD),uvx)
	$(MAKE) install-global
	$(MAKE) test-all
else
	@echo "Unknown installation method: $(INSTALL_METHOD)"
	@echo "Supported methods: uv, uvx"
	@exit 1
endif

# Unified test target
.PHONY: test-all
test-all: test test-diagnostics

# Verification targets
.PHONY: verify
verify: build verify-wheel

.PHONY: verify-wheel
verify-wheel:
	@echo "Verifying the built wheel..."
	@echo "Creating temporary virtual environment for verification..."
	rm -rf .verify_venv 2>/dev/null || true
	$(shell command -v python3 || command -v python) -m venv .verify_venv
	.verify_venv/bin/pip install dist/*.whl
	.verify_venv/bin/mcp-server-tree-sitter --help || true
	rm -rf .verify_venv

.PHONY: verify-global
verify-global: build
	@echo "Verifying global installation..."
	@echo "Creating temporary virtual environment for verification..."
	rm -rf .verify_venv 2>/dev/null || true
	$(shell command -v python3 || command -v python) -m venv .verify_venv
	.verify_venv/bin/pip install dist/*.whl
	.verify_venv/bin/mcp-server-tree-sitter --help || true
	rm -rf .verify_venv

# Linting and formatting targets
.PHONY: lint
lint:
	$(UV) run mypy .
	$(UV) run ruff check .

.PHONY: mypy
mypy:
	$(UV) run mypy .

.PHONY: format
format:
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

# Cleaning targets
.PHONY: clean
clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage .ruff_cache diagnostic_results .verify_venv
	# Use rmdir with -p to handle non-empty directories more gracefully
	find .mypy_cache -type d -exec rmdir -p {} \; 2>/dev/null || true
	rm -rf .mypy_cache 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -f tests/issue_tests/*.json 2>/dev/null || true
	rm -f tests/issue_tests/results/*.json 2>/dev/null || true

# Diagnostic directory handling
.PHONY: ensure-diagnostic-dir
ensure-diagnostic-dir:
	@mkdir -p diagnostic_results
	@if [ -z "$$(ls -A diagnostic_results 2>/dev/null)" ]; then \
		echo '{"info": "No diagnostic results generated"}' > diagnostic_results/placeholder.json; \
	fi

# Building and packaging
.PHONY: build
build:
	$(UV) run python -m build

# Release targets
.PHONY: pre-release
pre-release: clean lint test-all build verify

.PHONY: release-local
release-local: pre-release
	@echo "Local release process completed. Run 'make publish' to publish to PyPI."
	@echo "NOTE: Publishing to PyPI requires proper credentials and should be done via CI."

.PHONY: publish
publish:
	@echo "This target would publish to PyPI, but is intended to be run via CI."
	@echo "For manual publishing, use: python -m twine upload dist/*"

# CI integration
.PHONY: ci
ci: clean install-dev lint test-all build verify

# Run the server
# ARGS can be passed like: make run ARGS="--help"
.PHONY: run
run:
	$(UV) run python -m $(PACKAGE) $(ARGS)

# MCP specific targets
# ARGS can be passed like: make mcp-dev ARGS="--help"
.PHONY: mcp-dev
mcp-dev:
	$(UV) run mcp dev $(PACKAGE).server $(ARGS)

.PHONY: mcp-run
mcp-run:
	$(UV) run mcp run $(PACKAGE).server $(ARGS)

.PHONY: mcp-install
mcp-install:
	$(UV) run mcp install $(PACKAGE).server:mcp --name "tree_sitter" $(ARGS)

# Help target
.PHONY: show-help
show-help:
	@echo "Available targets:"
	@echo "  help                  : Show this help message (default target)"
	@echo "  all                   : Install the package"
	@echo "  install               : Install the package"
	@echo "  install-dev           : Install the package with development dependencies"
	@echo "  install-all           : Install with all dependencies"
	@echo "  install-global        : Install the package globally (system-wide)"
	@echo "  prepare               : Run pre-commit checks (format, lint, test, verify)"
	@echo "  test                  : Run normal tests"
	@echo "  test-with-args         : Run tests with extra arguments to catch CLI parsing issues"
	@echo "  test-ci                : Run tests in a CI-like environment (catches more issues)"
	@echo "  test-diagnostics      : Run pytest-based diagnostic tests"
	@echo "  test-diagnostics-ci   : Run diagnostic tests in CI mode (won't fail the build)"
	@echo "  test-coverage         : Run tests with coverage report"
	@echo "  test-matrix           : Run tests with different installation methods (set INSTALL_METHOD=uv|uvx)"
	@echo "  test-all              : Run both normal tests and diagnostic tests"
	@echo "  verify                : Verify the built package works correctly"
	@echo "  verify-wheel          : Verify the built wheel by installing and running a basic check"
	@echo "  verify-global         : Verify global installation (similar to CI verify-uvx job)"
	@echo "  clean                 : Clean build artifacts and test results"
	@echo "  ensure-diagnostic-dir : Create diagnostic results directory if it doesn't exist"
	@echo "  lint                  : Run linting checks"
	@echo "  format                : Format code using ruff"
	@echo "  build                 : Build distribution packages"
	@echo "  pre-release           : Run all pre-release checks (clean, lint, test, build, verify)"
	@echo "  release-local         : Perform a complete local release process"
	@echo "  publish               : Placeholder for publishing to PyPI (intended for CI use)"
	@echo "  ci                    : Run the CI workflow steps locally"
	@echo "  run                   : Run the server directly (use ARGS=\"--help\" to pass arguments)"
	@echo "  mcp-dev               : Run the server with MCP Inspector (use ARGS=\"--help\" to pass arguments)"
	@echo "  mcp-run               : Run the server with MCP (use ARGS=\"--help\" to pass arguments)"
	@echo "  mcp-install           : Install the server in Claude Desktop"
