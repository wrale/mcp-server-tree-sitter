# MCP Tree-sitter Server Tutorial

This tutorial will guide you through using the MCP Tree-sitter Server to analyze code with Claude, leveraging AST parsing, query execution, and structural analysis.

## Setup

First, make sure you have the server installed:

```bash
# Install the package using pip
pip install mcp-server-tree-sitter

# Or install from source
git clone https://github.com/wrale/mcp-server-tree-sitter.git
cd mcp-server-tree-sitter
make install
```

## Using with Claude Desktop

The easiest way to use the MCP Tree-sitter Server is to install it in Claude Desktop.

### Installing in Claude Desktop

```bash
# Use the MCP CLI to install the server
mcp install mcp_server_tree_sitter.server:mcp --name "tree_sitter"
```

This will make the server available in Claude Desktop as "tree_sitter". You'll see the MCP tools icon (hammer) in the interface once it's properly configured.

### Basic Usage with Claude

Once installed, you can use the server by asking Claude to analyze code. Here's a typical workflow:

1. **Register a Project**:
   ```
   Claude, please register a project at /path/to/my/project using the tree_sitter MCP tool register_project_tool.
   ```

2. **Explore Files**:
   ```
   What files are in this project? Can you list Python files using the list_files tool?
   ```

3. **Examine File Contents**:
   ```
   Show me the content of main.py using the get_file tool.
   ```

4. **Analyze Code Structure**:
   ```
   Can you analyze the structure of main.py? Extract all functions and classes using the get_symbols tool.
   ```

5. **Search for Patterns**:
   ```
   Find all function definitions that take more than 3 parameters using tree-sitter queries.
   ```

6. **Ask for Code Improvements**:
   ```
   Can you analyze the complexity of this file using analyze_complexity and suggest improvements?
   ```

## Advanced Usage Examples

### AST Analysis

Abstract Syntax Tree (AST) analysis allows Claude to understand code structure at a deeper level:

```
Claude, can you show me the AST for the main function in this file using the get_ast tool? 
Please limit the depth to 3 for readability.
```

The cursor-based AST traversal enables more efficient analysis of larger files and more complex structures.

### Tree-sitter Queries

Tree-sitter offers powerful queries to find specific patterns in code:

```
Claude, can you find all function calls to 'print' in this project? 
You can use the run_query tool with this query pattern:
(call function: (identifier) @func (#eq? @func "print"))
```

### Building Compound Queries

You can combine multiple query patterns for more sophisticated searches:

```
Claude, can you build a compound query to find both print statements and logging calls 
in my Python code? Use the build_query tool to combine patterns.
```

Claude can build a compound query using the `build_query` tool:

```
build_query(
    language="python",
    patterns=[
        '(call function: (identifier) @func (#eq? @func "print"))',
        '(call function: (attribute object: (identifier) @obj attribute: (identifier) @attr) (#eq? @obj "logging") (#eq? @attr "info"))'
    ],
    combine="or"
)
```

### Dependency Analysis

To understand code relationships, the dependency analysis tool now correctly extracts imports:

```
Claude, what external libraries does this file import? 
Use the get_dependencies tool to find all imports.
```

### Code Complexity Analysis

Use the complexity analysis tool to identify complex functions:

```
Claude, can you analyze the complexity of this file using analyze_complexity? 
Tell me about the cyclomatic complexity, line count, and comment ratio.
```

Claude can provide metrics including:
- Cyclomatic complexity
- Line count (total, code, comment)
- Comment ratio
- Function count and average size
- Class count

## Language Support

The server supports a wide range of programming languages through tree-sitter-language-pack:

- Python
- JavaScript/TypeScript
- Go
- Rust
- C/C++
- Swift
- Java/Kotlin
- Ruby
- And many more

For each language, specialized templates and queries are available. You can ask:

```
Claude, what languages are supported by the tree_sitter server? Use the list_languages tool.
```

## Project Analysis Strategies

### Breaking Down Large Projects

For large codebases:

```
Claude, this project is quite large. Can you first analyze the project structure 
using analyze_project, then focus on specific modules of interest?
```

Claude can segment analysis by:
1. Identifying key entry points
2. Finding core modules and dependencies
3. Exploring specific parts in depth

### Finding Patterns Across Files

For multi-file analysis:

```
Claude, can you find all uses of the database connection across the project? 
Look for imports of 'database' and any pattern accessing a connection object.
```

## Advanced Query Techniques

### Using Predicates in Queries

Tree-sitter queries support predicates for more powerful matching:

```
Claude, can you find functions with more than 3 parameters? Try a query with a predicate.
```

Example query with predicate:
```
(function_definition
  parameters: (parameters) @params
  (#match? @params ",.*,.*,"))
```

### Node Type Exploration

Understanding available node types helps build better queries:

```
Claude, what node types are available for JavaScript? Use the get_node_types tool.
```

### Adapting Queries Between Languages

When working with multiple languages:

```
Claude, I have a query for finding print statements in Python. Can you adapt it for JavaScript 
using the adapt_query tool?
```

## Best Practices

1. **Start with project overview** - Use `analyze_project` to get a high-level understanding of the codebase structure.

2. **Leverage symbol extraction** - `get_symbols` helps identify functions, classes, and imports in a file.

3. **Use specific queries** - Narrow down searches with specific tree-sitter queries rather than broad text searches.

4. **Visualize the AST** - Understanding the AST structure helps build better queries and understand code relationships.

5. **Use progress reporting** - For long-running tasks, use the MCPContext for progress reporting.

6. **Handle errors gracefully** - Wrap complex operations in try/except blocks to handle failures.

7. **Combine multiple tools** - Most powerful insights come from combining multiple analysis tools.

## Troubleshooting

**Issue**: Claude says it can't access files  
**Solution**: Ensure the project is registered correctly with an absolute path and permissions are correct.

**Issue**: AST parsing fails for large files  
**Solution**: Set a lower max_depth when calling get_ast to limit tree depth, or analyze specific parts of the file.

**Issue**: Queries return unexpected or no results  
**Solution**: Check the query syntax, or try a simpler query first. Ask Claude to explain and refine your query.

**Issue**: Analysis is slow for large projects  
**Solution**: Use more specific file patterns with `list_files`, specify extensions, or focus on specific directories.

## Example Analysis Workflow

Here's a complete example workflow for analyzing a new project:

```
1. Claude, register my project at /path/to/project using register_project_tool.

2. Give me an overview of the project structure using analyze_project.

3. List Python files in the 'src' directory using list_files.

4. Show me the content of src/main.py.

5. Analyze the structure of main.py - what functions and classes does it contain?

6. Find dependencies imported by main.py using get_dependencies.

7. Analyze the complexity of main.py using analyze_complexity.

8. Find all TODO comments in the project using find_text.

9. Use run_query to find all function calls to 'connect()' in the project.

10. Based on your analysis, what are the main entry points, and how do the components interact?
```

This structured approach helps Claude build a comprehensive understanding of the codebase.

## Additional Resources

- Run the examples in the examples directory: `python examples/basic_usage.py /path/to/project`
- Try the query explorer: `python examples/query_explorer.py /path/to/project --language python`
- Check the project README for detailed documentation

Happy coding!
