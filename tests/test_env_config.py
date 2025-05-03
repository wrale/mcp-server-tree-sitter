"""Tests for environment variable configuration overrides."""

import os
import tempfile

import pytest
import yaml

from mcp_server_tree_sitter.config import ConfigurationManager


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

    # Clean up
    os.unlink(temp_file_path)


def test_env_overrides_defaults(monkeypatch):
    """Environment variables should override hard-coded defaults."""
    # Using single underscore format that matches current implementation
    monkeypatch.setenv("MCP_TS_CACHE_MAX_SIZE_MB", "512")

    mgr = ConfigurationManager()
    cfg = mgr.get_config()

    assert cfg.cache.max_size_mb == 512, "Environment variable should override default value"
    # ensure other defaults stay intact
    assert cfg.security.max_file_size_mb == 5
    assert cfg.language.default_max_depth == 5


def test_env_overrides_yaml(temp_yaml_file, monkeypatch):
    """Environment variables should take precedence over YAML values."""
    # YAML sets 256; env var must win with 1024
    # Using single underscore format that matches current implementation
    monkeypatch.setenv("MCP_TS_CACHE_MAX_SIZE_MB", "1024")

    # Also set a security env var to verify multiple variables work
    monkeypatch.setenv("MCP_TS_SECURITY_MAX_FILE_SIZE_MB", "15")

    mgr = ConfigurationManager()
    # First load the YAML file
    mgr.load_from_file(temp_yaml_file)

    # Get the loaded config
    cfg = mgr.get_config()

    # Verify environment variables override YAML settings
    assert cfg.cache.max_size_mb == 1024, "Environment variable should override YAML values"
    assert cfg.security.max_file_size_mb == 15, "Environment variable should override YAML values"

    # But YAML values that aren't overridden by env vars should remain
    assert cfg.cache.ttl_seconds == 3600
    assert cfg.language.default_max_depth == 7
    assert cfg.language.auto_install is True


def test_log_level_env_var(monkeypatch):
    """Test the specific MCP_TS_LOG_LEVEL variable that was the original issue."""
    monkeypatch.setenv("MCP_TS_LOG_LEVEL", "DEBUG")

    mgr = ConfigurationManager()
    cfg = mgr.get_config()

    assert cfg.log_level == "DEBUG", "Log level should be set from environment variable"


def test_invalid_env_var_handling(monkeypatch):
    """Test that invalid environment variable values don't crash the system."""
    # Set an invalid value for an integer field
    monkeypatch.setenv("MCP_TS_CACHE_MAX_SIZE_MB", "not_a_number")

    # This should not raise an exception
    mgr = ConfigurationManager()
    cfg = mgr.get_config()

    # The default value should be used
    assert cfg.cache.max_size_mb == 100, "Invalid values should fall back to defaults"
