"""Tests for the new ConfigurationManager class."""

from collections.abc import Generator
from pathlib import Path

import pytest
import yaml

# Import will fail initially until we implement the class


@pytest.fixture
def temp_yaml_file(tmp_path: Path) -> Generator[str, None, None]:
    """Create a temporary YAML file with test configuration."""
    test_config = {
        "cache": {"enabled": True, "max_size_mb": 256, "ttl_seconds": 3600},
        "security": {"max_file_size_mb": 10, "excluded_dirs": [".git", "node_modules", "__pycache__", ".cache"]},
        "language": {"default_max_depth": 7},
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(test_config))
    yield str(path)


def test_config_manager_initialization() -> None:
    """Test that ConfigurationManager initializes with default config."""
    # This test will fail until we implement ConfigurationManager
    from mcp_server_tree_sitter.config import ConfigurationManager

    manager = ConfigurationManager()
    config = manager.get_config()

    # Check default values
    assert config.cache.max_size_mb == 100
    assert config.security.max_file_size_mb == 5
    assert config.language.default_max_depth == 5


def test_config_manager_load_from_file(temp_yaml_file: str) -> None:
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


def test_config_manager_update_values() -> None:
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


def test_config_manager_to_dict() -> None:
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


def test_env_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables should override hard-coded defaults."""
    monkeypatch.setenv("MCP_TS_CACHE_MAX_SIZE_MB", "512")

    from mcp_server_tree_sitter.config import ConfigurationManager

    mgr = ConfigurationManager()
    cfg = mgr.get_config()

    assert cfg.cache.max_size_mb == 512, "Environment variable should override default value"
    # ensure other defaults stay intact
    assert cfg.security.max_file_size_mb == 5
    assert cfg.language.default_max_depth == 5


def test_env_overrides_yaml(temp_yaml_file: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables should take precedence over YAML values (at load time)."""
    # YAML sets 256; env var must win with 1024
    monkeypatch.setenv("MCP_TS_CACHE_MAX_SIZE_MB", "1024")
    monkeypatch.setenv("MCP_TS_SECURITY_MAX_FILE_SIZE_MB", "15")

    from mcp_server_tree_sitter.config import ConfigurationManager

    mgr = ConfigurationManager()
    mgr.load_from_file(temp_yaml_file)
    cfg = mgr.get_config()

    assert cfg.cache.max_size_mb == 1024, "Environment variable should override YAML value"
    assert cfg.security.max_file_size_mb == 15, "Environment variable should override YAML value"


def test_explicit_update_value_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Explicit update_value() takes precedence over env vars (env applied only at load)."""
    monkeypatch.setenv("MCP_TS_CACHE_MAX_SIZE_MB", "512")

    from mcp_server_tree_sitter.config import ConfigurationManager

    mgr = ConfigurationManager()
    cfg = mgr.get_config()
    assert cfg.cache.max_size_mb == 512, "Env applied at init"

    mgr.update_value("cache.max_size_mb", 999)
    cfg = mgr.get_config()
    assert cfg.cache.max_size_mb == 999, "Explicit update_value must override env (no re-apply of env)"


def test_precedence_yaml_over_defaults(temp_yaml_file: str) -> None:
    """YAML file values take precedence over schema defaults when file is loaded."""
    from mcp_server_tree_sitter.config import ConfigurationManager

    mgr = ConfigurationManager()
    assert mgr.get_config().cache.max_size_mb == 100, "Default before load"
    mgr.load_from_file(temp_yaml_file)
    assert mgr.get_config().cache.max_size_mb == 256, "YAML value after load"
