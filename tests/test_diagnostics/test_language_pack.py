"""Pytest-based diagnostic tests for tree-sitter language pack integration."""

import sys

import pytest


@pytest.mark.diagnostic
def test_tree_sitter_import(diagnostic) -> None:
    """Test basic import of tree-sitter library."""
    try:
        # Try to import the tree-sitter library
        import tree_sitter

        # Record basic functionality information
        results = {
            "version": getattr(tree_sitter, "__version__", "Unknown"),
            "has_language": hasattr(tree_sitter, "Language"),
            "has_parser": hasattr(tree_sitter, "Parser"),
            "has_tree": hasattr(tree_sitter, "Tree"),
            "has_node": hasattr(tree_sitter, "Node"),
            "dir_contents": dir(tree_sitter),
        }
        diagnostic.add_detail("tree_sitter_info", results)

        # Check if Parser can be initialized
        try:
            _ = tree_sitter.Parser()
            diagnostic.add_detail("can_create_parser", True)
        except Exception as e:
            diagnostic.add_detail("can_create_parser", False)
            diagnostic.add_error("ParserCreationError", str(e))

        # Verify the basic components are available
        assert hasattr(tree_sitter, "Language"), "tree_sitter should have Language class"
        assert hasattr(tree_sitter, "Parser"), "tree_sitter should have Parser class"
        assert hasattr(tree_sitter, "Tree"), "tree_sitter should have Tree class"
        assert hasattr(tree_sitter, "Node"), "tree_sitter should have Node class"

    except ImportError as e:
        diagnostic.add_error("ImportError", str(e))
        pytest.fail(f"Failed to import tree_sitter: {e}")
    except Exception as e:
        diagnostic.add_error("UnexpectedError", str(e))
        raise


@pytest.mark.diagnostic
def test_language_pack_import(diagnostic) -> None:
    """Test basic import of tree-sitter-language-pack."""
    try:
        # Try to import the tree-sitter-language-pack
        import tree_sitter_language_pack

        # Check if bindings are available
        bindings_available = hasattr(tree_sitter_language_pack, "bindings")
        version = getattr(tree_sitter_language_pack, "__version__", "Unknown")

        results = {
            "version": version,
            "bindings_available": bindings_available,
            "dir_contents": dir(tree_sitter_language_pack),
        }
        diagnostic.add_detail("language_pack_info", results)

        # Test basic assertions
        assert hasattr(tree_sitter_language_pack, "get_language"), (
            "tree_sitter_language_pack should have get_language function"
        )
        assert hasattr(tree_sitter_language_pack, "get_parser"), (
            "tree_sitter_language_pack should have get_parser function"
        )

    except ImportError as e:
        diagnostic.add_error("ImportError", str(e))
        pytest.fail(f"Failed to import tree_sitter_language_pack: {e}")
    except Exception as e:
        diagnostic.add_error("UnexpectedError", str(e))
        raise


@pytest.mark.diagnostic
def test_language_binding_available(diagnostic) -> None:
    """Test if specific language bindings are available."""
    test_languages = [
        "python",
        "javascript",
        "typescript",
        "c",
        "cpp",
        "go",
        "rust",
    ]

    language_results = {}
    try:
        # Use find_spec to check if the module is available
        import importlib.util

        has_pack = importlib.util.find_spec("tree_sitter_language_pack") is not None
        diagnostic.add_detail("has_language_pack", has_pack)

        # If we have the language_pack, we'll try to use it later
        # through _get_language_binding()

        for language in test_languages:
            try:
                # Try to get the binding for this language
                binding_result = _get_language_binding(language)
                language_results[language] = binding_result
            except Exception as e:
                language_results[language] = {
                    "status": "error",
                    "error": str(e),
                }

        diagnostic.add_detail("language_results", language_results)

        # Check that at least some languages are available
        successful_languages = [lang for lang, result in language_results.items() if result.get("status") == "success"]

        if not successful_languages:
            diagnostic.add_error("NoLanguagesAvailable", "None of the test languages are available")

        assert len(successful_languages) > 0, "No languages are available"

    except ImportError:
        diagnostic.add_error("ImportError", "tree_sitter_language_pack not available")
        pytest.fail("tree_sitter_language_pack not available")
    except Exception as e:
        diagnostic.add_error("UnexpectedError", str(e))
        raise


def _get_language_binding(language_name) -> dict:
    """Helper method to test getting a language binding from the language pack."""
    try:
        from tree_sitter_language_pack import get_language, get_parser

        # Get language (may raise exception)
        language = get_language(language_name)

        # Try to get a parser
        parser = get_parser(language_name)

        return {
            "status": "success",
            "language_available": language is not None,
            "parser_available": parser is not None,
            "language_type": type(language).__name__ if language else None,
            "parser_type": type(parser).__name__ if parser else None,
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
        }


@pytest.mark.diagnostic
def test_python_environment(diagnostic) -> None:
    """Test the Python environment to help diagnose issues."""
    env_info = {
        "python_version": sys.version,
        "python_path": sys.executable,
        "sys_path": sys.path,
        "modules": sorted(list(sys.modules.keys())),
    }

    diagnostic.add_detail("python_environment", env_info)
    diagnostic.add_detail("environment_captured", True)
