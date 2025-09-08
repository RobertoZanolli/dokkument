# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e .[dev]

# Install with enhanced features (optional)
pip install -e .[enhanced]
```

### Testing
```bash
# Run tests with coverage
pytest

# Run tests with verbose output
pytest --verbose

# Run specific test file
pytest tests/test_parser.py

# Run tests without coverage
pytest --disable-warnings -q

# Run single test with maximum failure limit
pytest --maxfail=1
```

### Code Quality
```bash
# Run linting
pylint -j 0 src/dokkument

# Run type checking
mypy src/dokkument

# Format code
black src/dokkument tests/

# Sort imports
isort src/dokkument tests/

# Check code style
flake8 src/dokkument
```

### Application Usage
```bash
# Run the application
dokkument

# List mode with different formats
dokkument --list
dokkument --list --format json
dokkument --list --format markdown

# Open specific links or all links
dokkument --open 1 3 5
dokkument --open-all

# Scan specific directory
dokkument --path /path/to/docs

# Show statistics and validate links
dokkument --stats
dokkument --validate
```

## Architecture Overview

### Core Design Patterns
- **Factory Pattern**: `DokkParserFactory` creates appropriate parsers for different file types
- **Command Pattern**: Modular command system in `commands.py` for extensible operations
- **Singleton Pattern**: `ConfigManager` provides global configuration management
- **Strategy Pattern**: Different export formats (text, JSON, Markdown, HTML)

### Key Components

#### Parser System (`parser.py`)
- `BaseParser`: Abstract base class for file parsers
- `StandardDokkParser`: Handles standard `.dokk` file format parsing
- `DokkParserFactory`: Factory to create appropriate parsers
- `DokkFileScanner`: Scans directories for `.dokk` files
- `DokkEntry`: Represents a single documentation link entry

#### Link Management (`link_manager.py`)
- `LinkManager`: Central component managing collections of links
- Handles scanning, filtering, statistics, validation, and export
- Manages color coding for files in terminal display
- Supports multiple export formats

#### User Interface (`cli_display.py`)
- `CLIDisplay`: Manages command-line interface with colors and formatting
- Auto-detects terminal capabilities (colors, hyperlinks)
- Cross-platform terminal support (Windows, macOS, Linux)

#### Configuration (`config_manager.py`)
- `ConfigManager`: Handles configuration loading and management
- Supports multiple config file locations
- JSON-based configuration with hierarchical settings

#### Main Application (`main.py`)
- `DokkumentApp`: Main application orchestration
- Handles different operation modes (interactive, list, open)
- Command-line argument parsing and processing

### File Structure
```
src/dokkument/
├── __init__.py         # Package initialization and main imports
├── main.py             # Entry point and application orchestration
├── parser.py           # .dokk file parsing with Factory pattern
├── link_manager.py     # Link collection management and operations
├── cli_display.py      # Terminal interface and formatting
├── config_manager.py   # Configuration management
├── commands.py         # Command pattern implementation
└── browser_opener.py   # Cross-platform browser opening
```

### .dokk File Format
The application parses `.dokk` files with this format:
```
"Link description" -> "https://example.com"
"API Documentation" -> "https://api.example.com/docs"
```
- One link per line
- Comments start with `#`
- Only HTTP/HTTPS URLs supported
- Empty lines ignored

### Configuration System
Configuration is loaded from multiple locations in order:
1. `.dokkument.json` (current directory)
2. `~/.dokkument.json` (home directory)
3. `~/.config/dokkument/config.json` (Linux/macOS)
4. `%APPDATA%/dokkument/config.json` (Windows)

Key configuration sections:
- `scanning`: Directory scanning behavior
- `display`: Terminal display preferences
- `browser`: Browser opening settings
- `security`: URL validation rules

### Testing Strategy
- Unit tests for core components (`tests/`)
- Pytest with coverage reporting
- Tests for parser, link manager, and CLI display
- Mock-based testing for external dependencies

### Dependencies
- **Core**: Uses only Python standard library (no mandatory external dependencies)
- **Optional Enhanced**: `rich`, `click`, `colorama` for better UX
- **Development**: `pytest`, `pylint`, `black`, `mypy`, `isort`, `flake8`