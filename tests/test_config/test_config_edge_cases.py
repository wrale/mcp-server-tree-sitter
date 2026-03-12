"""Configuration edge-case tests.

Covers: malformed YAML, unknown keys, env var overrides, runtime update_value(),
precedence order verification.
"""

from pathlib import Path

import pytest

from mcp_server_tree_sitter.config import ConfigurationManager, ServerConfig
from mcp_server_tree_sitter.config_loader import load_config_from_file


def test_malformed_yaml_returns_defaults(tmp_path: Path) -> None:
    """Malformed YAML file loading returns default config (no crash)."""
    path = tmp_path / "config.yaml"
    path.write_text("cache:\n  enabled: true\n  max_size_mb: [broken\n")
    config = load_config_from_file(str(path))
    assert isinstance(config, ServerConfig)
    assert config.cache.max_size_mb == 100  # default


def test_malformed_yaml_manager_keeps_previous_config(tmp_path: Path) -> None:
    """ConfigurationManager.load_from_file on malformed YAML keeps previous config."""
    bad_path = tmp_path / "bad.yaml"
    bad_path.write_text("not: valid: yaml: [[[")
    mgr = ConfigurationManager()
    mgr.update_value("cache.max_size_mb", 200)
    mgr.load_from_file(str(bad_path))
    cfg = mgr.get_config()
    assert cfg.cache.max_size_mb == 200


def test_unknown_keys_in_yaml_ignored_or_defaulted(tmp_path: Path) -> None:
    """Unknown top-level or section keys do not crash; valid keys applied."""
    path = tmp_path / "config.yaml"
    path.write_text("cache:\n  max_size_mb: 64\n  unknown_key: 999\nunknown_section: {}\n")
    config = load_config_from_file(str(path))
    assert config.cache.max_size_mb == 64


def test_unknown_key_update_value_logs_no_crash() -> None:
    """update_value with unknown key does not crash (logs warning)."""
    mgr = ConfigurationManager()
    mgr.update_value("nonexistent.thing", 1)
    mgr.update_value("cache.nonexistent_key", 2)
    cfg = mgr.get_config()
    assert cfg.cache.max_size_mb == 100


def test_env_var_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables override default values at load time."""
    monkeypatch.setenv("MCP_TS_CACHE_MAX_SIZE_MB", "128")
    monkeypatch.setenv("MCP_TS_LOG_LEVEL", "DEBUG")
    mgr = ConfigurationManager()
    cfg = mgr.get_config()
    assert cfg.cache.max_size_mb == 128
    assert cfg.log_level == "DEBUG"


def test_runtime_update_value_persists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Runtime update_value() takes effect and persists (overrides env at runtime)."""
    monkeypatch.setenv("MCP_TS_CACHE_MAX_SIZE_MB", "64")
    mgr = ConfigurationManager()
    cfg = mgr.get_config()
    assert cfg.cache.max_size_mb == 64
    mgr.update_value("cache.max_size_mb", 256)
    cfg = mgr.get_config()
    assert cfg.cache.max_size_mb == 256


def test_precedence_update_value_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Precedence: update_value() over env (env applied at init; update_value wins after)."""
    monkeypatch.setenv("MCP_TS_CACHE_TTL_SECONDS", "600")
    mgr = ConfigurationManager()
    mgr.update_value("cache.ttl_seconds", 120)
    cfg = mgr.get_config()
    assert cfg.cache.ttl_seconds == 120


def test_precedence_env_over_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Precedence: env over YAML when both present (env applied after YAML load)."""
    monkeypatch.setenv("MCP_TS_SECURITY_MAX_FILE_SIZE_MB", "20")
    path = tmp_path / "config.yaml"
    path.write_text("security:\n  max_file_size_mb: 10\n")
    mgr = ConfigurationManager()
    mgr.load_from_file(str(path))
    cfg = mgr.get_config()
    assert cfg.security.max_file_size_mb == 20


def test_precedence_yaml_over_defaults(tmp_path: Path) -> None:
    """Precedence: YAML file values override schema defaults."""
    path = tmp_path / "config.yaml"
    path.write_text("language:\n  default_max_depth: 8\n")
    config = load_config_from_file(str(path))
    assert config.language.default_max_depth == 8
