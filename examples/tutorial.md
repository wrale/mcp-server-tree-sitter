# MCP Tree-sitter Server Tutorial

This tutorial will guide you through using the MCP Tree-sitter Server to analyze code with Claude.

## Setup

First, make sure you have the server installed:

```bash
# Install the package
pip install mcp-server-tree-sitter

# Or install from source
git clone https://github.com/organization/mcp-server-tree-sitter.git
cd mcp-server-tree-sitter
make install
```

## Using with Claude Desktop

The easiest way to use the MCP Tree-sitter Server is to install it in Claude Desktop.

### Installing in Claude Desktop

```bash
mcp install mcp_server_tree_sitter.server:mcp --name "Code Explorer"
```

This will make the server available in Claude Desktop as "Code Explorer".

### Basic Usage with Claude

Once installed, you can use the server by asking Claude to analyze code. Here's a typical workflow:

1. **Register a Project**:
   ```
   Claude, please register a project at /path/to/my/project using the Code Explorer.
   ```

2. **Explore Files**:
   ```
   What files are in this project? Can you list Python files?
   ```

3. **Examine File Contents**:
   ```
   Show me the content of main.py
   ```

4. **Analyze Code Structure**:
   ```
   Can you analyze the structure of main.py? What functions and classes does it contain?
   ```

5. **Search for Patterns**:
   ```
   Find all function definitions that take more than 3 parameters.
   ```

6. **Ask for Code Improvements**:
   ```
   Can you suggest improvements for this file?
   ```

## Advanced Usage Examples

### Tree-sitter Queries

Tree-sitter allows powerful queries to find specific patterns in code. Here's how to use them:

```
Claude, can you find all function calls to 'print' in this project?
```

Claude might use a query like:
```
(call
  function: (identifier) @func
  (#eq? @func "print"))
```

### Code Complexity Analysis

You can ask Claude to analyze code complexity:

```
Claude, what's the complexity of this file? Are there any functions that are too complex?
```

Claude can provide metrics like cyclomatic complexity, lines of code, and function length.

### Finding Dependencies

To understand code relationships:

```
Claude, what external libraries does this project depend on?
```

or

```
What other modules does this file import?
```

## Tips for Effective Use

1. **Be specific about what you're looking for** - The more specific your request, the better Claude can use the tools.

2. **Start with project registration** - Always register your project first before analyzing code.

3. **Use incremental exploration** - Start with high-level overview, then drill down into specific areas of interest.

4. **Ask for explanations** - Claude can explain complex code structures by using the AST to understand relationships.

5. **Try different query patterns** - If you're not finding what you want, try a different way of describing the code pattern.

## Troubleshooting

**Issue**: Claude says it can't access files
**Solution**: Make sure you've registered the project correctly and the path is accessible.

**Issue**: Queries return unexpected results
**Solution**: Tree-sitter queries have specific syntax. Ask Claude to explain and refine your query.

**Issue**: Analysis is slow for large projects
**Solution**: Try limiting the scope of analysis to specific directories or file types.

## Next Steps

As you get comfortable with the basics, try:

1. Using tree-sitter queries to find complex patterns
2. Analyzing codebase architecture across multiple files
3. Getting suggestions for code refactoring
4. Having Claude explain complex algorithms using the AST

Happy coding!
