"""
Example of using mcp-server-tree-sitter to analyze a project.
"""

import os
import logging
import sys
from pathlib import Path
import argparse

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the MCP server
from mcp_server_tree_sitter.server import mcp
from mcp_server_tree_sitter.config import load_config


# Configure logging
logging.basicConfig(level=logging.INFO)


def analyze_project(project_path: str, project_name: str = None):
    """Analyze a project using mcp-server-tree-sitter."""
    # Register the project
    if project_name is None:
        project_name = Path(project_path).name
        
    print(f"Registering project '{project_name}' at {project_path}")
    project_info = mcp.tools.register_project_tool(
        path=project_path, 
        name=project_name
    )
    
    # Print project info
    print(f"Project registered with {len(project_info['languages'])} languages:")
    for lang, count in project_info['languages'].items():
        print(f"  - {lang}: {count} files")
    
    # Analyze project structure
    print("\nAnalyzing project structure...")
    analysis = mcp.tools.analyze_project(project_name)
    
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
    
    # Find Python functions
    print("\nSearching for Python functions...")
    py_files = mcp.tools.list_files(project_name, extensions=["py"])
    
    for file_path in py_files[:5]:  # Limit to first 5 files for brevity
        print(f"\nAnalyzing {file_path}:")
        try:
            symbols = mcp.tools.get_symbols(project_name, file_path)
            
            if "functions" in symbols and symbols["functions"]:
                print("  Functions:")
                for func in symbols["functions"][:5]:  # Limit to first 5 functions
                    print(f"    - {func['name']}")
            
            if "classes" in symbols and symbols["classes"]:
                print("  Classes:")
                for cls in symbols["classes"][:5]:  # Limit to first 5 classes
                    print(f"    - {cls['name']}")
        except Exception as e:
            print(f"  Error analyzing file: {e}")
    
    # Return project name for further analysis
    return project_name


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze a project with tree-sitter")
    parser.add_argument("project_path", help="Path to the project directory")
    parser.add_argument("--name", help="Optional project name (defaults to directory name)")
    parser.add_argument("--detailed", action="store_true", help="Perform detailed analysis")
    
    args = parser.parse_args()
    
    # Load configuration
    load_config()
    
    if not os.path.exists(args.project_path):
        print(f"Project path {args.project_path} does not exist")
        return 1
    
    project_name = analyze_project(args.project_path, args.name)
    
    # Run detailed analysis if requested
    if args.detailed:
        print("\nRunning detailed analysis...")
        
        # Find TODOs
        print("\nSearching for TODOs and FIXMEs...")
        todos = mcp.tools.find_text(project_name, "TODO|FIXME", use_regex=True)
        print(f"Found {len(todos)} TODOs/FIXMEs")
        
        for todo in todos[:5]:  # Limit to first 5
            print(f"  {todo['file']}:{todo['line']} - {todo['text']}")
        
        # Find complex functions
        print("\nSearching for complex functions...")
        py_files = mcp.tools.list_files(project_name, extensions=["py"])
        
        for file_path in py_files[:3]:  # Limit to first 3 files
            try:
                complexity = mcp.tools.analyze_complexity(project_name, file_path)
                if complexity["cyclomatic_complexity"] > 5:
                    print(f"  {file_path} - complexity: {complexity['cyclomatic_complexity']}")
            except Exception as e:
                print(f"  Error analyzing complexity in {file_path}: {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
