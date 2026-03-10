# Language coverage

This project uses [tree-sitter-language-pack](https://pypi.org/project/tree-sitter-language-pack/) (>=0.13.0) for parsing. The pack provides **165+** tree-sitter languages. Below we track which of those languages have extra support in this server:

- **Templates**: query templates in `src/mcp_server_tree_sitter/language/templates/` (e.g. functions, classes, imports) used by tools like `run_query` and symbol extraction.
- **get_enclosing_scope**: scope node types defined in `scope_node_types_data.py` so the `get_enclosing_scope` tool returns function/class/module scope for a given position.

We add support for more languages over time and update this table as we go.

**Legend:** ✅ = supported, ❌ = not yet. **Bold** = widely used mainstream language (general-purpose, web, or common config/data formats).

| Language (pack key) | Templates | get_enclosing_scope |
|---------------------|-----------|---------------------|
| actionscript        | ❌         | ❌                   |
| ada                 | ❌         | ❌                   |
| agda                | ❌         | ❌                   |
| apl                 | ✅         | ❌                   |
| apex                | ❌         | ❌                   |
| arduino             | ❌         | ❌                   |
| asm                 | ❌         | ❌                   |
| astro               | ❌         | ❌                   |
| **bash**            | ❌         | ❌                   |
| beancount           | ❌         | ❌                   |
| bibtex              | ❌         | ❌                   |
| bicep               | ❌         | ❌                   |
| bitbake             | ❌         | ❌                   |
| bsl                 | ❌         | ❌                   |
| **c**               | ✅         | ✅                   |
| cairo               | ❌         | ❌                   |
| capnp               | ❌         | ❌                   |
| chatito             | ❌         | ❌                   |
| clarity             | ❌         | ❌                   |
| clojure             | ❌         | ❌                   |
| cmake               | ❌         | ❌                   |
| cobol               | ❌         | ❌                   |
| comment             | ❌         | ❌                   |
| commonlisp          | ❌         | ❌                   |
| cpon                | ❌         | ❌                   |
| **cpp**             | ✅         | ✅                   |
| **csharp**          | ❌         | ❌                   |
| **css**             | ❌         | ❌                   |
| csv                 | ❌         | ❌                   |
| cuda                | ❌         | ❌                   |
| d                   | ❌         | ❌                   |
| dart                | ❌         | ❌                   |
| dockerfile          | ❌         | ❌                   |
| doxygen             | ❌         | ❌                   |
| dtd                 | ❌         | ❌                   |
| elisp               | ❌         | ❌                   |
| elixir              | ❌         | ❌                   |
| elm                 | ❌         | ❌                   |
| embeddedtemplate    | ❌         | ❌                   |
| erlang              | ❌         | ❌                   |
| fennel              | ❌         | ❌                   |
| firrtl              | ❌         | ❌                   |
| fish                | ❌         | ❌                   |
| fortran             | ❌         | ❌                   |
| fsharp              | ❌         | ❌                   |
| func                | ❌         | ❌                   |
| gdscript            | ❌         | ❌                   |
| gitattributes       | ❌         | ❌                   |
| gitcommit           | ❌         | ❌                   |
| gitignore           | ❌         | ❌                   |
| gleam               | ❌         | ❌                   |
| glsl                | ❌         | ❌                   |
| gn                  | ❌         | ❌                   |
| **go**              | ✅         | ✅                   |
| gomod               | ❌         | ❌                   |
| gosum               | ❌         | ❌                   |
| graphql             | ❌         | ❌                   |
| groovy              | ❌         | ❌                   |
| gstlaunch           | ❌         | ❌                   |
| hack                | ❌         | ❌                   |
| hare                | ❌         | ❌                   |
| **haskell**         | ❌         | ❌                   |
| haxe                | ❌         | ❌                   |
| hcl                 | ❌         | ❌                   |
| heex                | ❌         | ❌                   |
| hlsl                | ❌         | ❌                   |
| **html**            | ❌         | ❌                   |
| hyprlang            | ❌         | ❌                   |
| ini                 | ❌         | ❌                   |
| ispc                | ❌         | ❌                   |
| janet               | ❌         | ❌                   |
| **java**            | ✅         | ✅                   |
| **javascript**      | ✅         | ✅                   |
| jsdoc               | ❌         | ❌                   |
| **json**            | ❌         | ❌                   |
| jsonnet             | ❌         | ❌                   |
| **julia**           | ✅         | ✅                   |
| kconfig             | ❌         | ❌                   |
| kdl                 | ❌         | ❌                   |
| **kotlin**          | ✅         | ✅                   |
| latex               | ❌         | ❌                   |
| linkerscript        | ❌         | ❌                   |
| llvm                | ❌         | ❌                   |
| **lua**             | ❌         | ❌                   |
| luadoc              | ❌         | ❌                   |
| luap                | ❌         | ❌                   |
| luau                | ❌         | ❌                   |
| magik               | ❌         | ❌                   |
| make                | ❌         | ❌                   |
| **markdown**        | ❌         | ❌                   |
| markdown_inline     | ❌         | ❌                   |
| matlab              | ❌         | ❌                   |
| mermaid             | ❌         | ❌                   |
| meson               | ❌         | ❌                   |
| netlinx             | ❌         | ❌                   |
| nim                 | ❌         | ❌                   |
| ninja               | ❌         | ❌                   |
| nix                 | ❌         | ❌                   |
| nqc                 | ❌         | ❌                   |
| **objc**            | ❌         | ❌                   |
| ocaml               | ❌         | ❌                   |
| odin                | ❌         | ❌                   |
| org                 | ❌         | ❌                   |
| pascal              | ❌         | ❌                   |
| pem                 | ❌         | ❌                   |
| **perl**            | ❌         | ❌                   |
| pgn                 | ❌         | ❌                   |
| **php**             | ❌         | ❌                   |
| po                  | ❌         | ❌                   |
| pony                | ❌         | ❌                   |
| powershell          | ❌         | ❌                   |
| printf              | ❌         | ❌                   |
| prisma              | ❌         | ❌                   |
| properties          | ❌         | ❌                   |
| proto               | ❌         | ❌                   |
| psv                 | ❌         | ❌                   |
| puppet              | ❌         | ❌                   |
| purescript          | ❌         | ❌                   |
| pymanifest          | ❌         | ❌                   |
| **python**          | ✅         | ✅                   |
| qmldir              | ❌         | ❌                   |
| qmljs               | ❌         | ❌                   |
| query               | ❌         | ❌                   |
| **r**               | ❌         | ❌                   |
| racket              | ❌         | ❌                   |
| rbs                 | ❌         | ❌                   |
| re2c                | ❌         | ❌                   |
| readline            | ❌         | ❌                   |
| rego                | ❌         | ❌                   |
| requirements        | ❌         | ❌                   |
| ron                 | ❌         | ❌                   |
| rst                 | ❌         | ❌                   |
| **ruby**            | ❌         | ❌                   |
| **rust**            | ✅         | ✅                   |
| **scala**           | ❌         | ❌                   |
| scheme              | ❌         | ❌                   |
| **scss**            | ❌         | ❌                   |
| slang               | ❌         | ❌                   |
| smali               | ❌         | ❌                   |
| smithy              | ❌         | ❌                   |
| solidity            | ❌         | ❌                   |
| sparql              | ❌         | ❌                   |
| **sql**             | ❌         | ❌                   |
| squirrel            | ❌         | ❌                   |
| starlark            | ❌         | ❌                   |
| svelte              | ❌         | ❌                   |
| **swift**           | ✅         | ✅                   |
| tablegen            | ❌         | ❌                   |
| tcl                 | ❌         | ❌                   |
| test                | ❌         | ❌                   |
| thrift              | ❌         | ❌                   |
| toml                | ❌         | ❌                   |
| tsv                 | ❌         | ❌                   |
| tsx                 | ❌         | ❌                   |
| twig                | ❌         | ❌                   |
| **typescript**      | ✅         | ✅                   |
| typst               | ❌         | ❌                   |
| udev                | ❌         | ❌                   |
| ungrammar           | ❌         | ❌                   |
| uxntal              | ❌         | ❌                   |
| v                   | ❌         | ❌                   |
| verilog             | ❌         | ❌                   |
| vhdl                | ❌         | ❌                   |
| vim                 | ❌         | ❌                   |
| vue                 | ❌         | ❌                   |
| wast                | ❌         | ❌                   |
| wat                 | ❌         | ❌                   |
| wgsl                | ❌         | ❌                   |
| xcompose            | ❌         | ❌                   |
| **xml**             | ❌         | ❌                   |
| **yaml**            | ❌         | ❌                   |
| yuck                | ❌         | ❌                   |
| zig                 | ❌         | ❌                   |

## Summary

- **Templates**: 12 languages (apl, c, cpp, go, java, javascript, julia, kotlin, python, rust, swift, typescript).
- **get_enclosing_scope**: 11 languages (c, cpp, go, java, javascript, julia, kotlin, python, rust, swift, typescript).

Languages available in the pack but not listed above (e.g. `fsharp_signature`, `ocaml_interface`) can be added to the table when we add support for them.
