"""
LinkManager - Manages the collection of links and descriptions
Centralizes the logic for handling links found in .dokk files
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import json

from .parser import DokkEntry, DokkFileScanner, DokkParserFactory


class LinkManager:
    """Manages the collection of links and operations on them"""

    def __init__(self, parser_factory: DokkParserFactory = None):
        self.scanner = DokkFileScanner(parser_factory)
        self._entries: List[DokkEntry] = []
        self._entries_by_file: Dict[Path, List[DokkEntry]] = {}
        self._last_scan_path: Optional[Path] = None
        self._file_colors: Dict[Path, str] = {}

        # ANSI colors for terminal
        self._colors = [
            "\033[91m",  # Red
            "\033[92m",  # Green
            "\033[93m",  # Yellow
            "\033[94m",  # Blue
            "\033[95m",  # Magenta
            "\033[96m",  # Cyan
            "\033[97m",  # White
        ]
        self._reset_color = "\033[0m"

    def scan_for_links(self, root_path: Path = None, recursive: bool = True) -> int:
        """
        Scans for .dokk files and loads links

        Args:
            root_path: Directory to scan (default: current directory)
            recursive: If True, scans subdirectories

        Returns:
            int: Total number of links found
        """
        if root_path is None:
            root_path = Path.cwd()

        self._last_scan_path = root_path
        self._entries.clear()
        self._entries_by_file.clear()
        self._file_colors.clear()

        try:
            file_entries = self.scanner.scan_directory(root_path, recursive)

            # Assign colors to files
            color_index = 0
            for file_path in file_entries:
                self._file_colors[file_path] = self._colors[
                    color_index % len(self._colors)
                ]
                color_index += 1

            # Add all entries
            for file_path, entries in file_entries.items():
                self._entries_by_file[file_path] = entries
                self._entries.extend(entries)

            return len(self._entries)

        except Exception as scan_error:
            raise RuntimeError(f"Error during scanning: {scan_error}") from scan_error

    def get_all_entries(self) -> List[DokkEntry]:
        """Returns all loaded entries"""
        return self._entries.copy()

    def get_entries_by_file(self) -> Dict[Path, List[DokkEntry]]:
        """Returns entries grouped by file"""
        return self._entries_by_file.copy()

    def get_entry_by_index(self, index: int) -> Optional[DokkEntry]:
        """
        Returns an entry by index (1-based for the user)

        Args:
            index: 1-based index of the entry

        Returns:
            DokkEntry or None if the index is invalid
        """
        if 1 <= index <= len(self._entries):
            return self._entries[index - 1]
        return None

    def get_file_color(self, file_path: Path) -> str:
        """Returns the ANSI color associated with a file"""
        return self._file_colors.get(file_path, "")

    def get_colored_description(self, entry: DokkEntry) -> str:
        """
        Returns the colored description for the terminal

        Args:
            entry: Entry to color the description for

        Returns:
            str: Description with ANSI color codes
        """
        color = self.get_file_color(entry.file_path)
        return f"{color}{entry.description}{self._reset_color}"

    def get_colored_url(self, entry: DokkEntry, make_clickable: bool = True) -> str:
        """
        Returns the colored and optionally clickable URL

        Args:
            entry: Entry to color the URL for
            make_clickable: If True, makes the URL clickable if supported by the terminal

        Returns:
            str: URL with color codes and optionally clickable
        """
        color = self.get_file_color(entry.file_path)

        if make_clickable:
            # OSC 8 format for clickable links in compatible terminals
            clickable_url = f"\033]8;;{entry.url}\033\\{entry.url}\033]8;;\033\\"
            return f"{color}{clickable_url}{self._reset_color}"
        return f"{color}{entry.url}{self._reset_color}"

    def filter_entries(self, search_term: str) -> List[DokkEntry]:
        """
        Filters entries based on a search term

        Args:
            search_term: Term to search for in descriptions

        Returns:
            List[DokkEntry]: Entries containing the search term
        """
        search_lower = search_term.lower()
        return [
            entry
            for entry in self._entries
            if search_lower in entry.description.lower()
        ]

    def get_statistics(self) -> Dict[str, int]:
        """
        Returns statistics about loaded links

        Returns:
            Dict with statistics (total_links, total_files, unique_domains)
        """
        if not self._entries:
            return {"total_links": 0, "total_files": 0, "unique_domains": 0}

        # Extract unique domains
        domains = set()
        for entry in self._entries:
            try:
                parsed = urlparse(entry.url)
                if parsed.netloc:
                    domains.add(parsed.netloc.lower())
            except Exception:  # pylint: disable=broad-except
                continue

        return {
            "total_links": len(self._entries),
            "total_files": len(self._entries_by_file),
            "unique_domains": len(domains),
        }

    def validate_all_links(self) -> List[Tuple[DokkEntry, str]]:
        """
        Validates all links (basic format check)

        Returns:
            List[Tuple[DokkEntry, str]]: List of (entry, error_message) for invalid links
        """
        invalid_links = []

        for entry in self._entries:
            try:
                parsed = urlparse(entry.url)

                if not parsed.scheme or parsed.scheme not in ["http", "https"]:
                    invalid_links.append((entry, "Invalid URL scheme"))
                elif not parsed.netloc:
                    invalid_links.append((entry, "Missing domain in URL"))

            except Exception as parse_error:  # pylint: disable=broad-except
                invalid_links.append((entry, f"URL parsing error: {parse_error}"))

        return invalid_links

    def export_to_format(self, format_type: str = "text") -> str:
        """
        Exports links in various formats

        Args:
            format_type: Export format ('text', 'markdown', 'html', 'json')

        Returns:
            str: Exported content in the requested format
        """
        if format_type == "text":
            return self._export_to_text()
        if format_type == "markdown":
            return self._export_to_markdown()
        if format_type == "html":
            return self._export_to_html()
        if format_type == "json":
            return self._export_to_json()
        raise ValueError(f"Unsupported format: {format_type}")

    def _export_to_text(self) -> str:
        """Exports in plain text format"""
        lines = ["Documentation Links\n", "=" * 50, ""]

        for file_path, entries in self._entries_by_file.items():
            lines.append(f"File: {file_path}")
            lines.append("-" * 40)
            for i, entry in enumerate(entries, 1):
                lines.append(f"{i:2d}. {entry.description}")
                lines.append(f"    {entry.url}")
            lines.append("")

        return "\n".join(lines)

    def _export_to_markdown(self) -> str:
        """Exports in Markdown format"""
        lines = ["# Documentation Links", ""]

        for file_path, entries in self._entries_by_file.items():
            lines.append(f"## {file_path.name}")
            lines.append("")
            for entry in entries:
                lines.append(f"- [{entry.description}]({entry.url})")
            lines.append("")

        return "\n".join(lines)

    def _export_to_html(self) -> str:
        """Exports in HTML format"""
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Documentation Links</title>",
            "</head>",
            "<body>",
            "<h1>Documentation Links</h1>",
        ]

        for file_path, entries in self._entries_by_file.items():
            html.append(f"<h2>{file_path.name}</h2>")
            html.append("<ul>")
            for entry in entries:
                html.append(f'<li><a href="{entry.url}">{entry.description}</a></li>')
            html.append("</ul>")

        html.extend(["</body>", "</html>"])
        return "\n".join(html)

    def _export_to_json(self) -> str:
        """Exports in JSON format"""
        data = {
            "scan_info": {
                "scan_path": str(self._last_scan_path)
                if self._last_scan_path
                else None,
                "total_entries": len(self._entries),
                "total_files": len(self._entries_by_file),
            },
            "files": [],
        }

        for file_path, entries in self._entries_by_file.items():
            file_data = {
                "file_path": str(file_path),
                "entries": [
                    {"description": entry.description, "url": entry.url}
                    for entry in entries
                ],
            }
            data["files"].append(file_data)

        return json.dumps(data, indent=2, ensure_ascii=False)
