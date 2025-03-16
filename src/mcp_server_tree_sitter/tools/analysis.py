"""Code analysis tools using tree-sitter."""

import os
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from ..config import CONFIG
from ..exceptions import SecurityError
from ..language.query_templates import get_query_template
from ..language.registry import LanguageRegistry
from ..models.project import ProjectRegistry
from ..utils.context import MCPContext
from ..utils.file_io import get_comment_prefix, read_text_file
from ..utils.security import validate_file_access
from ..utils.tree_sitter_helpers import (
    ensure_language,
    ensure_node,
    get_node_text,
    parse_with_cached_tree,
)

project_registry = ProjectRegistry()
language_registry = LanguageRegistry()


def extract_symbols(
    project_name: str,
    file_path: str,
    symbol_types: Optional[List[str]] = None,
    exclude_class_methods: bool = False,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract symbols (functions, classes, etc) from a file.

    Args:
        project_name: Name of the registered project
        file_path: Path to the file relative to project root
        symbol_types: Types of symbols to extract (functions, classes, imports, etc.)
        exclude_class_methods: Whether to exclude methods from function count

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
        # Language-specific defaults based on their structural elements
        if language == "rust":
            symbol_types = ["functions", "structs", "imports"]
        elif language == "go":
            symbol_types = ["functions", "structs", "imports"]
        elif language == "c":
            symbol_types = ["functions", "structs", "imports"]
        elif language == "cpp":
            symbol_types = ["functions", "classes", "structs", "imports"]
        elif language == "typescript":
            symbol_types = ["functions", "classes", "interfaces", "imports"]
        elif language == "swift":
            symbol_types = ["functions", "classes", "structs", "imports"]
        elif language == "java":
            symbol_types = ["functions", "classes", "interfaces", "imports"]
        elif language == "kotlin":
            symbol_types = ["functions", "classes", "interfaces", "imports"]
        elif language == "julia":
            symbol_types = ["functions", "modules", "structs", "imports"]
        elif language == "apl":
            symbol_types = ["functions", "namespaces", "variables", "imports"]
        else:
            symbol_types = ["functions", "classes", "imports"]

    # Get query templates for each symbol type
    queries = {}
    for symbol_type in symbol_types:
        template = get_query_template(language, symbol_type)
        if template:
            queries[symbol_type] = template

    if not queries:
        raise ValueError(f"No query templates available for {language} and {symbol_types}")

    # Parse file and extract symbols
    try:
        # Get language object
        language_obj = language_registry.get_language(language)
        safe_lang = ensure_language(language_obj)

        # Parse with cached tree
        tree, source_bytes = parse_with_cached_tree(abs_path, language, safe_lang)

        # Execute queries
        symbols: Dict[str, List[Dict[str, Any]]] = {}
        # Track class ranges to identify methods
        class_ranges = []

        # Process classes first if we need to filter out class methods
        if exclude_class_methods and "classes" in queries:
            if "classes" not in symbols:
                symbols["classes"] = []

            class_query = safe_lang.query(queries["classes"])
            class_matches = class_query.captures(tree.root_node)

            # Process class locations to identify their boundaries
            process_symbol_matches(class_matches, "classes", symbols, source_bytes, tree)

            # Extract class body ranges to check if functions are inside classes
            # Use a more generous range to ensure we catch all methods
            for class_symbol in symbols["classes"]:
                start_row = class_symbol["location"]["start"]["row"]
                # For class end, we need to estimate where the class body might end
                # by scanning the file for likely class boundaries
                source_lines = source_bytes.decode("utf-8", errors="replace").splitlines()
                # Find a reasonable estimate for where the class ends
                end_row = min(start_row + 30, len(source_lines) - 1)
                class_ranges.append((start_row, end_row))

        # Now process all symbol types
        for symbol_type, query_string in queries.items():
            # Skip classes if we already processed them
            if symbol_type == "classes" and exclude_class_methods and class_ranges:
                continue

            if symbol_type not in symbols:
                symbols[symbol_type] = []

            query = safe_lang.query(query_string)
            matches = query.captures(tree.root_node)

            process_symbol_matches(
                matches,
                symbol_type,
                symbols,
                source_bytes,
                tree,
                (class_ranges if exclude_class_methods and symbol_type == "functions" else None),
            )

        return symbols

    except Exception as e:
        raise ValueError(f"Error extracting symbols from {file_path}: {e}") from e


def process_symbol_matches(
    matches: Any,
    symbol_type: str,
    symbols_dict: Dict[str, List[Dict[str, Any]]],
    source_bytes: bytes,
    tree: Any,
    class_ranges: Optional[List[Tuple[int, int]]] = None,
) -> None:
    """
    Process matches from a query and extract symbols.

    Args:
        matches: Query matches result
        symbol_type: Type of symbol being processed
        symbols_dict: Dictionary to store extracted symbols
        source_bytes: Source file bytes
        tree: Parsed syntax tree
        class_ranges: Optional list of class ranges to filter out class methods
    """

    # Helper function to check if a node is inside a class
    def is_inside_class(node_row: int) -> bool:
        if not class_ranges:
            return False
        for start_row, end_row in class_ranges:
            if start_row <= node_row <= end_row:
                return True
        return False

    # Track functions that should be filtered out (methods inside classes)
    filtered_methods: List[int] = []

    # Helper function to process a single node into a symbol
    def process_node(node: Any, capture_name: str) -> None:
        try:
            safe_node = ensure_node(node)

            # Skip methods inside classes if processing functions with class ranges
            if class_ranges is not None and is_inside_class(safe_node.start_point[0]):
                filtered_methods.append(safe_node.start_point[0])
                return

            # Skip non-name captures
            if not capture_name.endswith(".name") and not capture_name == symbol_type:
                return

            text = get_node_text(safe_node, source_bytes)

            symbol = {
                "name": text,
                "type": symbol_type,
                "location": {
                    "start": {
                        "row": safe_node.start_point[0],
                        "column": safe_node.start_point[1],
                    },
                    "end": {
                        "row": safe_node.end_point[0],
                        "column": safe_node.end_point[1],
                    },
                },
            }

            # Add to symbols list
            symbols_dict[symbol_type].append(symbol)

        except Exception:
            # Skip problematic nodes
            pass

    # Process nodes based on return format
    if isinstance(matches, dict):
        # Dictionary format: {capture_name: [node1, node2, ...], ...}
        for capture_name, nodes in matches.items():
            for node in nodes:
                process_node(node, capture_name)
    else:
        # List format: [(node1, capture_name1), (node2, capture_name2), ...]
        for match in matches:
            # Handle different return types from query.captures()
            if isinstance(match, tuple) and len(match) == 2:
                # Direct tuple unpacking
                node, capture_name = match
            elif hasattr(match, "node") and hasattr(match, "capture_name"):
                # Object with node and capture_name attributes
                node, capture_name = match.node, match.capture_name
            elif isinstance(match, dict) and "node" in match and "capture" in match:
                # Dictionary with node and capture keys
                node, capture_name = match["node"], match["capture"]
            else:
                # Skip if format is unknown
                continue

            process_node(node, capture_name)


def analyze_project_structure(project_name: str, scan_depth: int = 3, mcp_ctx: Optional[Any] = None) -> Dict[str, Any]:
    """
    Analyze the overall structure of a project.

    Args:
        project_name: Name of the registered project
        scan_depth: Depth to scan for detailed analysis (higher is slower)
        mcp_ctx: Optional MCP context for progress reporting

    Returns:
        Project structure analysis
    """
    project = project_registry.get_project(project_name)
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
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in CONFIG.security.excluded_dirs]

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
            extensions = [ext for ext, lang in language_registry._language_map.items() if lang == language]

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
                            symbol_type: len(symbols_list) for symbol_type, symbols_list in symbols.items()
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
        # Get language object
        language_obj = language_registry.get_language(language)
        safe_lang = ensure_language(language_obj)

        # Parse with cached tree
        tree, source_bytes = parse_with_cached_tree(abs_path, language, safe_lang)

        # Execute query
        query = safe_lang.query(query_string)
        matches = query.captures(tree.root_node)

        # Organize imports by type
        imports = defaultdict(list)
        # Track additional import information to handle aliased imports
        module_imports: Set[str] = set()

        # Helper function to process an import node
        def process_import_node(node: Any, capture_name: str) -> None:
            try:
                safe_node = ensure_node(node)
                text = get_node_text(safe_node, source_bytes)

                # Determine the import category
                if capture_name.startswith("import."):
                    category = capture_name.split(".", 1)[1]
                else:
                    category = "import"

                imports[category].append(text)

                # Add to module_imports for tracking all imported modules
                if category == "from":
                    # Handle 'from X import Y' cases
                    module_imports.add(text.split()[0].strip())
                elif category == "module":
                    # Handle 'import X' cases
                    module_imports.add(text.strip())
                elif "import" in text:
                    # Fallback for raw import statements
                    parts = text.split()
                    if len(parts) > 1 and parts[0] == "from":
                        # Handle 'from datetime import datetime as dt' case
                        module_imports.add(parts[1].strip())
                    elif "from" in text and "import" in text:
                        # Another way to handle 'from X import Y' patterns
                        from_parts = text.split("from", 1)[1].split("import", 1)
                        if len(from_parts) > 0:
                            module_name = from_parts[0].strip()
                            module_imports.add(module_name)
                    elif parts[0] == "import":
                        for module in " ".join(parts[1:]).split(","):
                            module = module.strip().split(" as ")[0].strip()
                            module_imports.add(module)
            except Exception:
                # Skip problematic nodes
                pass

        # Handle different return formats from query.captures()
        if isinstance(matches, dict):
            # Dictionary format: {capture_name: [node1, node2, ...], ...}
            for capture_name, nodes in matches.items():
                for node in nodes:
                    process_import_node(node, capture_name)
        else:
            # List format: [(node1, capture_name1), (node2, capture_name2), ...]
            for match in matches:
                # Handle different return types from query.captures()
                if isinstance(match, tuple) and len(match) == 2:
                    # Direct tuple unpacking
                    node, capture_name = match
                elif hasattr(match, "node") and hasattr(match, "capture_name"):
                    # Object with node and capture_name attributes
                    node, capture_name = match.node, match.capture_name
                elif isinstance(match, dict) and "node" in match and "capture" in match:
                    # Dictionary with node and capture keys
                    node, capture_name = match["node"], match["capture"]
                else:
                    # Skip if format is unknown
                    continue

                process_import_node(node, capture_name)

        # Add all detected modules to the result
        if module_imports:
            imports["module"] = list(set(imports.get("module", []) + list(module_imports)))

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
        # Get language object
        language_obj = language_registry.get_language(language)
        safe_lang = ensure_language(language_obj)

        # Parse with cached tree
        tree, source_bytes = parse_with_cached_tree(abs_path, language, safe_lang)

        # Calculate basic metrics
        # Read lines from file using utility
        lines = read_text_file(abs_path)

        line_count = len(lines)
        empty_lines = sum(1 for line in lines if line.strip() == "")
        comment_lines = 0

        # Language-specific comment detection using utility
        comment_prefix = get_comment_prefix(language)
        if comment_prefix:
            # Count comments for text lines
            comment_lines = sum(1 for line in lines if line.strip().startswith(comment_prefix))

        # Get function and class definitions, excluding methods from count
        symbols = extract_symbols(
            project_name,
            file_path,
            ["functions", "classes"],
            exclude_class_methods=True,
        )
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
                safe_node = ensure_node(node)
                count = 0
                if safe_node.type in types:
                    count += 1

                for child in safe_node.children:
                    count += count_nodes(child, types)

                return count

            cyclomatic_complexity += count_nodes(tree.root_node, decision_types)

        # Calculate maintainability metrics
        code_lines = line_count - empty_lines - comment_lines
        comment_ratio = comment_lines / line_count if line_count > 0 else 0

        # Estimate average function length
        avg_func_lines = float(code_lines / function_count if function_count > 0 else code_lines)

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
