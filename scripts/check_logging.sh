#!/bin/bash
# check_logging.sh - Script to spot check implementation patterns

grep -r ${1} . --exclude-dir=.venv --exclude-dir=.git --exclude-dir=./diagnostic_results --exclude-dir=./.pytest_cache --exclude-dir=./.ruff_cache --exclude-dir=./tests/__pycache__ --exclude=./.gitignore --exclude=./TODO.md --exclude=./FEATURES.md
