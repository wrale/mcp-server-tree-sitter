"""Tests for the new ConfigurationManager class."""

import os
import tempfile

import pytest
import yaml

# Import will fail initially until we implement the class


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


def test_config_manager_initialization():
    """Test that ConfigurationManager initializes with default config."""
    # This test will fail until we implement ConfigurationManager
    from mcp_server_tree_sitter.config import ConfigurationManager

    manager = ConfigurationManager()
    config = manager.get_config()

    # Check default values
    assert config.cache.max_size_mb == 100
    assert config.security.max_file_size_mb == 5
    assert config.language.default_max_depth == 5


def test_config_manager_load_from_file(temp_yaml_file):
    """Test loading configuration from a file."""
    # This test will fail until we implement ConfigurationManager
    from mcp_server_tree_sitter.config import ConfigurationManager

    manager = ConfigurationManager()
    manager.load_from_file(temp_yaml_file)
    config = manager.get_config()

    # Check loaded values
    assert config.cache.max_size_mb == 256
    assert config.security.max_file_size_mb == 10
    assert config.language.default_max_depth == 7


def test_config_manager_update_values():
    """Test updating individual configuration values."""
    # This test will fail until we implement ConfigurationManager
    from mcp_server_tree_sitter.config import ConfigurationManager

    manager = ConfigurationManager()

    # Update values
    manager.update_value("cache.max_size_mb", 512)
    manager.update_value("security.max_file_size_mb", 20)

    # Check updated values
    config = manager.get_config()
    assert config.cache.max_size_mb == 512
    assert config.security.max_file_size_mb == 20


def test_config_manager_to_dict():
    """Test converting configuration to dictionary."""
    # This test will fail until we implement ConfigurationManager
    from mcp_server_tree_sitter.config import ConfigurationManager

    manager = ConfigurationManager()
    config_dict = manager.to_dict()

    # Check dictionary structure
    assert "cache" in config_dict
    assert "security" in config_dict
    assert "language" in config_dict
    assert config_dict["cache"]["max_size_mb"] == 100


def test_env_overrides_defaults(monkeypatch):
    """Environment variables should override hard-coded defaults."""
    monkeypatch.setenv("MCP_TS_CACHE_MAX_SIZE_MB", "512")

    from mcp_server_tree_sitter.config import ConfigurationManager

    mgr = ConfigurationManager()
    cfg = mgr.get_config()

    assert cfg.cache.max_size_mb == 512, "Environment variable should override default value"
    # ensure other defaults stay intact
    assert cfg.security.max_file_size_mb == 5
    assert cfg.language.default_max_depth == 5


def test_env_overrides_yaml(temp_yaml_file, monkeypatch):
    """Environment variables should take precedence over YAML values."""
    # YAML sets 256; env var must win with 1024
    monkeypatch.setenv("MCP_TS_CACHE_MAX_SIZE_MB", "1024")
    monkeypatch.setenv("MCP_TS_SECURITY_MAX_FILE_SIZE_MB", "15")

    from mcp_server_tree_sitter.config import ConfigurationManager

    mgr = ConfigurationManager()
    mgr.load_from_file(temp_yaml_file)
    cfg = mgr.get_config()

    assert cfg.cache.max_size_mb == 1024, "Environment variable should override YAML value"
    assert cfg.security.max_file_size_mb == 15, "Environment variable should override YAML value"
