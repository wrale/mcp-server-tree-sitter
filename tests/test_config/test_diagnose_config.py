"""Tests for the diagnose_config tool (YAML config diagnostics)."""

from pathlib import Path

import yaml

from mcp_server_tree_sitter.app import get_app
from tests.test_helpers import diagnose_config


def test_diagnose_config_missing_config_file(tmp_path: Path) -> None:
    """Missing config file is reported in the diagnostic, not via exception."""
    missing = tmp_path / "nonexistent.yaml"
    assert not missing.exists()

    result = diagnose_config(str(missing))

    assert result["file_path"] == str(missing)
    assert result["exists"] is False
    assert result["error"] is not None
    assert "does not exist" in result["error"]
    assert result.get("readable") is False
    assert result.get("yaml_valid") is False
    assert result.get("config_before") is None
    assert result.get("config_after") is None


def test_diagnose_config_invalid_yaml_syntax(tmp_path: Path) -> None:
    """Invalid YAML syntax is reported with yaml_valid False and error set."""
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("key: 'unclosed string\nsecond: line")

    result = diagnose_config(str(bad_yaml))

    assert result["file_path"] == str(bad_yaml)
    assert result["exists"] is True
    assert result["readable"] is True
    assert result["yaml_valid"] is False
    assert result["error"] is not None
    assert "YAML" in result["error"] or "parsing" in result["error"].lower() or "Error" in result["error"]
    assert result.get("config_before") is None
    assert result.get("config_after") is None


def test_diagnose_config_incomplete_partial_config(tmp_path: Path) -> None:
    """Incomplete or invalid config (e.g. wrong types) is reported in error."""
    invalid_config = tmp_path / "invalid.yaml"
    # Type error: max_file_size_mb must be int, not string
    invalid_config.write_text(yaml.dump({"security": {"max_file_size_mb": "ten", "excluded_dirs": []}}))

    result = diagnose_config(str(invalid_config))

    assert result["file_path"] == str(invalid_config)
    assert result["exists"] is True
    assert result["readable"] is True
    assert result["yaml_valid"] is True
    assert result["parsed_data"] is not None
    assert result["error"] is not None
    assert "config" in result["error"].lower() or "update" in result["error"].lower() or "Error" in result["error"]


def test_diagnose_config_valid_config_returns_expected_diagnostic_fields(tmp_path: Path) -> None:
    """Valid config returns expected diagnostic fields and no error."""
    valid_config = tmp_path / "config.yaml"
    test_data = {
        "cache": {"enabled": True, "max_size_mb": 64, "ttl_seconds": 600},
        "security": {"max_file_size_mb": 8, "excluded_dirs": [".git", "node_modules"]},
        "language": {"default_max_depth": 6},
    }
    valid_config.write_text(yaml.dump(test_data))

    app = get_app()
    original = app.get_config()
    original_cache_mb = original.cache.max_size_mb
    original_security_mb = original.security.max_file_size_mb
    original_depth = original.language.default_max_depth

    try:
        result = diagnose_config(str(valid_config))

        assert result["file_path"] == str(valid_config)
        assert result["exists"] is True
        assert result["readable"] is True
        assert result["yaml_valid"] is True
        assert result["error"] is None

        assert result["parsed_data"] is not None
        assert isinstance(result["parsed_data"], dict)
        assert result["parsed_data"]["cache"]["max_size_mb"] == 64
        assert result["parsed_data"]["security"]["max_file_size_mb"] == 8
        assert result["parsed_data"]["language"]["default_max_depth"] == 6

        assert result["config_before"] is not None
        assert "cache.max_size_mb" in result["config_before"]
        assert "security.max_file_size_mb" in result["config_before"]
        assert "language.default_max_depth" in result["config_before"]

        assert result["new_config"] is not None
        assert result["new_config"]["cache.max_size_mb"] == 64
        assert result["new_config"]["security.max_file_size_mb"] == 8
        assert result["new_config"]["language.default_max_depth"] == 6

        assert result["config_after"] is not None
        assert result["config_after"]["cache.max_size_mb"] == 64
        assert result["config_after"]["security.max_file_size_mb"] == 8
        assert result["config_after"]["language.default_max_depth"] == 6
    finally:
        app.config_manager.update_value("cache.max_size_mb", original_cache_mb)
        app.config_manager.update_value("security.max_file_size_mb", original_security_mb)
        app.config_manager.update_value("language.default_max_depth", original_depth)
