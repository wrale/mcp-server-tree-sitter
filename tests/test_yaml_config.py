"""Tests for configuration loading from YAML files.

This file is being kept as an integration test but has been updated to fully use DI.
"""

import os
import tempfile

import pytest
import yaml

from mcp_server_tree_sitter.config import ServerConfig
from mcp_server_tree_sitter.di import get_container
from tests.test_helpers import configure


@pytest.fixture
def temp_yaml_file():
    """Create a temporary YAML file with test configuration."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+", delete=False) as temp_file:
        test_config = {
            "cache": {"enabled": True, "max_size_mb": 256, "ttl_seconds": 3600},
            "security": {"max_file_size_mb": 10, "excluded_dirs": [".git", "node_modules", "__pycache__", ".cache"]},
            "language": {"auto_install": True, "default_max_depth": 7},
        }
        yaml.dump(test_config, temp_file)
        temp_file.flush()
        temp_file_path = temp_file.name

    yield temp_file_path

    # Clean up the temporary file
    os.unlink(temp_file_path)


def test_server_config_from_file(temp_yaml_file):
    """Test the ServerConfig.from_file method directly."""
    # Print debug information
    print(f"Temporary YAML file created at: {temp_yaml_file}")
    with open(temp_yaml_file, "r") as f:
        print(f"File contents:\n{f.read()}")

    # Call from_file directly
    config = ServerConfig.from_file(temp_yaml_file)

    # Print the result for debugging
    print(f"ServerConfig from file: {config}")

    # Verify that the config object has the expected values
    assert config.cache.enabled is True
    assert config.cache.max_size_mb == 256
    assert config.cache.ttl_seconds == 3600
    assert config.security.max_file_size_mb == 10
    assert ".git" in config.security.excluded_dirs
    assert config.language.auto_install is True
    assert config.language.default_max_depth == 7


def test_load_config_function_di(temp_yaml_file):
    """Test the config loading with DI container."""
    # Print debug information
    print(f"Temporary YAML file created at: {temp_yaml_file}")

    # Get the container directly
    container = get_container()
    original_config = container.get_config()

    # Save original values to restore later
    original_cache_size = original_config.cache.max_size_mb
    original_security_size = original_config.security.max_file_size_mb
    original_depth = original_config.language.default_max_depth

    try:
        # Load config file using container's config manager
        container.config_manager.load_from_file(temp_yaml_file)
        config = container.get_config()

        # Verify that the config values were loaded correctly
        assert config.cache.max_size_mb == 256
        assert config.security.max_file_size_mb == 10
        assert config.language.default_max_depth == 7

    finally:
        # Restore original values
        container.config_manager.update_value("cache.max_size_mb", original_cache_size)
        container.config_manager.update_value("security.max_file_size_mb", original_security_size)
        container.config_manager.update_value("language.default_max_depth", original_depth)


def test_configure_helper(temp_yaml_file):
    """Test that the configure helper function properly loads values from a YAML file."""
    # Print debug information
    print(f"Temporary YAML file created at: {temp_yaml_file}")
    print(f"File exists: {os.path.exists(temp_yaml_file)}")

    # Get container to save original values
    container = get_container()
    original_config = container.get_config()

    # Save original values to restore later
    original_cache_size = original_config.cache.max_size_mb
    original_security_size = original_config.security.max_file_size_mb
    original_depth = original_config.language.default_max_depth

    try:
        # Call the configure helper with the path to the temp file
        result = configure(config_path=temp_yaml_file)

        # Print the result for debugging
        print(f"Configure result: {result}")

        # Verify the returned configuration matches the expected values
        # Cache settings
        assert result["cache"]["enabled"] is True
        assert result["cache"]["max_size_mb"] == 256
        assert result["cache"]["ttl_seconds"] == 3600

        # Security settings
        assert result["security"]["max_file_size_mb"] == 10
        assert ".git" in result["security"]["excluded_dirs"]

        # Language settings
        assert result["language"]["auto_install"] is True
        assert result["language"]["default_max_depth"] == 7

        # Also verify the container's config was updated
        config = container.get_config()
        assert config.cache.max_size_mb == 256
        assert config.security.max_file_size_mb == 10
        assert config.language.default_max_depth == 7

    finally:
        # Restore original values
        container.config_manager.update_value("cache.max_size_mb", original_cache_size)
        container.config_manager.update_value("security.max_file_size_mb", original_security_size)
        container.config_manager.update_value("language.default_max_depth", original_depth)


def test_real_yaml_example():
    """Test with a real-world example like the one in the issue."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+", delete=False) as temp_file:
        # Copy the example from the issue
        temp_file.write("""cache:
  enabled: true
  max_size_mb: 256
  ttl_seconds: 3600

security:
  max_file_size_mb: 10
  excluded_dirs:
    - .git
    - node_modules
    - __pycache__
    - .cache
    - .claude
    - .config
    - .idea
    - .llm-context
    - .local
    - .npm
    - .phpstorm_helpers
    - .tmp
    - .venv
    - .vscode
    - .w3m
    - admin/logs
    - cache
    - logs
    - tools/data_management/.error_codes_journal
    - tools/code_management/.patch_journal
    - runtime
    - vendor
    - venv
    - .aider*
    - .bash*
    - .claude-preferences.json
    - .codeiumignore
    - .continuerules
    - .env
    - .lesshst
    - .php_history
    - .python-version
    - .viminfo
    - .wget-hsts
    - .windsurfrules

language:
  auto_install: true
  default_max_depth: 7
""")
        temp_file.flush()
        temp_file_path = temp_file.name

    try:
        # Get container to save original values
        container = get_container()
        original_config = container.get_config()

        # Save original values to restore later
        original_cache_size = original_config.cache.max_size_mb
        original_security_size = original_config.security.max_file_size_mb
        original_depth = original_config.language.default_max_depth

        try:
            # Call configure helper
            result = configure(config_path=temp_file_path)

            # Print the result for debugging
            print(f"Configure result: {result}")

            # Verify the returned configuration matches the expected values
            assert result["cache"]["max_size_mb"] == 256
            assert result["security"]["max_file_size_mb"] == 10
            assert ".claude" in result["security"]["excluded_dirs"]
            assert result["language"]["auto_install"] is True
            assert result["language"]["default_max_depth"] == 7

            # Also verify the container's config was updated
            config = container.get_config()
            assert config.cache.max_size_mb == 256
            assert config.security.max_file_size_mb == 10
            assert config.language.default_max_depth == 7

        finally:
            # Restore original values
            container.config_manager.update_value("cache.max_size_mb", original_cache_size)
            container.config_manager.update_value("security.max_file_size_mb", original_security_size)
            container.config_manager.update_value("language.default_max_depth", original_depth)

    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)
