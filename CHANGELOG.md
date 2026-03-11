# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Removed

- **Configuration**: The deprecated `language.auto_install` field has been removed from `ServerConfig`. It was unused (the server uses tree-sitter-language-pack). If your `config.yaml` still contains `language.auto_install`, you can delete that key; existing YAML files that include it will continue to load (the key is ignored).
