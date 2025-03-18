"""Tests for Rust compatibility in the Tree-sitter server."""

import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from tests.test_helpers import (
    get_ast,
    get_dependencies,
    get_symbols,
    register_project_tool,
    run_query,
)


@pytest.fixture
def rust_project(request) -> Generator[Dict[str, Any], None, None]:
    """Create a test project with Rust files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create a simple Rust file
        main_rs = project_path / "main.rs"
        with open(main_rs, "w") as f:
            f.write(
                """
use std::io;
use std::collections::HashMap;

struct Person {
    name: String,
    age: u32,
}

impl Person {
    fn new(name: &str, age: u32) -> Person {
        Person {
            name: String::from(name),
            age,
        }
    }

    fn greet(&self) -> String {
        format!("Hello, my name is {} and I'm {} years old.", self.name, self.age)
    }
}

fn calculate_ages(people: &Vec<Person>) -> HashMap<String, u32> {
    let mut ages = HashMap::new();
    for person in people {
        ages.insert(person.name.clone(), person.age);
    }
    ages
}

fn main() {
    println!("Rust Sample Program");

    let mut people = Vec::new();
    people.push(Person::new("Alice", 30));
    people.push(Person::new("Bob", 25));

    for person in &people {
        println!("{}", person.greet());
    }

    let ages = calculate_ages(&people);
    println!("Ages: {:?}", ages);
}
"""
            )

        # Create a library file
        lib_rs = project_path / "lib.rs"
        with open(lib_rs, "w") as f:
            f.write(
                """
use std::fs;
use std::fs::File;
use std::io::{self, Read, Write};
use std::path::Path;

pub struct FileHandler {
    base_path: String,
}

impl FileHandler {
    pub fn new(base_path: &str) -> FileHandler {
        FileHandler {
            base_path: String::from(base_path),
        }
    }

    pub fn read_file(&self, filename: &str) -> Result<String, io::Error> {
        let path = format!("{}/{}", self.base_path, filename);
        fs::read_to_string(path)
    }

    pub fn write_file(&self, filename: &str, content: &str) -> Result<(), io::Error> {
        let path = format!("{}/{}", self.base_path, filename);
        let mut file = File::create(path)?;
        file.write_all(content.as_bytes())?;
        Ok(())
    }
}

pub fn list_files(dir: &str) -> Result<Vec<String>, io::Error> {
    let mut files = Vec::new();
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_file() {
            if let Some(filename) = path.file_name() {
                if let Some(name) = filename.to_str() {
                    files.push(String::from(name));
                }
            }
        }
    }
    Ok(files)
}
"""
            )

        # Generate a unique project name based on the test name
        test_name = request.node.name
        unique_id = abs(hash(test_name)) % 10000
        project_name = f"rust_test_project_{unique_id}"

        # Register project with retry mechanism
        try:
            register_project_tool(path=str(project_path), name=project_name)
        except Exception:
            # If registration fails, try with an even more unique name
            project_name = f"rust_test_project_{unique_id}_{int(time.time())}"
            register_project_tool(path=str(project_path), name=project_name)

        yield {
            "name": project_name,
            "path": str(project_path),
            "files": ["main.rs", "lib.rs"],
        }


def test_rust_ast_parsing(rust_project) -> None:
    """Test that Rust code can be parsed into an AST correctly."""
    # Get AST for main.rs
    ast_result = get_ast(
        project=rust_project["name"],
        path="main.rs",
        max_depth=5,
        include_text=True,
    )

    # Verify AST structure
    assert "tree" in ast_result, "AST result should contain a tree"
    assert "language" in ast_result, "AST result should contain language info"
    assert ast_result["language"] == "rust", "Language should be identified as Rust"

    # Check tree has the expected structure
    tree = ast_result["tree"]
    assert tree["type"] == "source_file", "Root node should be a source_file"
    assert "children" in tree, "Tree should have children"

    # Look for key Rust constructs in the AST
    structs_found = []
    functions_found = []
    impl_blocks_found = []

    def find_nodes(node, node_types) -> None:
        if isinstance(node, dict) and "type" in node:
            if node["type"] == "struct_item":
                if "children" in node:
                    for child in node["children"]:
                        if child.get("type") == "type_identifier":
                            structs_found.append(child.get("text", ""))
            elif node["type"] == "function_item":
                if "children" in node:
                    for child in node["children"]:
                        if child.get("type") == "identifier":
                            functions_found.append(child.get("text", ""))
            elif node["type"] == "impl_item":
                impl_blocks_found.append(node)

            if "children" in node:
                for child in node["children"]:
                    find_nodes(child, node_types)

    find_nodes(tree, ["struct_item", "function_item", "impl_item"])

    # Check for Person struct - handle both bytes and strings
    person_found = False
    for name in structs_found:
        if (isinstance(name, bytes) and b"Person" in name) or (isinstance(name, str) and "Person" in name):
            person_found = True
            break
    assert person_found, "Should find Person struct"
    # Check for main and calculate_ages functions - handle both bytes and strings
    main_found = False
    calc_found = False
    for name in functions_found:
        if (isinstance(name, bytes) and b"main" in name) or (isinstance(name, str) and "main" in name):
            main_found = True
        if (isinstance(name, bytes) and b"calculate_ages" in name) or (
            isinstance(name, str) and "calculate_ages" in name
        ):
            calc_found = True

    assert main_found, "Should find main function"
    assert calc_found, "Should find calculate_ages function"
    assert len(impl_blocks_found) > 0, "Should find impl blocks"


def test_rust_symbol_extraction(rust_project) -> None:
    """Test that symbols can be extracted from Rust code."""
    # Get symbols for main.rs
    symbols = get_symbols(project=rust_project["name"], file_path="main.rs")

    # Verify structure of symbols
    assert "structs" in symbols, "Symbols should include structs"
    assert "functions" in symbols, "Symbols should include functions"
    assert "imports" in symbols, "Symbols should include imports"

    # Check for specific symbols we expect
    struct_names = [s.get("name", "") for s in symbols.get("structs", [])]
    function_names = [f.get("name", "") for f in symbols.get("functions", [])]

    # Check for Person struct - handle both bytes and strings
    person_found = False
    for name in struct_names:
        if (isinstance(name, bytes) and b"Person" in name) or (isinstance(name, str) and "Person" in name):
            person_found = True
            break
    assert person_found, "Should find Person struct"
    # Check for main and calculate_ages functions - handle both bytes and strings
    main_found = False
    calc_found = False
    for name in function_names:
        if (isinstance(name, bytes) and b"main" in name) or (isinstance(name, str) and "main" in name):
            main_found = True
        if (isinstance(name, bytes) and b"calculate_ages" in name) or (
            isinstance(name, str) and "calculate_ages" in name
        ):
            calc_found = True

    assert main_found, "Should find main function"
    assert calc_found, "Should find calculate_ages function"


def test_rust_dependency_analysis(rust_project) -> None:
    """Test that dependencies can be identified in Rust code."""
    # Get dependencies for main.rs
    dependencies = get_dependencies(project=rust_project["name"], file_path="main.rs")

    # Verify dependencies structure
    assert isinstance(dependencies, dict), "Dependencies should be a dictionary"

    # Check for standard library dependencies
    all_deps = str(dependencies)  # Convert to string for easy checking
    assert "std::io" in all_deps, "Should find std::io dependency"
    assert "std::collections::HashMap" in all_deps, "Should find HashMap dependency"


def test_rust_specific_queries(rust_project) -> None:
    """Test that Rust-specific queries can be executed on the AST."""
    # Define a query to find struct definitions
    struct_query = """
    (struct_item
      name: (type_identifier) @struct.name
      body: (field_declaration_list) @struct.body
    ) @struct.def
    """

    # Run the query
    struct_results = run_query(
        project=rust_project["name"],
        query=struct_query,
        file_path="main.rs",
        language="rust",
    )

    # Verify results
    assert isinstance(struct_results, list), "Query results should be a list"
    assert len(struct_results) > 0, "Should find at least one struct"

    # Check for Person struct
    person_found = False
    for result in struct_results:
        if result.get("capture") == "struct.name" and result.get("text") == "Person":
            person_found = True
            break

    assert person_found, "Should find Person struct in query results"

    # Define a query to find impl blocks
    impl_query = """
    (impl_item
      trait: (type_identifier)? @impl.trait
      type: (type_identifier) @impl.type
      body: (declaration_list) @impl.body
    ) @impl.def
    """

    # Run the query
    impl_results = run_query(
        project=rust_project["name"],
        query=impl_query,
        file_path="main.rs",
        language="rust",
    )

    # Verify results
    assert isinstance(impl_results, list), "Query results should be a list"
    assert len(impl_results) > 0, "Should find at least one impl block"

    # Check for Person impl
    person_impl_found = False
    for result in impl_results:
        if result.get("capture") == "impl.type" and result.get("text") == "Person":
            person_impl_found = True
            break

    assert person_impl_found, "Should find Person impl in query results"


def test_rust_trait_and_macro_handling(rust_project) -> None:
    """Test handling of Rust-specific constructs like traits and macros."""
    # Create a file with traits and macros
    trait_file = Path(rust_project["path"]) / "traits.rs"
    with open(trait_file, "w") as f:
        f.write(
            """
pub trait Display {
    fn display(&self) -> String;
}

pub trait Calculate {
    fn calculate(&self) -> f64;
}

// Implement both traits for a struct
pub struct Value {
    pub x: f64,
    pub y: f64,
}

impl Display for Value {
    fn display(&self) -> String {
        format!("Value({}, {})", self.x, self.y)
    }
}

impl Calculate for Value {
    fn calculate(&self) -> f64 {
        self.x * self.y
    }
}

// A macro
macro_rules! create_value {
    ($x:expr, $y:expr) => {
        Value { x: $x, y: $y }
    };
}

fn main() {
    let v = create_value!(2.5, 3.0);
    println!("{}: {}", v.display(), v.calculate());
}
"""
        )

    # Get AST for this file
    ast_result = get_ast(
        project=rust_project["name"],
        path="traits.rs",
        max_depth=5,
        include_text=True,
    )

    # Look for trait definitions and macro rules
    traits_found = []
    macros_found = []

    def find_specific_nodes(node) -> None:
        if isinstance(node, dict) and "type" in node:
            if node["type"] == "trait_item":
                if "children" in node:
                    for child in node["children"]:
                        if child.get("type") == "type_identifier":
                            traits_found.append(child.get("text", ""))
            elif node["type"] == "macro_definition":
                if "children" in node:
                    for child in node["children"]:
                        if child.get("type") == "identifier":
                            macros_found.append(child.get("text", ""))

            if "children" in node:
                for child in node["children"]:
                    find_specific_nodes(child)

    find_specific_nodes(ast_result["tree"])

    # Check for Display and Calculate traits, and create_value macro - handle both bytes and strings
    display_found = False
    calculate_found = False
    macro_found = False

    for name in traits_found:
        if (isinstance(name, bytes) and b"Display" in name) or (isinstance(name, str) and "Display" in name):
            display_found = True
        if (isinstance(name, bytes) and b"Calculate" in name) or (isinstance(name, str) and "Calculate" in name):
            calculate_found = True

    for name in macros_found:
        if (isinstance(name, bytes) and b"create_value" in name) or (isinstance(name, str) and "create_value" in name):
            macro_found = True

    assert display_found, "Should find Display trait"
    assert calculate_found, "Should find Calculate trait"
    assert macro_found, "Should find create_value macro"
