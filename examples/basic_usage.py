"""
Example of using mcp-server-tree-sitter to analyze a project.

This script demonstrates:
- Project registration and analysis
- AST extraction and traversal
- Symbol extraction (functions, classes)
- Dependency analysis
- Complexity analysis
- Text search
"""

import os
import logging
import sys
from pathlib import Path
import argparse
from typing import Optional, Dict, Any, List

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the MCP server
from mcp_server_tree_sitter.server import mcp
from mcp_server_tree_sitter.config import load_config
from mcp_server_tree_sitter.utils.context import MCPContext


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_project(project_path: str, project_name: Optional[str] = None) -> str:
    """
    Analyze a project using mcp-server-tree-sitter.
    
    Args:
        project_path: Path to the project directory
        project_name: Name for the project (defaults to directory name)
        
    Returns:
        Project name
    """
    # Create context for progress reporting
    ctx = MCPContext()
    
    # Use progress scope for registration
    with ctx.progress_scope(100, "Registering and analyzing project") as progress:
        # Register the project
        if project_name is None:
            project_name = Path(project_path).name
            
        print(f"Registering project '{project_name}' at {project_path}")
        try:
            project_info = mcp.tools.register_project_tool(
                path=project_path, 
                name=project_name
            )
            progress.update(20)  # Update progress
            
            # Print project info
            print(f"Project registered with {len(project_info['languages'])} languages:")
            for lang, count in project_info['languages'].items():
                print(f"  - {lang}: {count} files")
            
            # Analyze project structure
            print("\nAnalyzing project structure...")
            analysis = mcp.tools.analyze_project(project_name, ctx=ctx)
            progress.update(40)
            
            # Print entry points
            if "entry_points" in analysis and analysis["entry_points"]:
                print("\nPossible entry points:")
                for entry in analysis["entry_points"]:
                    print(f"  - {entry['path']} ({entry['language']})")
            
            # Print build files
            if "build_files" in analysis and analysis["build_files"]:
                print("\nBuild configuration:")
                for file in analysis["build_files"]:
                    print(f"  - {file['path']} ({file['type']})")
            
            progress.update(60)
            
            # Find and analyze files
            analyze_files(project_name, progress)
            
        except Exception as e:
            ctx.error(f"Error during project analysis: {e}")
            logger.exception("Project analysis failed")
            raise
    
    return project_name


def analyze_files(project_name: str, progress: Any) -> None:
    """
    Analyze files in the project to extract symbols and structure.
    
    Args:
        project_name: Name of the registered project
        progress: Progress scope for reporting
    """
    # Find Python files
    print("\nSearching for Python files and extracting symbols...")
    py_files = mcp.tools.list_files(project_name, extensions=["py"])
    
    if not py_files:
        print("No Python files found in the project.")
        return
    
    # This uses the fixed symbol extraction functionality
    for idx, file_path in enumerate(py_files[:5]):  # Limit to first 5 files for brevity
        print(f"\nAnalyzing {file_path}:")
        try:
            # Extract symbols (now working correctly)
            symbols = mcp.tools.get_symbols(project_name, file_path)
            
            # Print functions
            if "functions" in symbols and symbols["functions"]:
                print("  Functions:")
                for func in symbols["functions"][:5]:  # Limit to first 5 functions
                    func_info = f"{func['name']}"
                    # Include location if available
                    if "location" in func:
                        start = func["location"]["start"]
                        func_info += f" (line {start['row'] + 1})"
                    print(f"    - {func_info}")
            else:
                print("  No functions found.")
            
            # Print classes
            if "classes" in symbols and symbols["classes"]:
                print("  Classes:")
                for cls in symbols["classes"][:5]:  # Limit to first 5 classes
                    cls_info = f"{cls['name']}"
                    # Include location if available
                    if "location" in cls:
                        start = cls["location"]["start"]
                        cls_info += f" (line {start['row'] + 1})"
                    print(f"    - {cls_info}")
            else:
                print("  No classes found.")
            
            # Try to get dependencies (now working correctly)
            dependencies = mcp.tools.get_dependencies(project_name, file_path)
            if dependencies and any(len(deps) > 0 for deps in dependencies.values()):
                print("  Dependencies:")
                for dep_type, deps in dependencies.items():
                    if deps:
                        deps_str = ", ".join(deps[:5])  # Limit to first 5
                        print(f"    - {dep_type}: {deps_str}")
            
            # Update progress for each file
            file_progress = 40 / min(5, len(py_files))  # Distribute remaining 40% among files
            progress.update(int(file_progress))
            
        except Exception as e:
            print(f"  Error analyzing file: {e}")
            logger.warning(f"Failed to analyze {file_path}: {e}")


def perform_detailed_analysis(project_name: str) -> None:
    """
    Perform more detailed analysis of the project.
    
    Args:
        project_name: Name of the registered project
    """
    print("\nRunning detailed analysis...")
    
    # Create context for progress reporting
    ctx = MCPContext()
    
    with ctx.progress_scope(100, "Performing detailed analysis") as progress:
        # Find TODOs and FIXMEs
        print("\nSearching for TODOs and FIXMEs...")
        try:
            todos = mcp.tools.find_text(
                project_name, 
                "TODO|FIXME", 
                use_regex=True,
                context_lines=1  # Include context lines
            )
            print(f"Found {len(todos)} TODOs/FIXMEs")
            
            for todo in todos[:5]:  # Limit to first 5
                print(f"  {todo['file']}:{todo['line']} - {todo['text']}")
                # Print context if available
                if "context" in todo and todo["context"]:
                    for ctx_line in todo["context"]:
                        if not ctx_line["is_match"]:  # Only show context, not the match itself
                            print(f"    {ctx_line['line']}: {ctx_line['text']}")
            
            progress.update(30)
            
        except Exception as e:
            print(f"Error searching for TODOs: {e}")
        
        # Find complex functions with AST-based analysis
        print("\nSearching for complex functions...")
        py_files = mcp.tools.list_files(project_name, extensions=["py"])
        
        complex_functions = []
        
        for file_path in py_files[:5]:  # Limit to first 5 files
            try:
                # Use the fixed complexity analysis functionality
                complexity = mcp.tools.analyze_complexity(project_name, file_path)
                
                # Now demonstrates additional metrics
                if complexity["cyclomatic_complexity"] > 5:
                    complex_functions.append({
                        "file": file_path,
                        "complexity": complexity["cyclomatic_complexity"],
                        "lines": complexity["line_count"],
                        "functions": complexity["function_count"],
                        "comment_ratio": complexity["comment_ratio"]
                    })
                    
                # Print detailed info for complex files
                if complexity["cyclomatic_complexity"] > 5:
                    print(f"  {file_path}:")
                    print(f"    - Complexity: {complexity['cyclomatic_complexity']}")
                    print(f"    - Line count: {complexity['line_count']}")
                    print(f"    - Function count: {complexity['function_count']}")
                    print(f"    - Comment ratio: {complexity['comment_ratio']:.1%}")
            except Exception as e:
                print(f"  Error analyzing complexity in {file_path}: {e}")
        
        progress.update(30)
        
        # Get AST for a complex file to demonstrate tree extraction
        if complex_functions:
            print("\nExtracting AST for a complex file...")
            complex_file = complex_functions[0]["file"]
            try:
                # Get AST using cursor-based traversal
                ast = mcp.tools.get_ast(
                    project=project_name, 
                    path=complex_file, 
                    max_depth=3  # Limit depth for readability
                )
                
                # Count nodes of different types
                node_types = {}
                
                def count_node_types(node):
                    if isinstance(node, dict) and "type" in node:
                        node_type = node["type"]
                        node_types[node_type] = node_types.get(node_type, 0) + 1
                        if "children" in node:
                            for child in node["children"]:
                                count_node_types(child)
                
                # Count node types in the AST
                count_node_types(ast["tree"])
                
                # Print node type counts
                print(f"  AST node types in {complex_file}:")
                for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"    - {node_type}: {count}")
                
            except Exception as e:
                print(f"  Error extracting AST: {e}")
        
        progress.update(40)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze a project with tree-sitter")
    parser.add_argument("project_path", help="Path to the project directory")
    parser.add_argument("--name", help="Optional project name (defaults to directory name)")
    parser.add_argument("--detailed", action="store_true", help="Perform detailed analysis")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="Set logging level")
    
    args = parser.parse_args()
    
    # Configure logging based on arguments
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Load configuration
    load_config()
    
    if not os.path.exists(args.project_path):
        print(f"Project path {args.project_path} does not exist")
        return 1
    
    try:
        # Main project analysis
        project_name = analyze_project(args.project_path, args.name)
        
        # Run detailed analysis if requested
        if args.detailed:
            perform_detailed_analysis(project_name)
        
        print("\nAnalysis completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.exception("Analysis failed")
        print(f"\nAnalysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
