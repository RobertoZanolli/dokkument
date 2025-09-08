"""
Commands - Implements the Command pattern to manage application commands
Provides a flexible architecture for adding new commands
"""

from abc import ABC, abstractmethod
from typing import Dict
from pathlib import Path

from .link_manager import LinkManager
from .browser_opener import BrowserOpener
from .cli_display import CLIDisplay
from .config_manager import get_config


class Command(ABC):
    """Abstract base class for all commands"""

    def __init__(
        self,
        link_manager: LinkManager,
        browser_opener: BrowserOpener,
        cli_display: CLIDisplay,
    ):
        self.link_manager = link_manager
        self.browser_opener = browser_opener
        self.cli_display = cli_display
        self.config = get_config()

    @abstractmethod
    def execute(self, *args, **kwargs) -> bool:
        """
        Executes the command

        Returns:
            bool: True if the command should continue the loop, False to exit
        """
        raise NotImplementedError

    @abstractmethod
    def get_description(self) -> str:
        """Returns the command description"""
        raise NotImplementedError


class OpenLinkCommand(Command):
    """Command to open a single link"""

    def execute(self, *args, **kwargs) -> bool:
        index = kwargs.get("index", args[0] if args else None)
        if not isinstance(index, int):
            self.cli_display.print_error_message("Invalid number. Provide a valid index")
            return True

        entry = self.link_manager.get_entry_by_index(index)
        if entry is None:
            self.cli_display.print_error_message(f"Invalid number: {index}")
            return True

        self.cli_display.print_opening_message(entry)

        preferred_browser = self.config.get("browser.preferred_browser")
        success = self.browser_opener.open_url(entry.url, preferred_browser)

        if success:
            self.cli_display.print_success_message("Link opened successfully!")
        else:
            self.cli_display.print_error_message("Unable to open the link")

        return True

    def get_description(self) -> str:
        return "Opens a specific link in the browser"


class OpenAllLinksCommand(Command):
    """Command to open all links"""

    def execute(self, *args, **kwargs) -> bool:
        entries = self.link_manager.get_all_entries()
        if not entries:
            self.cli_display.print_warning_message("No links to open")
            return True

        # Confirm if requested by configuration
        if self.config.get("display.confirm_open_all", True):
            self.cli_display.print_opening_all_message(len(entries))
            if not self.cli_display.confirm_action("Continue?"):
                self.cli_display.print_info_message("Operation cancelled")
                return True

        # Limit the number of links opened simultaneously
        max_concurrent = self.config.get("browser.max_concurrent_opens", 10)
        if len(entries) > max_concurrent:
            self.cli_display.print_warning_message(
                f"Too many links ({len(entries)}), only the first {max_concurrent} will be opened"
            )
            entries = entries[:max_concurrent]

        # Open all links
        preferred_browser = self.config.get("browser.preferred_browser")
        delay = self.config.get("browser.open_delay_seconds", 0.5)

        urls = [entry.url for entry in entries]
        results = self.browser_opener.open_multiple_urls(urls, preferred_browser, delay)

        success_count = sum(1 for result in results if result)
        self.cli_display.print_success_message(
            f"Opened {success_count} links out of {len(entries)}"
        )

        return True

    def get_description(self) -> str:
        return "Opens all links simultaneously"


class ListLinksCommand(Command):
    """Command to show only the list of links"""

    def execute(self, *args, **kwargs) -> bool:
        entries = self.link_manager.get_all_entries()
        show_files = self.config.get("display.group_by_file", True)

        self.cli_display.print_header("Complete List of Links")
        self.cli_display.print_menu(entries, show_files)

        return True

    def get_description(self) -> str:
        return "Shows the complete list of links without opening them"


class ReloadCommand(Command):
    """Command to reload/rescan .dokk files"""

    def execute(self, *args, **kwargs) -> bool:
        self.cli_display.print_info_message("Rescanning .dokk files...")

        current_path = Path.cwd()
        recursive = self.config.get("scanning.recursive", True)

        try:
            total_links = self.link_manager.scan_for_links(current_path, recursive)
            self.cli_display.print_scan_results(
                total_links, len(self.link_manager.get_entries_by_file())
            )

            if total_links > 0:
                entries = self.link_manager.get_all_entries()
                show_files = self.config.get("display.show_file_names", True)
                self.cli_display.print_menu(entries, show_files)
                self.cli_display.print_menu_footer(len(entries))

        except (OSError, RuntimeError, ValueError) as e:
            self.cli_display.print_error_message(f"Error during rescan: {e}")

        return True

    def get_description(self) -> str:
        return "Reloads and rescans .dokk files"


class StatisticsCommand(Command):
    """Command to show statistics on links"""

    def execute(self, *args, **kwargs) -> bool:
        stats = self.link_manager.get_statistics()
        self.cli_display.print_statistics(stats)

        # Additional information if requested
        if self.config.get("advanced.debug_mode", False):
            entries_by_file = self.link_manager.get_entries_by_file()
            print("\n" + self.cli_display.colorize("=Debug Details:", "info"))
            for file_path, entries in entries_by_file.items():
                print(f"  = {file_path}: {len(entries)} links")

        return True

    def get_description(self) -> str:
        return "Shows statistics on found links"


class HelpCommand(Command):
    """Command to show help"""

    def execute(self, *args, **kwargs) -> bool:
        self.cli_display.print_help()
        return True

    def get_description(self) -> str:
        return "Shows application help"


class ConfigCommand(Command):
    """Command to manage configuration"""

    def execute(self, *args, **kwargs) -> bool:
        action = kwargs.get("action", args[0] if args else "show")
        if action == "show":
            self.config.print_config_info()
        elif action == "export":
            template_path = Path.cwd() / "dokkument-config-template.json"
            if self.config.export_config_template(template_path):
                self.cli_display.print_success_message(
                    f"Template exported to: {template_path}"
                )
            else:
                self.cli_display.print_error_message(
                    "Error exporting template"
                )
        elif action == "validate":
            errors = self.config.validate_config()
            if errors:
                self.cli_display.print_error_message(
                    "Configuration errors found:"
                )
                for error in errors:
                    print(f"  - {error}")
            else:
                self.cli_display.print_success_message("Configuration is valid")

        return True

    def get_description(self) -> str:
        return "Manages application configuration"


class ValidateLinksCommand(Command):
    """Command to validate all links"""

    def execute(self, *args, **kwargs) -> bool:
        self.cli_display.print_info_message("Validating all links...")

        invalid_links = self.link_manager.validate_all_links()

        if invalid_links:
            self.cli_display.print_warning_message(
                f"Found {len(invalid_links)} invalid links:"
            )
            for entry, error in invalid_links:
                print(f"  L {entry.description}: {error}")
                print(f"     = File: {entry.file_path}")
                print(f"     = URL: {entry.url}")
                print()
        else:
            self.cli_display.print_success_message("All links are valid!")

        return True

    def get_description(self) -> str:
        return "Validates the correctness of all links"


class ExportCommand(Command):
    """Command to export links in various formats"""

    def execute(self, *args, **kwargs) -> bool:
        format_type = kwargs.get("format_type", args[0] if args else "text")
        output_file = kwargs.get("output_file", args[1] if len(args) > 1 else None)
        try:
            content = self.link_manager.export_to_format(format_type)

            if output_file:
                output_path = Path(output_file)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.cli_display.print_success_message(
                    f"Links exported to: {output_path}"
                )
            else:
                print(content)

        except ValueError as e:
            self.cli_display.print_error_message(f"Unsupported format: {e}")
        except (OSError, RuntimeError) as e:
            self.cli_display.print_error_message(f"Error during export: {e}")

        return True

    def get_description(self) -> str:
        return "Exports links in various formats (text, markdown, html, json)"


class SearchCommand(Command):
    """Command to search links by description"""

    def execute(self, *args, **kwargs) -> bool:
        search_term = kwargs.get("search_term", args[0] if args else "")
        if not search_term.strip():
            self.cli_display.print_warning_message("Empty search term")
            return True

        matching_entries = self.link_manager.filter_entries(search_term)

        if not matching_entries:
            self.cli_display.print_warning_message(
                f"No links found for: '{search_term}'"
            )
        else:
            self.cli_display.print_header(f"Search results: '{search_term}'")
            show_files = self.config.get("display.show_file_names", True)
            self.cli_display.print_menu(matching_entries, show_files)

        return True

    def get_description(self) -> str:
        return "Searches links by term in description"


class QuitCommand(Command):
    """Command to exit the application"""

    def execute(self, *args, **kwargs) -> bool:
        self.cli_display.print_farewell()
        return False  # Interrupts the main loop

    def get_description(self) -> str:
        return "Exits the application"


class CommandInvoker:
    """Invoker for the Command pattern - manages command execution"""

    def __init__(
        self,
        link_manager: LinkManager,
        browser_opener: BrowserOpener,
        cli_display: CLIDisplay,
    ):
        self.link_manager = link_manager
        self.browser_opener = browser_opener
        self.cli_display = cli_display

        # Register all available commands
        self.commands: Dict[str, Command] = {
            "open_link": OpenLinkCommand(link_manager, browser_opener, cli_display),
            "open_all": OpenAllLinksCommand(link_manager, browser_opener, cli_display),
            "list": ListLinksCommand(link_manager, browser_opener, cli_display),
            "reload": ReloadCommand(link_manager, browser_opener, cli_display),
            "statistics": StatisticsCommand(link_manager, browser_opener, cli_display),
            "help": HelpCommand(link_manager, browser_opener, cli_display),
            "config": ConfigCommand(link_manager, browser_opener, cli_display),
            "validate": ValidateLinksCommand(link_manager, browser_opener, cli_display),
            "export": ExportCommand(link_manager, browser_opener, cli_display),
            "search": SearchCommand(link_manager, browser_opener, cli_display),
            "quit": QuitCommand(link_manager, browser_opener, cli_display),
        }

    def execute_command(self, command_name: str, *args, **kwargs) -> bool:
        """
        Executes a specific command

        Args:
            command_name: Name of the command to execute
            *args, **kwargs: Arguments to pass to the command

        Returns:
            bool: True to continue, False to exit
        """
        command = self.commands.get(command_name)
        if command:
            try:
                return command.execute(*args, **kwargs)  # type: ignore
            except Exception as e:  # pylint: disable=broad-except
                self.cli_display.print_error_message(
                    f"Error executing command: {e}"
                )
                return True
        else:
            self.cli_display.print_error_message(
                f"Unrecognized command: {command_name}"
            )
            return True

    def get_available_commands(self) -> Dict[str, str]:
        """Returns a dictionary of available commands with their descriptions"""
        return {name: cmd.get_description() for name, cmd in self.commands.items()}

    def register_command(self, name: str, command: Command):
        """Registers a new custom command"""
        self.commands[name] = command

    def parse_and_execute_user_input(self, user_input: str, total_entries: int) -> bool:  # pylint: disable=too-many-return-statements
        """
        Parses user input and executes the appropriate command

        Args:
            user_input: User input
            total_entries: Total number of available entries

        Returns:
            bool: True to continue, False to exit
        """
        user_input = user_input.strip().lower()

        if not user_input:
            return True

        # Handle numbers (opening specific link)
        if user_input.isdigit():
            index = int(user_input)
            if 1 <= index <= total_entries:
                return self.execute_command("open_link", index)  # type: ignore
            self.cli_display.print_error_message(
                f"Invalid number. Enter a number between 1 and {total_entries}"
            )
            return True

        # Handle single commands
        command_map = {
            "a": "open_all",
            "l": "list",
            "r": "reload",
            "s": "statistics",
            "h": "help",
            "q": "quit",
            "v": "validate",
            "c": "config",
        }

        # Handle commands with arguments
        parts = user_input.split()
        if len(parts) > 1:
            cmd = parts[0]
            args = parts[1:]

            if cmd in ("search", "find"):
                search_term = " ".join(args)
                return self.execute_command("search", search_term)
            if cmd == "export":
                format_type = args[0] if args else "text"
                output_file = args[1] if len(args) > 1 else None
                return self.execute_command("export", format_type, output_file)
            if cmd in ("config", "c"):
                action = args[0] if args else "show"
                return self.execute_command("config", action)

        # Handle single commands
        if user_input in command_map:
            return self.execute_command(command_map[user_input])

        # Unrecognized command
        self.cli_display.print_error_message(
            f"Unrecognized command: '{user_input}'"
        )
        self.cli_display.print_info_message("Type 'h' to see help")
        return True
