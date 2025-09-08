"""
CLIDisplay - Manages the display of the interactive menu
Provides a user-friendly interface with colors and formatting
"""

import sys
import os
from typing import List, Dict
from pathlib import Path
import ctypes

from .parser import DokkEntry
from .link_manager import LinkManager


class CLIDisplay:
    """Manages the command-line interface display"""

    def __init__(self, link_manager: LinkManager):
        self.link_manager = link_manager
        self.supports_color = self._check_color_support()
        self.supports_hyperlinks = self._check_hyperlink_support()

        # ANSI color codes (default set)
        self._default_colors = {
            "header": "\033[1;36m",  # Bold cyan
            "success": "\033[1;32m",  # Bold green
            "warning": "\033[1;33m",  # Bold yellow
            "error": "\033[1;31m",  # Bold red
            "info": "\033[1;34m",  # Bold blue
            "prompt": "\033[1;35m",  # Bold magenta
            "reset": "\033[0m",  # Reset
            "dim": "\033[2m",  # Dim text
            "bold": "\033[1m",  # Bold
        }

        # If the terminal does not support colors, use empty strings
        if not self.supports_color:
            self.colors = {key: "" for key in self._default_colors}
        else:
            self.colors = self._default_colors

    def _check_color_support(self) -> bool:
        """Checks if the terminal supports ANSI colors"""
        # Check common environment variables
        term = os.environ.get("TERM", "")
        colorterm = os.environ.get("COLORTERM", "")

        # On Windows, check if we are using a modern terminal
        if sys.platform == "win32":
            # Windows Terminal, VS Code terminal, etc. support colors
            if any(env in os.environ for env in ["WT_SESSION", "VSCODE_PID"]):
                return True
            # Try to enable color support on Windows 10+
            try:
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:  # pylint: disable=broad-except
                return False

        # On Unix-like, check TERM
        color_terms = ["xterm", "xterm-256color", "screen", "tmux", "linux"]
        return any(color_term in term for color_term in color_terms) or bool(colorterm)

    def _check_hyperlink_support(self) -> bool:
        """Checks if the terminal supports OSC 8 hyperlinks"""
        # List of terminals that support OSC 8
        term = os.environ.get("TERM", "").lower()
        term_program = os.environ.get("TERM_PROGRAM", "").lower()

        hyperlink_terminals = ["iterm", "vte", "gnome-terminal", "konsole", "alacritty"]

        return (
            any(ht in term for ht in hyperlink_terminals)
            or any(ht in term_program for ht in hyperlink_terminals)
            or "VSCODE_PID" in os.environ
            or "WT_SESSION" in os.environ
        )

    def colorize(self, text: str, color_key: str) -> str:
        """Applies color to text if supported"""
        color = self.colors.get(color_key, "")
        reset = self.colors.get("reset", "")
        return f"{color}{text}{reset}" if color else text

    def print_header(self, title: str):
        """Prints a formatted header"""
        print()
        print(self.colorize("=" * 60, "header"))
        print(self.colorize(f"  {title.center(56)}", "header"))
        print(self.colorize("=" * 60, "header"))
        print()

    def print_scanning_message(self, path: Path):
        """Prints message during scanning"""
        print(self.colorize(f" Scanning directory: {path}", "info"))
        print()

    def print_scan_results(self, total_links: int, total_files: int):
        """Prints the scan results"""
        if total_links == 0:
            print(
                self.colorize(
                    " No .dokk files found in the current directory", "warning"
                )
            )
            print(
                self.colorize(
                    " Make sure there are .dokk files in the format:", "info"
                )
            )
            print(
                self.colorize(
                    '   "Link description" -> "https://example.com"', "dim"
                )
            )
            return

        print(
            self.colorize(
                f" Found {total_links} links in {total_files} files", "success"
            )
        )
        print()

    def print_menu(self, entries: List[DokkEntry], show_files: bool = True):
        """
        Prints the main menu with options

        Args:
            entries: List of entries to show
            show_files: If True, also shows file names
        """
        if not entries:
            print(self.colorize("No links available", "warning"))
            return

        print(self.colorize(" Available links:", "header"))
        print()

        # Group by file if requested
        if show_files:
            entries_by_file = {}
            for entry in entries:
                if entry.file_path not in entries_by_file:
                    entries_by_file[entry.file_path] = []
                entries_by_file[entry.file_path].append(entry)

            index = 1
            for file_path, file_entries in entries_by_file.items():
                # File name with color
                print(self.colorize(f" {file_path.name}", "dim"))

                for entry in file_entries:
                    description = self.link_manager.get_colored_description(entry)
                    url = self.link_manager.get_colored_url(
                        entry, self.supports_hyperlinks
                    )

                    print(f"{self.colorize(f'[{index:2d}]', 'prompt')} {description}")
                    if not self.supports_hyperlinks:
                        print(f"     {url}")

                    index += 1
                print()
        else:
            # Simple menu without grouping
            for i, entry in enumerate(entries, 1):
                description = self.link_manager.get_colored_description(entry)
                url = self.link_manager.get_colored_url(entry, self.supports_hyperlinks)

                print(f"{self.colorize(f'[{i:2d}]', 'prompt')} {description}")
                if not self.supports_hyperlinks:
                    print(f"     {url}")

        print()

    def print_menu_footer(self, total_entries: int):
        """Prints the menu footer with options"""
        print(self.colorize(" " * 60, "dim"))
        print(self.colorize("Available options:", "info"))
        print(
            f"  {self.colorize('1-' + str(total_entries), 'prompt')}: Open the corresponding link"
        )
        print(f"  {self.colorize('a', 'prompt')}: Open all links")
        print(f"  {self.colorize('l', 'prompt')}: Show only the list (without opening)")
        print(f"  {self.colorize('r', 'prompt')}: Reload/Rescan")
        print(f"  {self.colorize('s', 'prompt')}: Statistics")
        print(f"  {self.colorize('h', 'prompt')}: Help")
        print(f"  {self.colorize('q', 'prompt')}: Exit")
        print()

    def get_user_input(self, prompt: str = "Select an option") -> str:
        """Gets input from the user with colored prompt"""
        colored_prompt = self.colorize(f"{prompt}: ", "prompt")
        try:
            return input(colored_prompt).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return "q"  # Exits on Ctrl+C or Ctrl+D

    def print_opening_message(self, entry: DokkEntry):
        """Prints message when opening a link"""
        print(self.colorize(f" Opening: {entry.description}", "info"))
        print(self.colorize(f" URL: {entry.url}", "dim"))

    def print_opening_all_message(self, count: int):
        """Prints message when opening all links"""
        print(self.colorize(f" Opening all {count} links...", "warning"))
        print(
            self.colorize(
                "  This might open many browser tabs!", "warning"
            )
        )

    def print_success_message(self, message: str):
        """Prints a success message"""
        print(self.colorize(f" {message}", "success"))

    def print_error_message(self, message: str):
        """Prints an error message"""
        print(self.colorize(f" {message}", "error"))

    def print_warning_message(self, message: str):
        """Prints a warning message"""
        print(self.colorize(f"  {message}", "warning"))

    def print_info_message(self, message: str):
        """Prints an info message"""
        print(self.colorize(f"  {message}", "info"))

    def print_statistics(self, stats: Dict[str, int]):
        """Prints link statistics"""
        print()
        print(self.colorize(" Statistics", "header"))
        print(self.colorize("-" * 30, "dim"))
        print(
            f" .dokk files found: {self.colorize(str(stats['total_files']), 'info')}"
        )
        print(f" Total links: {self.colorize(str(stats['total_links']), 'info')}")
        print(f" Unique domains: {self.colorize(str(stats['unique_domains']), 'info')}")

        if stats["total_files"] > 0:
            avg_links = stats["total_links"] / stats["total_files"]
            print(
                f" Average links per file: {self.colorize(f'{avg_links:.1f}', 'info')}"
            )
        print()

    def print_help(self):
        """Prints help for the user"""
        print()
        print(self.colorize(" Help - dokkument", "header"))
        print()
        print(self.colorize("File .dokk format:", "info"))
        print('  "Link description" -> "https://example.com"')
        print('  "API Documentation" -> "https://api.example.com/docs"')
        print()
        print(self.colorize("Available commands:", "info"))
        print("   Number (1-N): Opens the corresponding link")
        print("   a: Opens all links simultaneously")
        print("   l: Shows only the list without opening anything")
        print("   r: Reloads and rescans .dokk files")
        print("   s: Shows statistics on found links")
        print("   h: Shows this help")
        print("   q: Exits the application")
        print()
        print(self.colorize("Notes:", "warning"))
        print("   Links from the same file have the same color")
        print("   On compatible terminals, links are clickable")
        print("   The application searches for .dokk files recursively")
        print()

    def confirm_action(self, message: str, default: bool = True) -> bool:
        """
        Asks for user confirmation

        Args:
            message: Message to show
            default: Default value if user presses Enter only

        Returns:
            bool: True if user confirms
        """
        default_text = "Y/n" if default else "y/N"
        response = (
            input(self.colorize(f"{message} ({default_text}): ", "prompt"))
            .strip()
            .lower()
        )

        if response == "":
            return default
        if response in ["y", "yes", "s", "si"]:
            return True
        if response in ["n", "no"]:
            return False
        return default

    def clear_screen(self):
        """Clears the screen if possible"""
        try:
            if sys.platform == "win32":
                os.system("cls")
            else:
                os.system("clear")
        except Exception:  # pylint: disable=broad-except
            # If it can't clear, print some empty lines
            print("\n" * 3)

    def print_farewell(self):
        """Prints farewell message"""
        print()
        print(
            self.colorize(" Goodbye! Thank you for using dokkument", "success")
        )
        print()
