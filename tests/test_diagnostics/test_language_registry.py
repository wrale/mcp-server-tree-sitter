"""Pytest-based diagnostic tests for language registry functionality."""

import pytest

from mcp_server_tree_sitter.language.registry import LanguageRegistry


@pytest.mark.diagnostic
def test_language_detection(diagnostic) -> None:
    """Test language detection functionality."""
    registry = LanguageRegistry()

    # Test a few common file extensions
    test_files = {
        "test.py": "python",
        "test.js": "javascript",
        "test.ts": "typescript",
        "test.go": "go",
        "test.cpp": "cpp",
        "test.c": "c",
        "test.rs": "rust",
        "test.unknown": None,
    }

    results = {}
    failures = []

    for filename, expected in test_files.items():
        detected = registry.language_for_file(filename)
        match = detected == expected

        results[filename] = {"detected": detected, "expected": expected, "match": match}

        if not match:
            failures.append(filename)

    # Add all results to diagnostic data
    diagnostic.add_detail("detection_results", results)
    if failures:
        diagnostic.add_detail("failed_files", failures)

    # Check results with proper assertions
    for filename, expected in test_files.items():
        assert registry.language_for_file(filename) == expected, f"Language detection failed for {filename}"


@pytest.mark.diagnostic
def test_language_list_empty(diagnostic) -> None:
    """Test that list_languages returns languages correctly."""
    registry = LanguageRegistry()

    # Get available languages
    available_languages = registry.list_available_languages()
    installable_languages = registry.list_installable_languages()

    # Add results to diagnostic data
    diagnostic.add_detail("available_languages", available_languages)
    diagnostic.add_detail("installable_languages", installable_languages)

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
    for lang in expected_languages:
        if lang not in available_languages:
            diagnostic.add_error(
                "LanguageNotAvailable",
                f"Expected language {lang} not in available languages",
            )

    # Assert that some languages are available
    assert len(available_languages) > 0, "No languages available"

    # Assert that we find at least some of our expected languages
    common_languages = set(expected_languages) & set(available_languages)
    assert len(common_languages) > 0, "None of the expected languages are available"


@pytest.mark.diagnostic
def test_language_detection_vs_listing(diagnostic) -> None:
    """Test discrepancy between language detection and language listing."""
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

    results = {}
    for lang in test_languages:
        try:
            # Check if language is available
            if registry.is_language_available(lang):
                results[lang] = {
                    "available": True,
                    "language_object": bool(registry.get_language(lang) is not None),
                    "reason": "",
                }
            else:
                results[lang] = {
                    "available": False,
                    "reason": "Not available in language-pack",
                    "language_object": False,
                }
        except Exception as e:
            results[lang] = {"available": False, "error": str(e), "language_object": False}

    # Check if languages reported as available appear in list_languages
    available_languages = registry.list_available_languages()

    # Add results to diagnostic data
    diagnostic.add_detail("language_results", results)
    diagnostic.add_detail("available_languages", available_languages)

    # Compare detection vs listing
    discrepancies = []
    for lang, result in results.items():
        if result.get("available", False) and lang not in available_languages:
            discrepancies.append(lang)

    if discrepancies:
        diagnostic.add_error(
            "LanguageInconsistency",
            f"Languages available but not in list_languages: {discrepancies}",
        )

    # For diagnostic purposes, not all assertions should fail
    # This checks if there are any available languages
    successful_languages = [lang for lang, result in results.items() if result.get("available", False)]

    assert len(successful_languages) > 0, "No languages could be successfully installed"
