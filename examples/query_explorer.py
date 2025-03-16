"""
Example of using tree-sitter queries with mcp-server-tree-sitter.

This script demonstrates how to:
1. Register a project
2. List available query templates
3. Run queries on code files
4. Build custom queries
5. Find code patterns using queries
"""

import os
import logging
import sys
from pathlib import Path
import argparse
import json

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the MCP server
from mcp_server_tree_sitter.server import mcp
from mcp_server_tree_sitter.config import load_config


# Configure logging
logging.basicConfig(level=logging.INFO)


def explore_queries(project_path: str, language: str = None):
    """Explore query capabilities of tree-sitter."""
    # Register the project
    project_name = Path(project_path).name
    
    print(f"Registering project '{project_name}' at {project_path}")
    project_info = mcp.tools.register_project_tool(
        path=project_path, 
        name=project_name
    )
    
    # Detect language if not provided
    if not language:
        languages = list(project_info['languages'].keys())
        if not languages:
            print("No languages detected in project")
            return 1
        
        language = languages[0]
        print(f"Using detected language: {language}")
    
    # List available query templates
    print(f"\nAvailable query templates for {language}:")
    templates = mcp.tools.list_query_templates_tool(language)
    
    if language in templates:
        for template_name in templates[language]:
            print(f"  - {template_name}")
    else:
        print(f"No templates available for {language}")
        return 1
    
    # Get a specific template
    template_name = next(iter(templates[language].keys()))
    print(f"\nGetting template '{template_name}':")
    template = mcp.tools.get_query_template_tool(language, template_name)
    print(f"Query:\n{template['query']}")
    
    # Find files to query
    extensions = {"python": ["py"], "javascript": ["js"], "typescript": ["ts"]}.get(language, [])
    if not extensions:
        print(f"No known extensions for {language}")
        return 1
    
    files = mcp.tools.list_files(project_name, extensions=extensions)
    if not files:
        print(f"No {language} files found in project")
        return 1
    
    # Pick a file to analyze
    file_path = files[0]
    print(f"\nAnalyzing file: {file_path}")
    
    # Run the query
    print(f"Running query for '{template_name}':")
    results = mcp.tools.run_query(
        project=project_name,
        query=template['query'],
        file_path=file_path,
        max_results=5
    )
    
    # Print results
    print(f"Found {len(results)} matches:")
    for i, result in enumerate(results[:5]):
        capture = result['capture']
        text = result.get('text', '')
        location = f"({result['start']['row']}:{result['start']['column']})"
        print(f"  {i+1}. {capture} {location}: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    # Build a compound query
    print("\nBuilding a compound query:")
    if len(templates[language]) >= 2:
        template_names = list(templates[language].keys())[:2]
        print(f"Combining templates: {template_names}")
        
        compound = mcp.tools.build_query(
            language=language,
            patterns=template_names,
            combine="or"
        )
        
        # Run the compound query
        results = mcp.tools.run_query(
            project=project_name,
            query=compound['query'],
            file_path=file_path,
            max_results=5
        )
        
        print(f"Compound query found {len(results)} matches")
    
    # Find specific pattern
    print("\nSearching for a specific pattern:")
    if language == "python":
        # Find print statements
        pattern = """
        (call
          function: (identifier) @function
          (#eq? @function "print"))
        """
    elif language in ["javascript", "typescript"]:
        # Find console.log statements
        pattern = """
        (call_expression
          function: (member_expression
            object: (identifier) @object
            property: (property_identifier) @property)
          (#eq? @object "console")
          (#eq? @property "log"))
        """
    else:
        pattern = None
    
    if pattern:
        print(f"Pattern: {pattern}")
        results = mcp.tools.run_query(
            project=project_name,
            query=pattern,
            file_path=file_path
        )
        
        print(f"Found {len(results)} matches for specific pattern")
    
    # Get node types
    print(f"\nCommon node types for {language}:")
    node_types = mcp.tools.get_node_types(language)
    for i, (node_type, description) in enumerate(list(node_types.items())[:5]):
        print(f"  - {node_type}: {description}")
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Explore tree-sitter queries")
    parser.add_argument("project_path", help="Path to the project directory")
    parser.add_argument("--language", help="Language to use for queries")
    
    args = parser.parse_args()
    
    # Load configuration
    load_config()
    
    if not os.path.exists(args.project_path):
        print(f"Project path {args.project_path} does not exist")
        return 1
    
    return explore_queries(args.project_path, args.language)


if __name__ == "__main__":
    sys.exit(main())
