"""
Main - Entry point for the dokkument application
Manages argparse and orchestration of main components
"""

import argparse
import sys
from pathlib import Path
import traceback

from .parser import DokkParserFactory
from .link_manager import LinkManager
from .browser_opener import BrowserOpener
from .cli_display import CLIDisplay
from .commands import CommandInvoker
from .config_manager import get_config


class DokkumentApp:
    """Main class for the dokkument application"""

    def __init__(self):
        self.config = get_config()
        self.parser_factory = DokkParserFactory()
        self.link_manager = LinkManager(self.parser_factory)
        self.browser_opener = BrowserOpener()
        self.cli_display = CLIDisplay(self.link_manager)
        self.command_invoker = CommandInvoker(
            self.link_manager, self.browser_opener, self.cli_display
        )

    def run_interactive_mode(self, scan_path: Path = None):
        """
        Runs the application in interactive mode

        Args:
            scan_path: Directory to scan (default: current directory)
        """
        if scan_path is None:
            scan_path = Path.cwd()

        # Application header
        self.cli_display.print_header("dokkument - Company Documentation Manager")
        self.cli_display.print_scanning_message(scan_path)

        # Scans for .dokk files
        try:
            recursive = self.config.get("scanning.recursive", True)
            total_links = self.link_manager.scan_for_links(scan_path, recursive)

            # Shows scan results
            self.cli_display.print_scan_results(
                total_links, self.link_manager.get_statistics()["total_files"]
            )

            if total_links == 0:
                return

            # Main interactive loop
            while True:
                entries = self.link_manager.get_all_entries()
                show_files = self.config.get("display.show_file_names", True)

                self.cli_display.print_menu(entries, show_files)
                self.cli_display.print_menu_footer(len(entries))

                user_input = self.cli_display.get_user_input()

                # Execute command
                should_continue = self.command_invoker.parse_and_execute_user_input(
                    user_input, len(entries)
                )

                if not should_continue:
                    break

                print()  # Empty line between iterations

        except KeyboardInterrupt:
            self.cli_display.print_farewell()
        except (OSError, RuntimeError, ValueError) as e:
            self.cli_display.print_error_message(f"Critical error: {e}")
            if self.config.get("advanced.debug_mode", False):
                traceback.print_exc()
            sys.exit(1)

    def run_list_mode(self, scan_path: Path = None, format_type: str = "text"):
        """
        Runs the application in list mode (non-interactive)

        Args:
            scan_path: Directory to scan
            format_type: Output format
        """
        if scan_path is None:
            scan_path = Path.cwd()

        try:
            recursive = self.config.get("scanning.recursive", True)
            total_links = self.link_manager.scan_for_links(scan_path, recursive)

            if total_links == 0:
                print("No .dokk files found")
                return

            # Output based on requested format
            if format_type in ["json", "markdown", "html"]:
                content = self.link_manager.export_to_format(format_type)
                print(content)
            else:
                # Simple text output
                entries = self.link_manager.get_all_entries()
                for i, entry in enumerate(entries, 1):
                    print(f"{i:2d}. {entry.description}")
                    print(f"    {entry.url}")
                    print(f"    = {entry.file_path}")
                    print()

        except (OSError, RuntimeError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def run_open_mode(
        self, scan_path: Path = None, link_indices: list = None, open_all: bool = False
    ):
        """
        Runs the application in open mode

        Args:
            scan_path: Directory to scan
            link_indices: List of link indices to open
            open_all: If True, opens all links
        """
        if scan_path is None:
            scan_path = Path.cwd()

        try:
            entries = self._scan_and_get_entries(scan_path)
            if not entries:
                print("No .dokk files found")
                return

            if open_all:
                self._open_all_links(entries)
            elif link_indices:
                self._open_specific_links(entries, link_indices)

        except (OSError, RuntimeError, ValueError) as open_error:
            print(f"Error: {open_error}", file=sys.stderr)
            sys.exit(1)

    def _scan_and_get_entries(self, scan_path: Path):
        """Helper method to scan and return entries"""
        recursive = self.config.get("scanning.recursive", True)
        total_links = self.link_manager.scan_for_links(scan_path, recursive)
        return self.link_manager.get_all_entries() if total_links > 0 else []

    def _open_all_links(self, entries):
        """Helper method to open all links"""
        urls = [entry.url for entry in entries]
        preferred_browser = self.config.get("browser.preferred_browser")
        delay = self.config.get("browser.open_delay_seconds", 0.5)

        print(f"Opening {len(urls)} links...")
        results = self.browser_opener.open_multiple_urls(urls, preferred_browser, delay)
        success_count = sum(1 for result in results if result)
        print(f"Opened {success_count} links out of {len(urls)}")

    def _open_specific_links(self, entries, link_indices):
        """Helper method to open specific links by indices"""
        preferred_browser = self.config.get("browser.preferred_browser")

        for index in link_indices:
            if 1 <= index <= len(entries):
                entry = entries[index - 1]
                print(f"Opening: {entry.description}")
                success = self.browser_opener.open_url(entry.url, preferred_browser)
                if not success:
                    print(f"Error opening: {entry.description}")
            else:
                print(f"Invalid index: {index}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Creates and configures the parser for command line arguments"""

    parser = argparse.ArgumentParser(
        prog="dokkument",
        description="CLI manager for corporate documentation via .dokk files",
        epilog="""
Usage examples:
  dokkument                        # Interactive mode
  dokkument --list                 # List all links
  dokkument --list --format json  # List in JSON format
  dokkument --open-all             # Open all links
  dokkument --open 1 3 5           # Open links 1, 3, and 5
  dokkument --path /docs           # Scan specific directory
  dokkument --config show          # Show configuration
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Argomenti generali
    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=None,
        help="Directory to scan for .dokk files (default: current directory)",
    )

    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Scan subdirectories recursively",
    )

    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not scan recursively (overrides configuration)",
    )

    # Operating modes (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()

    mode_group.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="Show only the list of links without interactive mode",
    )

    mode_group.add_argument(
        "--open-all", "-a", action="store_true", help="Open all found links and exit"
    )

    mode_group.add_argument(
        "--open",
        "-o",
        nargs="+",
        type=int,
        metavar="INDEX",
        help="Open links with specified indices (e.g., --open 1 3 5)",
    )

    # Options for list mode
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown", "html"],
        default="text",
        help="Output format for list mode (default: text)",
    )

    # Configuration options
    parser.add_argument(
        "--config",
        "-c",
        choices=["show", "export", "validate"],
        help="Configuration operations",
    )

    parser.add_argument(
        "--browser",
        "-b",
        type=str,
        help="Specific browser to use (overrides configuration)",
    )

    # Output options
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colors in output"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with additional information",
    )

    parser.add_argument("--version", "-v", action="version", version="dokkument 1.0.0")

    # Options for testing and development
    parser.add_argument(
        "--validate", action="store_true", help="Validate all found links"
    )

    parser.add_argument(
        "--stats", action="store_true", help="Show only statistics"
    )

    return parser


def main():
    """Main function"""

    # Create argument parser
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()

    # Create application
    app = DokkumentApp()

    # Apply configuration overrides from arguments
    if args.no_color:
        app.config.set("display.enable_colors", False)

    if args.debug:
        app.config.set("advanced.debug_mode", True)

    if args.recursive:
        app.config.set("scanning.recursive", True)
    elif args.no_recursive:
        app.config.set("scanning.recursive", False)

    if args.browser:
        app.config.set("browser.preferred_browser", args.browser)

    # Configuration command handling
    if args.config:
        app.command_invoker.execute_command("config", args.config)
        return

    # Specific mode handling
    if args.validate:
        # Scan first
        scan_path = args.path or Path.cwd()
        recursive = app.config.get("scanning.recursive", True)
        app.link_manager.scan_for_links(scan_path, recursive)

        # Then validate
        app.command_invoker.execute_command("validate")
        return

    if args.stats:
        # Scan first
        scan_path = args.path or Path.cwd()
        recursive = app.config.get("scanning.recursive", True)
        app.link_manager.scan_for_links(scan_path, recursive)

        # Then show statistics
        app.command_invoker.execute_command("statistics")
        return

    # Main modes
    if args.list:
        app.run_list_mode(args.path, args.format)
    elif args.open_all:
        app.run_open_mode(args.path, open_all=True)
    elif args.open:
        app.run_open_mode(args.path, link_indices=args.open)
    else:
        # Interactive mode (default)
        app.run_interactive_mode(args.path)


if __name__ == "__main__":
    main()
