"""
Example of using tree-sitter queries with mcp-server-tree-sitter.

This script demonstrates how to:
1. Register a project
2. List available query templates
3. Run queries on code files
4. Build custom queries
5. Find code patterns using queries
6. Adapt queries across languages
7. Visualize and explore query results
"""

import os
import logging
import sys
from pathlib import Path
import argparse
import json
from typing import Dict, List, Any, Optional, Tuple

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the MCP server
from mcp_server_tree_sitter.server import mcp
from mcp_server_tree_sitter.config import load_config
from mcp_server_tree_sitter.utils.context import MCPContext


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def explore_queries(project_path: str, language: Optional[str] = None, output_dir: Optional[str] = None) -> int:
    """
    Explore query capabilities of tree-sitter.
    
    Args:
        project_path: Path to the project directory
        language: Language to use for queries (auto-detected if not provided)
        output_dir: Directory to save query results as JSON (optional)
        
    Returns:
        Exit code (0 for success)
    """
    # Create context for progress reporting
    ctx = MCPContext()
    
    with ctx.progress_scope(100, "Exploring tree-sitter queries") as progress:
        try:
            # Register the project
            project_name = Path(project_path).name
            
            print(f"Registering project '{project_name}' at {project_path}")
            project_info = mcp.tools.register_project_tool(
                path=project_path, 
                name=project_name,
                description="Project for query exploration"
            )
            
            progress.update(10)
            
            # Detect language if not provided
            if not language:
                languages = list(project_info['languages'].keys())
                if not languages:
                    print("No languages detected in project")
                    return 1
                
                language = languages[0]
                print(f"Using detected language: {language}")
            
            # Create output directory if specified
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            progress.update(10)
            
            # Explore the templates and queries
            templates = explore_templates(project_name, language, progress)
            
            progress.update(40)
            
            # Find files for analysis
            file_path = find_files_to_query(project_name, language)
            if not file_path:
                return 1
                
            progress.update(10)
            
            # Run queries
            results_data = run_queries(project_name, language, file_path, templates, progress)
            
            # Save results to file if output_dir is specified
            if output_dir and results_data:
                save_path = os.path.join(output_dir, f"{language}_query_results.json")
                with open(save_path, 'w') as f:
                    json.dump(results_data, f, indent=2)
                print(f"\nQuery results saved to {save_path}")
            
            return 0
            
        except KeyboardInterrupt:
            print("\nQuery exploration interrupted by user.")
            return 130
        except Exception as e:
            logger.exception("Query exploration failed")
            print(f"Error: {e}")
            return 1


def explore_templates(project_name: str, language: str, progress: Any) -> Dict[str, Any]:
    """
    Explore available query templates for a language.
    
    Args:
        project_name: Name of the project
        language: Language to explore
        progress: Progress scope for reporting
        
    Returns:
        Dictionary of templates
    """
    # List available query templates
    print(f"\nAvailable query templates for {language}:")
    try:
        templates = mcp.tools.list_query_templates_tool(language)
        
        if language in templates and templates[language]:
            for template_name in templates[language]:
                print(f"  - {template_name}")
        else:
            print(f"No templates available for {language}")
            return {}
        
        progress.update(10)
        
        # Get details for a few templates
        print("\nDetailed template examples:")
        selected_templates = {}
        
        for template_name in list(templates[language].keys())[:3]:  # Get details for up to 3 templates
            try:
                template = mcp.tools.get_query_template_tool(language, template_name)
                selected_templates[template_name] = template
                
                # Display template info
                print(f"\n### Template: {template_name} ###")
                print(f"Query:\n{template['query']}")
            except Exception as e:
                print(f"Error getting template '{template_name}': {e}")
        
        progress.update(10)
        
        return templates
        
    except Exception as e:
        print(f"Error exploring templates: {e}")
        return {}


def find_files_to_query(project_name: str, language: str) -> Optional[str]:
    """
    Find appropriate files in the project for querying.
    
    Args:
        project_name: Name of the project
        language: Language to find files for
        
    Returns:
        Path to a file for querying or None if no suitable files found
    """
    # Map languages to file extensions
    language_extensions = {
        "python": ["py"],
        "javascript": ["js"],
        "typescript": ["ts"],
        "go": ["go"],
        "rust": ["rs"],
        "c": ["c", "h"],
        "cpp": ["cpp", "hpp", "cc", "h"],
        "swift": ["swift"],
        "java": ["java"],
        "kotlin": ["kt"],
        "ruby": ["rb"],
    }
    
    extensions = language_extensions.get(language, [])
    if not extensions:
        print(f"No known extensions for {language}")
        return None
    
    try:
        # Find files with the appropriate extensions
        files = mcp.tools.list_files(project_name, extensions=extensions)
        
        if not files:
            print(f"No {language} files found in project")
            return None
        
        # Pick a file with reasonable content (not too small)
        selected_file = None
        for file_path in files:
            # Get file info
            file_info = mcp.tools.get_file_metadata(project_name, file_path)
            
            # Look for files with at least 10 lines
            if file_info.get("line_count", 0) > 10:
                selected_file = file_path
                break
        
        # If no suitable file found, use the first one
        if not selected_file and files:
            selected_file = files[0]
        
        print(f"\nSelected file for analysis: {selected_file}")
        
        # Print file content for reference
        try:
            content = mcp.tools.get_file(project_name, selected_file, max_lines=10)
            print("\nFile content preview:")
            print("```")
            print(content)
            if "..." not in content:
                print("...")
            print("```")
        except Exception as e:
            print(f"Error reading file: {e}")
        
        return selected_file
        
    except Exception as e:
        print(f"Error finding files: {e}")
        return None


def run_queries(
    project_name: str, 
    language: str, 
    file_path: str, 
    templates: Dict[str, Any],
    progress: Any
) -> Dict[str, Any]:
    """
    Run various queries on the selected file.
    
    Args:
        project_name: Name of the project
        language: Language for queries
        file_path: Path to the file to query
        templates: Query templates dictionary
        progress: Progress scope for reporting
        
    Returns:
        Dictionary with query results data
    """
    results_data = {
        "language": language,
        "file": file_path,
        "queries": {}
    }
    
    try:
        # Run a simple template query
        if language in templates and templates[language]:
            template_name = next(iter(templates[language].keys()))
            template = mcp.tools.get_query_template_tool(language, template_name)
            
            print(f"\nRunning query for '{template_name}':")
            results = mcp.tools.run_query(
                project=project_name,
                query=template['query'],
                file_path=file_path,
                max_results=10
            )
            
            # Save results data
            results_data["queries"][template_name] = {
                "query": template['query'],
                "results": results
            }
            
            # Print results
            print(f"Found {len(results)} matches:")
            for i, result in enumerate(results[:5]):  # Limit to first 5 for display
                capture = result['capture']
                text = result.get('text', '')
                location = f"(line {result['start']['row'] + 1}, col {result['start']['column'] + 1})"
                print(f"  {i+1}. {capture} {location}: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        progress.update(10)
        
        # Build and run a compound query
        print("\nBuilding a compound query:")
        if language in templates and len(templates[language]) >= 2:
            template_names = list(templates[language].keys())[:2]
            print(f"Combining templates: {template_names}")
            
            compound = mcp.tools.build_query(
                language=language,
                patterns=template_names,
                combine="or"
            )
            
            # Run the compound query
            compound_results = mcp.tools.run_query(
                project=project_name,
                query=compound['query'],
                file_path=file_path,
                max_results=10
            )
            
            # Save compound results
            results_data["queries"]["compound"] = {
                "templates": template_names,
                "query": compound['query'],
                "results": compound_results
            }
            
            print(f"Compound query found {len(compound_results)} matches")
            
            # Show new matches that weren't in the first query
            if results and compound_results:
                # Extract node text from first query results
                original_texts = set()
                for result in results:
                    if 'text' in result:
                        original_texts.add(result['text'])
                
                # Find new results
                new_results = []
                for result in compound_results:
                    if 'text' in result and result['text'] not in original_texts:
                        new_results.append(result)
                
                if new_results:
                    print(f"New matches from compound query:")
                    for i, result in enumerate(new_results[:3]):  # Show up to 3 new matches
                        capture = result['capture']
                        text = result.get('text', '')
                        print(f"  {i+1}. {capture}: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        progress.update(10)
        
        # Run language-specific pattern query
        print("\nSearching for a language-specific pattern:")
        pattern = None
        pattern_description = ""
        
        # Define language-specific patterns
        language_patterns = {
            "python": {
                "pattern": """
                (call
                  function: (identifier) @function
                  (#eq? @function "print"))
                """,
                "description": "print() statements"
            },
            "javascript": {
                "pattern": """
                (call_expression
                  function: (member_expression
                    object: (identifier) @object
                    property: (property_identifier) @property)
                  (#eq? @object "console")
                  (#eq? @property "log"))
                """,
                "description": "console.log() statements"
            },
            "typescript": {
                "pattern": """
                (call_expression
                  function: (member_expression
                    object: (identifier) @object
                    property: (property_identifier) @property)
                  (#eq? @object "console")
                  (#eq? @property "log"))
                """,
                "description": "console.log() statements"
            },
            "go": {
                "pattern": """
                (call_expression
                  function: (selector_expression
                    operand: (identifier) @package
                    field: (field_identifier) @func)
                  (#eq? @package "fmt")
                  (#match? @func "^Print"))
                """,
                "description": "fmt.Print* statements"
            },
            "rust": {
                "pattern": """
                (macro_invocation
                  macro: (identifier) @macro
                  (#match? @macro "^print"))
                """,
                "description": "print! and println! macros"
            }
        }
        
        if language in language_patterns:
            pattern = language_patterns[language]["pattern"]
            pattern_description = language_patterns[language]["description"]
        
        if pattern:
            print(f"Searching for {pattern_description}:")
            print(f"Pattern: {pattern}")
            
            pattern_results = mcp.tools.run_query(
                project=project_name,
                query=pattern,
                file_path=file_path,
                max_results=5
            )
            
            # Save pattern results
            results_data["queries"]["custom_pattern"] = {
                "description": pattern_description,
                "query": pattern,
                "results": pattern_results
            }
            
            print(f"Found {len(pattern_results)} matches for {pattern_description}")
            
            # Show the matches
            for i, result in enumerate(pattern_results[:3]):  # Show up to 3 matches
                capture = result['capture']
                text = result.get('text', '')
                location = f"(line {result['start']['row'] + 1})"
                print(f"  {i+1}. {capture} {location}: {text}")
        
        progress.update(10)
        
        # Demonstrate adapting queries between languages
        print("\nDemonstrating query adaptation between languages:")
        
        # Define source language and target language
        source_lang = language
        target_langs = ["python", "javascript", "typescript", "go", "rust"]
        target_langs = [lang for lang in target_langs if lang != source_lang][:2]  # Pick up to 2 different languages
        
        if target_langs and pattern:
            for target_lang in target_langs:
                try:
                    # Adapt the query
                    adapted = mcp.tools.adapt_query(
                        query=pattern,
                        from_language=source_lang,
                        to_language=target_lang
                    )
                    
                    # Save adaptation results
                    results_data["queries"][f"adapted_to_{target_lang}"] = {
                        "original_query": pattern,
                        "adapted_query": adapted["adapted_query"],
                        "from_language": source_lang,
                        "to_language": target_lang
                    }
                    
                    print(f"\nAdapted query from {source_lang} to {target_lang}:")
                    print(f"Original: {pattern.strip()}")
                    print(f"Adapted: {adapted['adapted_query'].strip()}")
                except Exception as e:
                    print(f"Error adapting query to {target_lang}: {e}")
        
        progress.update(10)
        
        # Get node types to understand the language grammar
        print(f"\nCommon node types for {language}:")
        try:
            node_types = mcp.tools.get_node_types(language)
            
            # Save node types
            results_data["node_types"] = node_types
            
            # Print some node types
            for i, (node_type, description) in enumerate(list(node_types.items())[:7]):
                print(f"  - {node_type}: {description}")
        except Exception as e:
            print(f"Error getting node types: {e}")
        
        progress.update(10)
        
        return results_data
        
    except Exception as e:
        print(f"Error running queries: {e}")
        logger.exception("Query execution failed")
        return results_data


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Explore tree-sitter queries")
    parser.add_argument("project_path", help="Path to the project directory")
    parser.add_argument("--language", help="Language to use for queries")
    parser.add_argument("--output", help="Directory to save query results as JSON")
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
    
    return explore_queries(args.project_path, args.language, args.output)


if __name__ == "__main__":
    sys.exit(main())
