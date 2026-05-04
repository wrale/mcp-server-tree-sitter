"""Tests for manifest-based entry-point detection in analyze_project_structure.

These cover the augmentation that reads entry points from package manifests
(pyproject.toml [project.scripts] / [tool.poetry.scripts], package.json bin/main,
Cargo.toml [[bin]]) on top of the existing filename-pattern heuristics.
"""

from pathlib import Path

from tests.test_helpers import analyze_project, register_project_tool


def _ep(result, path):
    """Return the entry-point dict for ``path`` or None."""
    for ep in result.get("entry_points", []):
        if ep["path"] == path:
            return ep
    return None


def test_pyproject_project_scripts(tmp_path: Path) -> None:
    """[project.scripts] in pyproject.toml is detected and resolved to a file."""
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "cli.py").write_text("def main():\n    pass\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\n'
        '[project.scripts]\nmycli = "pkg.cli:main"\n'
    )

    register_project_tool(path=str(tmp_path), name="ep_pyproj")
    result = analyze_project(project="ep_pyproj", scan_depth=3)

    ep = _ep(result, "pkg/cli.py")
    assert ep is not None, f"expected pkg/cli.py in entry_points, got {result.get('entry_points')}"
    assert ep["language"] == "python"
    assert ep.get("name") == "mycli"
    assert ep.get("source") == "pyproject.toml"


def test_pyproject_module_only_target(tmp_path: Path) -> None:
    """A 'pkg.mod' target (no ``:func``) resolves to ``pkg/mod.py``."""
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "runner.py").write_text("def run():\n    pass\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\n'
        '[project.scripts]\nrun = "pkg.runner"\n'
    )

    register_project_tool(path=str(tmp_path), name="ep_pyproj_mod")
    result = analyze_project(project="ep_pyproj_mod", scan_depth=3)

    assert _ep(result, "pkg/runner.py") is not None


def test_pyproject_src_layout(tmp_path: Path) -> None:
    """src-layout packages are resolved under ``src/``."""
    (tmp_path / "src" / "demo").mkdir(parents=True)
    (tmp_path / "src" / "demo" / "__init__.py").write_text("")
    (tmp_path / "src" / "demo" / "main.py").write_text("def go():\n    pass\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\n'
        '[project.scripts]\ndemo = "demo.main:go"\n'
    )

    register_project_tool(path=str(tmp_path), name="ep_src_layout")
    result = analyze_project(project="ep_src_layout", scan_depth=3)

    assert _ep(result, "src/demo/main.py") is not None


def test_poetry_scripts(tmp_path: Path) -> None:
    """[tool.poetry.scripts] entries are also picked up."""
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "cli.py").write_text("def main():\n    pass\n")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.poetry]\nname = "demo"\nversion = "0.1.0"\n'
        '[tool.poetry.scripts]\npoet = "pkg.cli:main"\n'
    )

    register_project_tool(path=str(tmp_path), name="ep_poetry")
    result = analyze_project(project="ep_poetry", scan_depth=3)

    ep = _ep(result, "pkg/cli.py")
    assert ep is not None
    assert ep.get("name") == "poet"


def test_package_json_bin_string(tmp_path: Path) -> None:
    """``bin`` as a string maps to a single entry under the package name."""
    (tmp_path / "cli.js").write_text("// entry\n")
    (tmp_path / "package.json").write_text(
        '{"name": "demo-cli", "bin": "./cli.js"}'
    )

    register_project_tool(path=str(tmp_path), name="ep_pkg_string")
    result = analyze_project(project="ep_pkg_string", scan_depth=3)

    ep = _ep(result, "cli.js")
    assert ep is not None
    assert ep["language"] == "javascript"
    assert ep.get("name") == "demo-cli"


def test_package_json_bin_object(tmp_path: Path) -> None:
    """``bin`` as an object maps each key to its file."""
    (tmp_path / "a.ts").write_text("// a\n")
    (tmp_path / "b.js").write_text("// b\n")
    (tmp_path / "package.json").write_text(
        '{"name": "demo", "bin": {"a": "./a.ts", "b": "./b.js"}}'
    )

    register_project_tool(path=str(tmp_path), name="ep_pkg_object")
    result = analyze_project(project="ep_pkg_object", scan_depth=3)

    a = _ep(result, "a.ts")
    b = _ep(result, "b.js")
    assert a is not None and a["language"] == "typescript"
    assert b is not None and b["language"] == "javascript"


def test_cargo_bin(tmp_path: Path) -> None:
    """[[bin]] in Cargo.toml resolves to declared or conventional path."""
    (tmp_path / "src" / "bin").mkdir(parents=True)
    (tmp_path / "src" / "bin" / "tool.rs").write_text("fn main() {}\n")
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "demo"\nversion = "0.1.0"\n'
        '[[bin]]\nname = "tool"\n'
    )

    register_project_tool(path=str(tmp_path), name="ep_cargo")
    result = analyze_project(project="ep_cargo", scan_depth=3)

    ep = _ep(result, "src/bin/tool.rs")
    assert ep is not None
    assert ep["language"] == "rust"
    assert ep.get("name") == "tool"


def test_filename_heuristic_dedup(tmp_path: Path) -> None:
    """A path that matches both heuristic and manifest is listed once."""
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    # main.py at root would be picked up by the filename heuristic
    (tmp_path / "main.py").write_text("def cli():\n    pass\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\n'
        '[project.scripts]\ndemo = "main:cli"\n'
    )

    register_project_tool(path=str(tmp_path), name="ep_dedup")
    result = analyze_project(project="ep_dedup", scan_depth=3)

    matches = [ep for ep in result.get("entry_points", []) if ep["path"] == "main.py"]
    assert len(matches) == 1, f"expected exactly one entry, got {matches}"
