"""
DokkFileParser - Parser for .dokk with Factory pattern
Manages reading and interpreting .dokk files for the dokkument project
"""

import re
from pathlib import Path
from typing import List, Optional, Dict
from abc import ABC, abstractmethod


class ParseError(Exception):
    """Exception raised when a parsing error occurs"""


class DokkEntry:
    """Represents a single entry in the .dokk file"""

    def __init__(self, description: str, url: str, file_path: Path):
        self.description = description.strip()
        self.url = url.strip()
        self.file_path = file_path
        self._validate()

    def _validate(self):
        """Validates the entry to ensure it is correct"""
        if not self.description:
            raise ParseError(f"Empty description in {self.file_path}")
        if not self.url:
            raise ParseError(f"Empty URL for '{self.description}' in {self.file_path}")
        if not self.url.startswith(("http://", "https://")):
            raise ParseError(
                f"Invalid URL '{self.url}' for '{self.description}' in {self.file_path}"
            )

    def __str__(self):
        return f"{self.description} -> {self.url}"

    def __repr__(self):
        return (
            f"DokkEntry(description='{self.description}', "
            f"url='{self.url}', file_path='{self.file_path}')"
        )


class BaseParser(ABC):
    """Abstract base class for .dokk file parsers"""

    @abstractmethod
    def parse(self, file_path: Path) -> List[DokkEntry]:
        """Parses a .dokk file and returns a list of DokkEntry"""

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Determines if this parser can handle the specified file."""


class StandardDokkParser(BaseParser):
    """Standard parser for .dokk files in the format: "Description" -> "URL" """

    PATTERN = re.compile(r'"([^"]+)"\s*->\s*"([^"]+)"')

    def can_handle(self, file_path: Path) -> bool:
        """Checks if the file has a .dokk extension"""
        return file_path.suffix.lower() == ".dokk"

    def parse(self, file_path: Path) -> List[DokkEntry]:
        """
        Parses a .dokk file in the standard format

        Args:
            file_path: Path of the file to parse

        Returns:
            List[DokkEntry]: List of found entries

        Raises:
            ParseError: If the file cannot be parsed or contains errors
            FileNotFoundError: If the file does not exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ParseError(f"The specified path is not a file: {file_path}")

        entries = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception as fallback_error:
                raise ParseError(
                    f"Unable to read file {file_path}: {fallback_error}"
                ) from fallback_error
        except OSError as os_error:
            raise ParseError(f"Error reading file {file_path}: {os_error}") from os_error

        line_number = 0
        for line in content.splitlines():
            line_number += 1
            line = line.strip()

            # Ignore empty lines and comments
            if not line or line.startswith("#"):
                continue

            match = self.PATTERN.match(line)
            if match:
                description, url = match.groups()
                try:
                    entry = DokkEntry(description, url, file_path)
                    entries.append(entry)
                except ParseError as e:
                    raise ParseError(
                        f"Error at line {line_number} in {file_path}: {e}"
                    ) from e
            else:
                raise ParseError(
                    f"Invalid format at line {line_number} in {file_path}: {line}"
                )

        return entries


class DokkParserFactory:
    """Factory to create appropriate parsers for .dokk files"""

    def __init__(self):
        self._parsers: List[BaseParser] = [
            StandardDokkParser(),
        ]

    def register_parser(self, parser: BaseParser):
        """Registers a new custom parser"""
        self._parsers.insert(0, parser)  # Custom parsers have priority

    def create_parser(self, file_path: Path) -> Optional[BaseParser]:
        """
        Creates the appropriate parser for the specified file

        Args:
            file_path: Path of the file to parse

        Returns:
            BaseParser: Appropriate parser or None if no parser can handle the file
        """
        for parser in self._parsers:
            if parser.can_handle(file_path):
                return parser
        return None

    def parse_file(self, file_path: Path) -> List[DokkEntry]:
        """
        Parses a file using the appropriate parser

        Args:
            file_path: Path of the file to parse

        Returns:
            List[DokkEntry]: List of found entries

        Raises:
            ParseError: If the file cannot be parsed
        """
        parser = self.create_parser(file_path)
        if parser is None:
            raise ParseError(f"No parser available for file: {file_path}")

        return parser.parse(file_path)


class DokkFileScanner:
    """Scanner to find all .dokk files in a directory and subdirectories"""

    def __init__(self, parser_factory: DokkParserFactory = None):
        self.parser_factory = parser_factory or DokkParserFactory()

    def scan_directory(
        self, root_path: Path, recursive: bool = True
    ) -> Dict[Path, List[DokkEntry]]:
        """
        Scans a directory to find all .dokk files

        Args:
            root_path: Root directory to scan
            recursive: If True, also scans subdirectories

        Returns:
            Dict[Path, List[DokkEntry]]: Dictionary with file path as key and
                list of entries as value
        """
        if not root_path.exists():
            raise FileNotFoundError(f"Directory not found: {root_path}")

        if not root_path.is_dir():
            raise NotADirectoryError(
                f"The specified path is not a directory: {root_path}"
            )

        results = {}
        pattern = "**/*.dokk" if recursive else "*.dokk"

        for file_path in root_path.glob(pattern):
            try:
                entries = self.parser_factory.parse_file(file_path)
                if entries:  # Only if there are valid entries
                    results[file_path] = entries
            except Exception as parse_error:  # pylint: disable=broad-except
                # Log the error but continue scanning
                print(f"Warning: Error parsing {file_path}: {parse_error}")
                continue

        return results

    def get_all_entries(
        self, root_path: Path, recursive: bool = True
    ) -> List[DokkEntry]:
        """
        Gets all entries from all found .dokk files

        Args:
            root_path: Root directory to scan
            recursive: If True, also scans subdirectories

        Returns:
            List[DokkEntry]: List of all found entries
        """
        file_entries = self.scan_directory(root_path, recursive)
        all_entries = []

        for entries in file_entries.values():
            all_entries.extend(entries)

        return all_entries
