"""Code analysis tools using tree-sitter."""

import os
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from ..cache.parser_cache import tree_cache
from ..config import CONFIG
from ..exceptions import SecurityError
from ..language.query_templates import get_query_template
from ..language.registry import LanguageRegistry
from ..models.project import ProjectRegistry
from ..utils.security import validate_file_access

project_registry = ProjectRegistry()
language_registry = LanguageRegistry()


def extract_symbols(
    project_name: str, file_path: str, symbol_types: Optional[List[str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract symbols (functions, classes, etc) from a file.

    Args:
        project_name: Name of the registered project
        file_path: Path to the file relative to project root
        symbol_types: Types of symbols to extract (functions, classes, imports, etc.)

    Returns:
        Dictionary of symbols by type
    """
    project = project_registry.get_project(project_name)
    abs_path = project.get_file_path(file_path)

    try:
        validate_file_access(abs_path, project.root_path)
    except SecurityError as e:
        raise SecurityError(f"Access denied: {e}") from e

    language = language_registry.language_for_file(file_path)
    if not language:
        raise ValueError(f"Could not detect language for {file_path}")

    # Default symbol types if not specified
    if symbol_types is None:
        symbol_types = ["functions", "classes", "imports"]

    # Get query templates for each symbol type
    queries = {}
    for symbol_type in symbol_types:
        template = get_query_template(language, symbol_type)
        if template:
            queries[symbol_type] = template

    if not queries:
        raise ValueError(
            f"No query templates available for {language} and {symbol_types}"
        )

    # Parse file and extract symbols
    try:
        # Check if we have a cached tree
        cached = tree_cache.get(abs_path, language)
        if cached:
            tree, source_bytes = cached
        else:
            # Parse file
            with open(abs_path, "rb") as f:
                source_bytes = f.read()

            parser = language_registry.get_parser(language)
            tree = parser.parse(source_bytes)

            # Cache the tree
            tree_cache.put(abs_path, language, tree, source_bytes)

        # Execute queries
        lang = language_registry.get_language(language)
        symbols: Dict[str, List[Dict[str, Any]]] = {}

        for symbol_type, query_string in queries.items():
            query = lang.query(query_string)
            matches = query.captures(tree.root_node)

            symbols[symbol_type] = []
            for node, capture_name in matches:
                # Skip non-name captures
                if (
                    not capture_name.endswith(".name")
                    and not capture_name == symbol_type
                ):
                    continue

                try:
                    text = source_bytes[node.start_byte : node.end_byte].decode(
                        "utf-8", errors="replace"
                    )

                    symbol = {
                        "name": text,
                        "type": symbol_type,
                        "location": {
                            "start": {
                                "row": node.start_point[0],
                                "column": node.start_point[1],
                            },
                            "end": {
                                "row": node.end_point[0],
                                "column": node.end_point[1],
                            },
                        },
                    }

                    # Add to symbols list
                    symbols[symbol_type].append(symbol)
                except Exception:
                    # Skip problematic nodes
                    continue

        return symbols

    except Exception as e:
        raise ValueError(f"Error extracting symbols from {file_path}: {e}") from e


def analyze_project_structure(project_name: str, scan_depth: int = 3) -> Dict[str, Any]:
    """
    Analyze the overall structure of a project.

    Args:
        project_name: Name of the registered project
        scan_depth: Depth to scan for detailed analysis (higher is slower)

    Returns:
        Project structure analysis
    """
    project = project_registry.get_project(project_name)
    root = project.root_path

    # Update language information
    project.scan_files(language_registry)

    # Count files by language
    languages = project.languages

    # Find potential entry points based on common patterns
    entry_points = []
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
                        entry_points.append(
                            {
                                "path": rel_path,
                                "language": language,
                            }
                        )

    # Look for build configuration files
    build_files = []
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
                build_files.append(
                    {
                        "path": rel_path,
                        "type": category,
                    }
                )

    # Analyze directory structure
    dir_counts: Counter = Counter()
    file_counts: Counter = Counter()

    for current_dir, dirs, files in os.walk(root):
        rel_dir = os.path.relpath(current_dir, root)
        if rel_dir == ".":
            rel_dir = ""

        # Skip hidden directories and common excludes
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".") and d not in CONFIG.security.excluded_dirs
        ]

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
    key_files_analysis = {}

    if scan_depth > 0:
        # Analyze a sample of files from each language
        for language, _ in languages.items():
            extensions = [
                ext
                for ext, lang in language_registry._language_map.items()
                if lang == language
            ]

            if not extensions:
                continue

            # Find sample files
            sample_files = []
            for ext in extensions:
                # Look for files with this extension
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
                language_analysis = []

                for file_path in sample_files:
                    try:
                        symbols = extract_symbols(project_name, file_path)

                        # Summarize symbols
                        symbol_counts = {
                            symbol_type: len(symbols_list)
                            for symbol_type, symbols_list in symbols.items()
                        }

                        language_analysis.append(
                            {
                                "file": file_path,
                                "symbols": symbol_counts,
                            }
                        )
                    except Exception:
                        # Skip problematic files
                        continue

                if language_analysis:
                    key_files_analysis[language] = language_analysis

    return {
        "name": project.name,
        "path": str(project.root_path),
        "languages": languages,
        "entry_points": entry_points,
        "build_files": build_files,
        "dir_counts": dict(dir_counts),
        "file_counts": dict(file_counts),
        "total_files": sum(languages.values()),
        "key_files_analysis": key_files_analysis,
    }


def find_dependencies(project_name: str, file_path: str) -> Dict[str, List[str]]:
    """
    Find dependencies of a file.

    Args:
        project_name: Name of the registered project
        file_path: Path to the file relative to project root

    Returns:
        Dictionary of dependencies (imports, includes, etc.)
    """
    project = project_registry.get_project(project_name)
    abs_path = project.get_file_path(file_path)

    try:
        validate_file_access(abs_path, project.root_path)
    except SecurityError as e:
        raise SecurityError(f"Access denied: {e}") from e

    language = language_registry.language_for_file(file_path)
    if not language:
        raise ValueError(f"Could not detect language for {file_path}")

    # Get the appropriate query for imports
    query_string = get_query_template(language, "imports")
    if not query_string:
        raise ValueError(f"Import query not available for {language}")

    # Parse file and extract imports
    try:
        # Use cached tree if available
        cached = tree_cache.get(abs_path, language)
        if cached:
            tree, source_bytes = cached
        else:
            # Parse file
            with open(abs_path, "rb") as f:
                source_bytes = f.read()

            parser = language_registry.get_parser(language)
            tree = parser.parse(source_bytes)

            # Cache the tree
            tree_cache.put(abs_path, language, tree, source_bytes)

        # Execute query
        lang = language_registry.get_language(language)
        query = lang.query(query_string)
        matches = query.captures(tree.root_node)

        # Organize imports by type
        imports = defaultdict(list)

        for node, capture_name in matches:
            try:
                text = source_bytes[node.start_byte : node.end_byte].decode(
                    "utf-8", errors="replace"
                )

                if capture_name.startswith("import."):
                    category = capture_name.split(".", 1)[1]
                else:
                    category = "import"

                imports[category].append(text)
            except Exception:
                # Skip problematic nodes
                continue

        return dict(imports)

    except Exception as e:
        raise ValueError(f"Error finding dependencies in {file_path}: {e}") from e


def analyze_code_complexity(project_name: str, file_path: str) -> Dict[str, Any]:
    """
    Analyze code complexity.

    Args:
        project_name: Name of the registered project
        file_path: Path to the file relative to project root

    Returns:
        Complexity metrics
    """
    project = project_registry.get_project(project_name)
    abs_path = project.get_file_path(file_path)

    try:
        validate_file_access(abs_path, project.root_path)
    except SecurityError as e:
        raise SecurityError(f"Access denied: {e}") from e

    language = language_registry.language_for_file(file_path)
    if not language:
        raise ValueError(f"Could not detect language for {file_path}")

    # Parse file
    try:
        # Use cached tree if available
        cached = tree_cache.get(abs_path, language)
        if cached:
            tree, source_bytes = cached
        else:
            # Parse file
            with open(abs_path, "rb") as f:
                source_bytes = f.read()

            parser = language_registry.get_parser(language)
            tree = parser.parse(source_bytes)

            # Cache the tree
            tree_cache.put(abs_path, language, tree, source_bytes)

        # Calculate basic metrics
        # Open file for reading text content
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        line_count = len(lines)
        empty_lines = sum(1 for line in lines if line.strip() == "")
        comment_lines = 0

        # Language-specific comment detection
        comment_starters = {
            "python": "#",
            "javascript": "//",
            "typescript": "//",
            "java": "//",
            "c": "//",
            "cpp": "//",
            "go": "//",
            "ruby": "#",
            "rust": "//",
        }

        if language in comment_starters:
            comment_start = comment_starters[language]
            # Count comments for text lines
            comment_lines = 0
            for line in lines:
                if line.strip().startswith(comment_start):
                    comment_lines += 1

        # Get function and class definitions
        symbols = extract_symbols(project_name, file_path, ["functions", "classes"])
        function_count = len(symbols.get("functions", []))
        class_count = len(symbols.get("classes", []))

        # Calculate cyclomatic complexity using AST
        complexity_nodes = {
            "python": [
                "if_statement",
                "for_statement",
                "while_statement",
                "try_statement",
            ],
            "javascript": [
                "if_statement",
                "for_statement",
                "while_statement",
                "try_statement",
            ],
            "typescript": [
                "if_statement",
                "for_statement",
                "while_statement",
                "try_statement",
            ],
            # Add more languages...
        }

        cyclomatic_complexity = 1  # Base complexity

        if language in complexity_nodes:
            # Count decision points
            decision_types = complexity_nodes[language]

            def count_nodes(node: Any, types: List[str]) -> int:
                count = 0
                if node.type in types:
                    count += 1

                for child in node.children:
                    count += count_nodes(child, types)

                return count

            cyclomatic_complexity += count_nodes(tree.root_node, decision_types)

        # Calculate maintainability metrics
        code_lines = line_count - empty_lines - comment_lines
        comment_ratio = comment_lines / line_count if line_count > 0 else 0

        # Estimate average function length
        avg_func_lines = float(
            code_lines / function_count if function_count > 0 else code_lines
        )

        return {
            "line_count": line_count,
            "code_lines": code_lines,
            "empty_lines": empty_lines,
            "comment_lines": comment_lines,
            "comment_ratio": comment_ratio,
            "function_count": function_count,
            "class_count": class_count,
            "avg_function_lines": round(avg_func_lines, 2),
            "cyclomatic_complexity": cyclomatic_complexity,
            "language": language,
        }

    except Exception as e:
        raise ValueError(f"Error analyzing complexity in {file_path}: {e}") from e
