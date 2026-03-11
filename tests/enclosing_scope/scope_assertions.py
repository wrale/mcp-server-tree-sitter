"""Shared scope assertion helpers for enclosing_scope tests."""

from typing import Any, Dict, Optional

SCOPE_KEYS = {"kind", "text", "start_line", "end_line"}
# Optional key returned when scope text is truncated
SCOPE_KEYS_OPTIONAL = SCOPE_KEYS | {"truncated"}


def assert_scope_has_keys(scope: Dict[str, Any]) -> None:
    """Assert the scope dict has the required keys and no unexpected keys."""
    keys = set(scope.keys())
    assert SCOPE_KEYS <= keys <= SCOPE_KEYS_OPTIONAL, (
        f"Expected keys in {SCOPE_KEYS}..{SCOPE_KEYS_OPTIONAL}, got {keys}"
    )


def assert_scope_is_module(scope: Dict[str, Any], *text_contains: str) -> None:
    """Assert scope is module and optional text snippets are present."""
    assert_scope_has_keys(scope)
    assert scope["kind"] == "module", f"Expected kind 'module', got {scope.get('kind')}"
    for snippet in text_contains:
        assert snippet in scope["text"], f"Expected '{snippet}' in scope text"


def assert_scope_is_function(
    scope: Dict[str, Any],
    *text_contains: str,
    row: Optional[int] = None,
) -> None:
    """Assert scope is function and optional text snippets are present; optionally check row in range."""
    assert_scope_has_keys(scope)
    assert scope["kind"] == "function", f"Expected kind 'function', got {scope.get('kind')}"
    for snippet in text_contains:
        assert snippet in scope["text"], f"Expected '{snippet}' in scope text"
    if row is not None:
        assert scope["start_line"] <= row <= scope["end_line"], (
            f"Expected {row} in [start_line, end_line] = [{scope['start_line']}, {scope['end_line']}]"
        )


def assert_scope_is_function_or_method(
    scope: Dict[str, Any],
    *text_contains: str,
    row: Optional[int] = None,
) -> None:
    """Assert scope is function or method and optional text snippets are present."""
    assert_scope_has_keys(scope)
    assert scope["kind"] in ("function", "method"), f"Expected kind function/method, got {scope.get('kind')}"
    for snippet in text_contains:
        assert snippet in scope["text"], f"Expected '{snippet}' in scope text"
    if row is not None:
        assert scope["start_line"] <= row <= scope["end_line"]


def assert_scope_is_class(scope: Dict[str, Any], *text_contains: str, row: Optional[int] = None) -> None:
    """Assert scope is class and optional text snippets are present."""
    assert_scope_has_keys(scope)
    assert scope["kind"] == "class", f"Expected kind 'class', got {scope.get('kind')}"
    for snippet in text_contains:
        assert snippet in scope["text"], f"Expected '{snippet}' in scope text"
    if row is not None:
        assert scope["start_line"] <= row <= scope["end_line"]


def assert_scope_empty(scope: Dict[str, Any]) -> None:
    """Assert scope is empty (e.g. position outside file)."""
    assert scope == {}, f"Expected empty dict, got {scope}"
