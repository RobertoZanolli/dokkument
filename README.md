# dokkument

**CLI Manager for corporate documentation via .dokk files**
[![CI](https://github.com/RobertoZanolli/dokkument/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/RobertoZanolli/dokkument/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.0.0-red)

`dokkument` is a command-line application that allows you to manage and quickly access corporate documentation using `.dokk` files containing organized links. Perfect for development teams, sysadmins, and companies that need quick access to distributed documentation resources.

## 🚀 Features

- **🔍 Automatic scanning** of `.dokk` files in the current directory and subdirectories
- **🎨 Colored interface** with support for clickable links in compatible terminals
- **🌍 Intelligent browser opening** cross-platform (Windows, macOS, Linux)
- **⚙️ Flexible configuration** with customizable JSON files
- **📤 Export** in multiple formats (text, Markdown, HTML, JSON)
- **✅ URL validation** to ensure link correctness
- **🔧 Zero external dependencies** - uses only Python standard libraries

## 📦 Installation

### Quick Installation

```bash
pip install dokkument
```

### Installation from source

```bash
git clone https://github.com/your-username/dokkument.git
cd dokkument
pip install -e .
```

### Installation with advanced features (optional)

```bash
pip install "dokkument[enhanced]"  # Includes rich, click, colorama for better UX
```

## 📖 .dokk file format

The `.dokk` files use a simple and readable format:

```
# Comments start with #
"Link description" -> "https://link.com"
"API Documentation" -> "https://api.example.com/docs"
"GitLab Repository" -> "https://gitlab.com/company/project"
"Monitoring Dashboard" -> "https://grafana.example.com"
```

### Format rules:
- One line per entry
- Format: `"Description" -> "URL"`
- Empty lines and comments (`#`) are ignored
- Only HTTP/HTTPS URLs are supported

## 🚀 Usage

### Interactive mode (default)

```bash
dokkument
```

Scans the current directory for `.dokk` files and presents an interactive menu.

### List mode

```bash
dokkument --list                 # Textual list
dokkument --list --format json   # JSON output
dokkument --list --format markdown  # Markdown output
```

### Direct opening

```bash
dokkument --open-all             # Opens all links
dokkument --open 1 3 5           # Opens links 1, 3, and 5
```

### Scan specific directory

```bash
dokkument --path /docs           # Scan specific directory
dokkument --path /docs --no-recursive  # Non-recursive
```

### Statistics and validation

```bash
dokkument --stats                # Show statistics
dokkument --validate             # Validate all links
```

## ⚙️ Configuration

### Configuration file

dokkument automatically looks for configuration files in:
- `.dokkument.json` (current directory)
- `~/.dokkument.json` (home directory)
- `~/.config/dokkument/config.json` (Linux/macOS)
- `%APPDATA%/dokkument/config.json` (Windows)

### Configuration example

```json
{
  "scanning": {
    "recursive": true,
    "max_depth": 10,
    "excluded_dirs": [".git", "__pycache__", "node_modules"]
  },
  "display": {
    "enable_colors": true,
    "enable_hyperlinks": true,
    "group_by_file": true,
    "confirm_open_all": true
  },
  "browser": {
    "preferred_browser": "firefox",
    "open_delay_seconds": 0.5
  },
  "security": {
    "validate_urls": true,
    "allowed_schemes": ["http", "https"]
  }
}
```

## 🏗️ Architecture

dokkument implements several design patterns to ensure clean and maintainable code:

- **Factory Pattern** - `DokkParserFactory` to handle different types of parsers
- **Command Pattern** - Modular and extensible command system
- **Singleton Pattern** - `ConfigManager` for global configuration
- **Strategy Pattern** - Different export formats

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Commit your changes (`git commit -am 'Add your-feature-name'`)
4. Push the branch (`git push origin feature/your-feature-name`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/RobertoZanolli/dokkument/issues)
- **Documentation**: this readme right here :D

---

**Made with ❤️ by a developer for developers**
