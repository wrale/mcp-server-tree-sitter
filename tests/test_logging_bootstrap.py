"""Tests for the logging bootstrap module."""

import importlib
import logging

import pytest


def test_bootstrap_imported_first():
    """Test that bootstrap is imported in __init__.py before anything else."""
    # Get the content of __init__.py
    import inspect

    import mcp_server_tree_sitter

    init_source = inspect.getsource(mcp_server_tree_sitter)

    # Check that bootstrap is imported before any other modules
    bootstrap_import_index = init_source.find("from . import bootstrap")
    assert bootstrap_import_index > 0, "bootstrap should be imported in __init__.py"

    # Check that bootstrap is imported before any other significant imports
    other_imports = [
        "from . import config",
        "from . import server",
        "from . import context",
    ]

    for other_import in other_imports:
        other_import_index = init_source.find(other_import)
        if other_import_index > 0:
            assert bootstrap_import_index < other_import_index, f"bootstrap should be imported before {other_import}"


def test_logging_config_forwards_to_bootstrap():
    """Test that logging_config.py forwards to bootstrap.logging_bootstrap."""
    # Import both modules
    from mcp_server_tree_sitter import logging_config
    from mcp_server_tree_sitter.bootstrap import logging_bootstrap

    # Verify that key functions are the same objects
    assert logging_config.get_logger is logging_bootstrap.get_logger
    assert logging_config.update_log_levels is logging_bootstrap.update_log_levels
    assert logging_config.get_log_level_from_env is logging_bootstrap.get_log_level_from_env
    assert logging_config.configure_root_logger is logging_bootstrap.configure_root_logger
    assert logging_config.LOG_LEVEL_MAP is logging_bootstrap.LOG_LEVEL_MAP


def test_key_modules_use_bootstrap():
    """Test that key modules import logging utilities from bootstrap."""
    # Import key modules
    modules_to_check = [
        "mcp_server_tree_sitter.server",
        "mcp_server_tree_sitter.config",
        "mcp_server_tree_sitter.context",
        "mcp_server_tree_sitter.di",
        "mcp_server_tree_sitter.__main__",
    ]

    # Import bootstrap for comparison

    # Check each module
    for module_name in modules_to_check:
        try:
            # Import the module
            module = importlib.import_module(module_name)

            # Check if the module has a logger attribute
            if hasattr(module, "logger"):
                # Check where the logger comes from by examining the code
                import inspect

                source = inspect.getsource(module)

                # Look for bootstrap import pattern
                bootstrap_import = "from .bootstrap import get_logger" in source
                legacy_import = "from .logging_config import get_logger" in source

                # If module uses logging_config, it should be forwarding to bootstrap
                assert bootstrap_import or not legacy_import, f"{module_name} should import get_logger from bootstrap"

        except (ImportError, AttributeError) as e:
            pytest.skip(f"Couldn't check {module_name}: {e}")


def test_log_level_update_consistency():
    """Test that all log level updates use bootstrap's implementation."""
    # Create test loggers and handlers
    root_logger = logging.getLogger("mcp_server_tree_sitter")
    original_level = root_logger.level

    child_logger = logging.getLogger("mcp_server_tree_sitter.test_logging_bootstrap")
    child_handler = logging.StreamHandler()
    child_handler.setLevel(logging.WARNING)
    child_logger.addHandler(child_handler)

    try:
        # Import and use bootstrap's update_log_levels
        from mcp_server_tree_sitter.bootstrap import update_log_levels

        # Set a known state before testing
        root_logger.setLevel(logging.INFO)
        child_logger.setLevel(logging.NOTSET)

        # Apply the update
        update_log_levels("DEBUG")

        # Verify effects on root logger
        assert root_logger.level == logging.DEBUG, "Root logger level should be updated"

        # Verify effects on child logger
        assert child_logger.level == logging.NOTSET, "Child logger level should not be changed"
        assert child_logger.getEffectiveLevel() == logging.DEBUG, "Child logger should inherit level from root"

        # Explicitly synchronize the handler level by calling update_log_levels again
        update_log_levels("DEBUG")

        # Now check the handler level
        assert child_handler.level == logging.DEBUG, "Handler level should be synchronized"

    finally:
        # Clean up
        root_logger.setLevel(original_level)
        child_logger.removeHandler(child_handler)


def test_no_duplicate_log_level_implementations():
    """Test that only the bootstrap implementation of update_log_levels exists."""
    # Import bootstrap's update_log_levels for reference
    from mcp_server_tree_sitter.bootstrap.logging_bootstrap import update_log_levels as bootstrap_update

    # Import the re-exported function from logging_config
    from mcp_server_tree_sitter.logging_config import update_log_levels as config_update

    # Verify the re-exported function is the same object as the original
    assert config_update is bootstrap_update, "logging_config should re-export the same function object"

    # Get the module from context
    # We test the identity of the imported function rather than checking source code
    # which is more brittle
    from mcp_server_tree_sitter.context import update_log_levels as context_update

    # If context.py properly imports from bootstrap or logging_config,
    # all three should be the same object
    assert context_update is bootstrap_update, "context should import update_log_levels from bootstrap"
