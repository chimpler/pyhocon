# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

pyhocon is a Python implementation of the HOCON (Human-Optimized Config Object Notation) parser. It parses HOCON configuration files into Python data structures and can convert to JSON, YAML, properties, and HOCON formats.

HOCON spec: https://github.com/typesafehub/config/blob/master/HOCON.md

## Commands

### Testing
```bash
# Run all tests
pytest tests/

# Run a specific test file
pytest tests/test_config_parser.py

# Run a specific test
pytest tests/test_config_parser.py::TestConfigParser::test_parse_simple_value

# Run with coverage
coverage run --source=pyhocon -m pytest tests/
coverage report -m
```

### Linting
```bash
flake8 pyhocon tests setup.py
```

### Tox (multi-environment testing)
```bash
tox                    # Run all environments
tox -e flake8          # Run flake8 only
tox -e py312           # Run tests on Python 3.12
```

### CLI Tool
```bash
# Convert HOCON to JSON
pyhocon -i input.conf -f json -o output.json
cat input.conf | pyhocon -f json

# Other formats: json, yaml, properties, hocon
# Use -c for compact output (nested single-value dicts as a.b.c = 1)
```

## Architecture

### Core Modules

- **config_parser.py** - Main parsing engine using pyparsing library
  - `ConfigFactory` - Public API for parsing (parse_file, parse_string, parse_URL, from_dict)
  - `ConfigParser` - Internal parser with HOCON grammar rules

- **config_tree.py** - Data structures
  - `ConfigTree` - Hierarchical config storage (extends OrderedDict), supports dot notation access (`config['a.b.c']`)
  - `ConfigList` - HOCON arrays
  - `ConfigValues` - Concatenated values (handles array/string/dict merging)
  - `ConfigSubstitution` - Represents `${var}` and `${?var}` substitutions

- **converter.py** - `HOCONConverter` with to_json, to_yaml, to_properties, to_hocon methods

- **period_parser.py / period_serializer.py** - Duration parsing (e.g., "5 days", "10 seconds")

- **tool.py** - CLI entry point

### Parsing Flow

1. `ConfigFactory.parse_*()` receives input
2. `ConfigParser.parse()` applies pyparsing grammar rules
3. Produces `ConfigTree`/`ConfigList` with unresolved `ConfigSubstitution` tokens
4. `resolve_substitutions()` replaces `${var}` references from config or environment variables
5. Returns resolved `ConfigTree`

### Key Features

- Substitutions: `${key}` (required) and `${?key}` (optional, fallback to env vars)
- Includes: `include "file.conf"`, `include url("http://...")`, `include required(file("..."))`, glob patterns
- Value access: `config['a.b.c']` or `config['a']['b']['c']` or `config.get_string('a.b.c')`
- Type-safe getters: `get_string()`, `get_int()`, `get_float()`, `get_bool()`, `get_list()`, `get_config()`

## Dependencies

- **pyparsing** (>=2, <4) - Grammar parsing
- **python-dateutil** (>=2.8.0, optional) - For months/years in duration parsing

## Test Dependencies

- pytest
- mock
- python-dateutil
- coveralls (for CI coverage reporting)
