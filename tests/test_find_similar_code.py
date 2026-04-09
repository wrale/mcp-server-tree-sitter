"""Tests for AST-based find_similar_code."""

import tempfile
from pathlib import Path

import pytest

from mcp_server_tree_sitter.di import get_container
from mcp_server_tree_sitter.models.project import Project
from mcp_server_tree_sitter.tools.search import (
    _extract_ast_fingerprint,
    _iter_top_level_blocks,
    find_similar_code,
)


@pytest.fixture
def project():
    """Create a test project with Python files."""
    container = get_container()
    lr = container.language_registry

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        (root / "funcs.py").write_text(
            """
def greet(name):
    return f"Hello, {name}"

def farewell(name):
    return f"Goodbye, {name}"

def compute(x, y):
    return x + y
"""
        )

        (root / "classes.py").write_text(
            """
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof"
"""
        )

        (root / "unrelated.py").write_text(
            """
import os
import sys

X = 42
Y = "hello"
"""
        )

        yield Project("test", root), lr, container.tree_cache


def test_extract_ast_fingerprint():
    """Fingerprint extracts both leaf tokens and interior node types."""
    container = get_container()
    parser = container.language_registry.get_parser("python")

    source = b"def foo(x): return x + 1"
    tree = parser.parse(source)
    fp = _extract_ast_fingerprint(tree.root_node, source)

    # Should contain identifiers
    assert ("identifier", "foo") in fp
    assert ("identifier", "x") in fp
    # Should contain structural nodes
    assert "function_definition" in fp
    assert "parameters" in fp
    # Should have reasonable size
    assert len(fp) > 5


def test_extract_ast_fingerprint_empty():
    """Empty source produces minimal fingerprint."""
    container = get_container()
    parser = container.language_registry.get_parser("python")

    tree = parser.parse(b"")
    fp = _extract_ast_fingerprint(tree.root_node, b"")
    assert isinstance(fp, set)


def test_iter_top_level_blocks():
    """Iterates functions, classes, and nested methods."""
    container = get_container()
    parser = container.language_registry.get_parser("python")

    source = b"""
def foo(): pass

class Bar:
    def method(self): pass

X = 1
"""
    tree = parser.parse(source)
    blocks = _iter_top_level_blocks(tree)
    types = [b.type for b in blocks]

    assert "function_definition" in types
    assert "class_definition" in types
    # Should find more than just the top-level function
    assert len(blocks) >= 3  # foo, Bar, X=1


def test_find_similar_function(project):
    """Finds functions structurally similar to a snippet."""
    proj, lr, tc = project

    results = find_similar_code(
        proj,
        "def greet(name): return name",
        lr,
        tc,
        language="python",
        threshold=0.5,
    )

    assert len(results) > 0
    # The top result should be from funcs.py
    files = [r["file"] for r in results]
    assert any("funcs.py" in f for f in files)
    # Should have similarity score
    assert all(r["similarity"] >= 0.5 for r in results)
    # Should be sorted by similarity descending
    sims = [r["similarity"] for r in results]
    assert sims == sorted(sims, reverse=True)


def test_find_similar_class(project):
    """Finds classes structurally similar to a snippet."""
    proj, lr, tc = project

    results = find_similar_code(
        proj,
        """
class Pet:
    def __init__(self, name):
        self.name = name
""",
        lr,
        tc,
        language="python",
        threshold=0.4,
    )

    assert len(results) > 0
    files = [r["file"] for r in results]
    assert any("classes.py" in f for f in files)


def test_find_similar_no_match(project):
    """Returns empty when nothing matches."""
    proj, lr, tc = project

    results = find_similar_code(
        proj,
        """
async def stream_data(url, headers, timeout):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=timeout) as resp:
            async for chunk in resp.content.iter_chunked(1024):
                yield chunk
""",
        lr,
        tc,
        language="python",
        threshold=0.9,
    )

    assert len(results) == 0


def test_find_similar_respects_max_results(project):
    """Respects max_results parameter."""
    proj, lr, tc = project

    results = find_similar_code(
        proj,
        "def f(x): return x",
        lr,
        tc,
        language="python",
        threshold=0.3,
        max_results=2,
    )

    assert len(results) <= 2


def test_find_similar_requires_language(project):
    """Raises error when language is not provided."""
    proj, lr, tc = project

    with pytest.raises(Exception, match="Language is required"):
        find_similar_code(proj, "def foo(): pass", lr, tc, language=None)


def test_find_similar_result_structure(project):
    """Results have the expected fields."""
    proj, lr, tc = project

    results = find_similar_code(
        proj,
        "def greet(name): pass",
        lr,
        tc,
        language="python",
        threshold=0.3,
        max_results=1,
    )

    assert len(results) >= 1
    r = results[0]
    assert "file" in r
    assert "start" in r and "row" in r["start"] and "column" in r["start"]
    assert "end" in r and "row" in r["end"] and "column" in r["end"]
    assert "similarity" in r and 0.0 <= r["similarity"] <= 1.0
    assert "node_type" in r
    assert "text" in r
