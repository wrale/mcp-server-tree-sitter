"""Test for language listing functionality."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_server_tree_sitter.language.registry import LanguageRegistry
from tests.test_helpers import check_language_available, list_languages


def test_list_available_languages() -> None:
    """Test that list_available_languages returns languages correctly."""
    registry = LanguageRegistry()

    # Get available languages
    available_languages = registry.list_available_languages()

    # Check for common languages we expect to be available
    expected_languages = [
        "python",
        "javascript",
        "typescript",
        "c",
        "cpp",
        "go",
        "rust",
    ]

    # Assert that we have languages available
    assert len(available_languages) > 0, "No languages available"

    # Assert that we find at least some of our expected languages
    for lang in expected_languages:
        assert lang in available_languages, f"Expected language {lang} not in available languages"


def test_language_api_consistency() -> None:
    """Test consistency between language detection and language listing."""
    registry = LanguageRegistry()

    # Test with a few common languages
    test_languages = [
        "python",
        "javascript",
        "typescript",
        "c",
        "cpp",
        "go",
        "rust",
    ]

    # Check each language both through is_language_available and list_available_languages
    available_languages = registry.list_available_languages()

    for lang in test_languages:
        is_available = registry.is_language_available(lang)
        is_listed = lang in available_languages

        # Both methods should return the same result
        assert is_available == is_listed, f"Inconsistency for {lang}: available={is_available}, listed={is_listed}"


def test_server_language_tools() -> None:
    """Test the server language tools."""
    # Test list_languages
    languages_result = list_languages()
    assert "available" in languages_result, "Missing 'available' key in list_languages result"
    assert isinstance(languages_result["available"], list), "'available' should be a list"
    assert len(languages_result["available"]) > 0, "No languages available"

    # Test each language with check_language_available
    for lang in ["python", "javascript", "typescript"]:
        result = check_language_available(lang)
        assert result["status"] == "success", f"Language {lang} should be available"
        assert "message" in result, "Missing 'message' key in check_language_available result"


def test_fallback_extension_overwritten_by_language_data_warns(caplog: pytest.LogCaptureFixture) -> None:
    """When the loader returns an extension that is also in the fallback list, registry logs a warning.
    Language data takes precedence; the warning guarantees we are aware of the overlap.
    """
    # Extensions "rb" and "json" are in _EXTENSION_FALLBACK. Simulate language data
    # providing "rb" -> "ruby" so fallback is skipped for "rb" and we warn.
    loader_extension_map = {"py": "python", "rb": "ruby", "js": "javascript"}
    # Patch the module-level get_extension_map so the registry gets our map when it does
    # "from .loader import get_extension_map" and calls it in __init__.
    with patch(
        "mcp_server_tree_sitter.language.loader.get_extension_map",
        MagicMock(return_value=loader_extension_map),
    ):
        with caplog.at_level("WARNING"):
            LanguageRegistry()

    # When an extension from fallback is already set by language data, we skip it and warn
    fallback_overwrite_warnings = [
        r for r in caplog.records if "already set by language data" in r.message and "fallback" in r.message
    ]
    assert len(fallback_overwrite_warnings) >= 1, (
        "Expected a warning when fallback extension is overwritten by language data"
    )
    assert any("rb" in r.message for r in fallback_overwrite_warnings), (
        "Warning should mention the overlapping extension (rb)"
    )


if __name__ == "__main__":
    test_list_available_languages()
    test_language_api_consistency()
    test_server_language_tools()
    print("All tests passed!")
