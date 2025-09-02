"""
dokkument - Documentation helper for .dokk files

This package provides tools to manage and quickly access
company documentation using .dokk files containing
organized links.

Main components:
- DokkFileParser: Parser for .dokk files
- LinkManager: Management of links and collections
- BrowserOpener: Opens URLs in the browser
- CLIDisplay: Command-line interface
- ConfigManager: Configuration management
- Commands: Command system with Command pattern
"""

__version__ = "1.0.0"
__author__ = "Roberto Zanolli"
__description__ = "CLI manager for company documentation using .dokk files"

# Main imports for easier module usage
from .parser import DokkEntry, DokkParserFactory, DokkFileScanner, ParseError

from .link_manager import LinkManager
from .browser_opener import BrowserOpener
from .cli_display import CLIDisplay
from .config_manager import ConfigManager, get_config
from .commands import CommandInvoker
from .main import DokkumentApp, main



__all__ = [
    # Main classes
    "DokkumentApp",
    "LinkManager",
    "BrowserOpener",
    "CLIDisplay",
    "ConfigManager",
    "CommandInvoker",
    # Parser
    "DokkEntry",
    "DokkParserFactory",
    "DokkFileScanner",
    "ParseError",
    # Utility functions
    "get_config",
    "main",
    # Metadata
    "__version__",
    "__author__",
    "__description__",
]
