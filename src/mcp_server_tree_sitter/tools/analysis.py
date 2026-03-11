"""Code analysis tools using tree-sitter.

Orchestrates project structure analysis, dependency discovery, and complexity
metrics. Symbol extraction in symbol_extraction; metrics in metrics; dependencies in dependencies.
"""

import os
from collections import Counter
from typing import TypedDict

from ..exceptions import SecurityError
from ..language.registry import LanguageRegistry
from ..models.project import Project
from ..utils.context import MCPContext, MCPContextProtocol
from ..utils.file_io import read_text_file
from ..utils.security import validate_file_access
from ..utils.tree_sitter_helpers import ensure_language, parse_with_cached_tree
from .dependencies import find_dependencies
from .metrics import compute_cyclomatic_complexity, count_lines_and_comments
from .symbol_extraction import extract_symbols


class _EntryPoint(TypedDict):
    path: str
    language: str


class _BuildFile(TypedDict):
    path: str
    type: str


class _KeyFileSymbolCounts(TypedDict):
    file: str
    symbols: dict[str, int]


class ProjectStructureResult(TypedDict, total=False):
    name: str
    path: str
    languages: dict[str, int]
    entry_points: list[_EntryPoint]
    build_files: list[_BuildFile]
    dir_counts: dict[str, int]
    file_counts: dict[str, int]
    total_files: int
    key_files_analysis: dict[str, list[_KeyFileSymbolCounts]]


class ComplexityResult(TypedDict):
    line_count: int
    code_lines: int
    empty_lines: int
    comment_lines: int
    comment_ratio: float
    function_count: int
    class_count: int
    avg_function_lines: float
    cyclomatic_complexity: int
    language: str


__all__ = [
    "ComplexityResult",
    "ProjectStructureResult",
    "extract_symbols",
    "analyze_project_structure",
    "find_dependencies",
    "analyze_code_complexity",
]


def analyze_project_structure(
    project: Project,
    language_registry: LanguageRegistry,
    scan_depth: int = 3,
    mcp_ctx: MCPContextProtocol | None = None,
) -> ProjectStructureResult:
    """
    Analyze the overall structure of a project.

    Args:
        project: Project object
        language_registry: Language registry object
        scan_depth: Depth to scan for detailed analysis (higher is slower)
        mcp_ctx: Optional MCP context for progress reporting

    Returns:
        Project structure analysis
    """
    root = project.root_path

    # Create context for progress reporting
    ctx = MCPContext(mcp_ctx)

    with ctx.progress_scope(100, "Analyzing project structure") as progress:
        # Update language information (5%)
        project.scan_files(language_registry)
        progress.update(5)

    # Count files by language
    languages = project.languages

    # Find potential entry points based on common patterns
    entry_points: list[_EntryPoint] = []
    entry_patterns = {
        "python": ["__main__.py", "main.py", "app.py", "run.py", "manage.py"],
        "javascript": ["index.js", "app.js", "main.js", "server.js"],
        "typescript": ["index.ts", "app.ts", "main.ts", "server.ts"],
        "go": ["main.go"],
        "rust": ["main.rs"],
        "java": ["Main.java", "App.java"],
    }

    for language, patterns in entry_patterns.items():
        if language in languages:
            for pattern in patterns:
                # Look for pattern in root and src directories
                for entry_path in ["", "src/", "lib/"]:
                    candidate = root / entry_path / pattern
                    if candidate.is_file():
                        rel_path = str(candidate.relative_to(root))
                        entry_points.append(_EntryPoint(path=rel_path, language=language))

    # Look for build configuration files
    build_files: list[_BuildFile] = []
    build_patterns = {
        "python": [
            "setup.py",
            "pyproject.toml",
            "requirements.txt",
            "Pipfile",
            "environment.yml",
        ],
        "javascript": ["package.json", "yarn.lock", "npm-shrinkwrap.json"],
        "typescript": ["tsconfig.json"],
        "go": ["go.mod", "go.sum"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "generic": ["Makefile", "CMakeLists.txt", "Dockerfile", "docker-compose.yml"],
    }

    for category, patterns in build_patterns.items():
        for pattern in patterns:
            candidate = root / pattern
            if candidate.is_file():
                rel_path = str(candidate.relative_to(root))
                build_files.append(_BuildFile(path=rel_path, type=category))

    # Analyze directory structure
    dir_counts: Counter = Counter()
    file_counts: Counter = Counter()

    for current_dir, dirs, files in os.walk(root):
        rel_dir = os.path.relpath(current_dir, root)
        if rel_dir == ".":
            rel_dir = ""

        # Skip hidden directories and common excludes
        from ..api import get_config

        config = get_config()
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in config.security.excluded_dirs]

        # Count directories
        dir_counts[rel_dir] = len(dirs)

        # Count files by extension
        for file in files:
            if file.startswith("."):
                continue

            ext = os.path.splitext(file)[1].lower()[1:]
            if ext:
                key = f"{rel_dir}/.{ext}" if rel_dir else f".{ext}"
                file_counts[key] += 1

    # Detailed analysis of key files if scan_depth > 0
    key_files_analysis: dict[str, list[_KeyFileSymbolCounts]] = {}

    if scan_depth > 0:
        # Analyze a sample of files from each language
        for language, _ in languages.items():
            extensions = [ext for ext, lang in language_registry._language_map.items() if lang == language]

            if not extensions:
                continue

            # Find sample files
            sample_files: list[str] = []
            for ext in extensions:
                pattern = f"**/*.{ext}"
                for path in root.glob(pattern):
                    if path.is_file():
                        rel_path = str(path.relative_to(root))
                        sample_files.append(rel_path)

                        if len(sample_files) >= scan_depth:
                            break

                if len(sample_files) >= scan_depth:
                    break

            # Analyze sample files
            if sample_files:
                language_analysis: list[_KeyFileSymbolCounts] = []

                for file_path in sample_files:
                    try:
                        symbols = extract_symbols(project, file_path, language_registry)

                        # Summarize symbols
                        symbol_counts = {
                            symbol_type: len(symbols_list) for symbol_type, symbols_list in symbols.items()
                        }

                        language_analysis.append(
                            _KeyFileSymbolCounts(file=file_path, symbols=symbol_counts)
                        )
                    except Exception:
                        # Skip problematic files
                        continue

                if language_analysis:
                    key_files_analysis[language] = language_analysis

    return ProjectStructureResult(
        name=project.name,
        path=str(project.root_path),
        languages=languages,
        entry_points=entry_points,
        build_files=build_files,
        dir_counts=dict(dir_counts),
        file_counts=dict(file_counts),
        total_files=sum(languages.values()),
        key_files_analysis=key_files_analysis,
    )


def analyze_code_complexity(
    project: Project,
    file_path: str,
    language_registry: LanguageRegistry,
) -> ComplexityResult:
    """
    Analyze code complexity.

    Args:
        project: Project object
        file_path: Path to the file relative to project root
        language_registry: Language registry object

    Returns:
        Complexity metrics
    """
    abs_path = project.get_file_path(file_path)

    try:
        validate_file_access(abs_path, project.root_path)
    except SecurityError as e:
        raise SecurityError(f"Access denied: {e}") from e

    language = language_registry.language_for_file(file_path)
    if not language:
        raise ValueError(f"Could not detect language for {file_path}")

    try:
        language_obj = language_registry.get_language(language)
        safe_lang = ensure_language(language_obj)

        tree, source_bytes = parse_with_cached_tree(abs_path, language, safe_lang)

        lines = read_text_file(abs_path)
        line_metrics = count_lines_and_comments(lines, language)

        symbols = extract_symbols(
            project,
            file_path,
            language_registry,
            ["functions", "classes"],
            exclude_class_methods=True,
        )
        function_count = len(symbols.get("functions", []))
        class_count = len(symbols.get("classes", []))

        cyclomatic_complexity = compute_cyclomatic_complexity(tree, language)

        code_lines = line_metrics["code_lines"]
        avg_func_lines = float(code_lines / function_count if function_count > 0 else code_lines)

        return ComplexityResult(
            line_count=line_metrics["line_count"],
            code_lines=code_lines,
            empty_lines=line_metrics["empty_lines"],
            comment_lines=line_metrics["comment_lines"],
            comment_ratio=line_metrics["comment_ratio"],
            function_count=function_count,
            class_count=class_count,
            avg_function_lines=round(avg_func_lines, 2),
            cyclomatic_complexity=cyclomatic_complexity,
            language=language,
        )

    except Exception as e:
        raise ValueError(f"Error analyzing complexity in {file_path}: {e}") from e
