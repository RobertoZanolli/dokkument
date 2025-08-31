"""
DokkFileParser - Parser per file .dokk con pattern Factory
Gestisce la lettura e interpretazione dei file .dokk per il progetto dokkument
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod


class ParseError(Exception):
    """Eccezione sollevata quando si verifica un errore di parsing"""

    pass


class DokkEntry:
    """Rappresenta una singola entry del file .dokk"""

    def __init__(self, description: str, url: str, file_path: Path):
        self.description = description.strip()
        self.url = url.strip()
        self.file_path = file_path
        self._validate()

    def _validate(self):
        """Valida l'entry per assicurarsi che sia corretta"""
        if not self.description:
            raise ParseError(f"Descrizione vuota in {self.file_path}")
        if not self.url:
            raise ParseError(f"URL vuoto per '{self.description}' in {self.file_path}")
        if not self.url.startswith(("http://", "https://")):
            raise ParseError(
                f"URL non valido '{self.url}' per '{self.description}' in {self.file_path}"
            )

    def __str__(self):
        return f"{self.description} -> {self.url}"

    def __repr__(self):
        return f"DokkEntry(description='{self.description}', url='{self.url}', file_path='{self.file_path}')"


class BaseParser(ABC):
    """Classe base astratta per i parser di file .dokk"""

    @abstractmethod
    def parse(self, file_path: Path) -> List[DokkEntry]:
        """Parsa un file .dokk e restituisce una lista di DokkEntry"""
        pass

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Determina se questo parser puo gestire il file specificato."""
        pass


class StandardDokkParser(BaseParser):
    """Parser standard per file .dokk nel formato: "Descrizione" -> "URL" """

    PATTERN = re.compile(r'"([^"]+)"\s*->\s*"([^"]+)"')

    def can_handle(self, file_path: Path) -> bool:
        """Controlla se il file ha estensione .dokk"""
        return file_path.suffix.lower() == ".dokk"

    def parse(self, file_path: Path) -> List[DokkEntry]:
        """
        Parsa un file .dokk nel formato standard

        Args:
            file_path: Path del file da parsare

        Returns:
            List[DokkEntry]: Lista delle entry trovate

        Raises:
            ParseError: Se il file non puo essere parsato o contiene errori
            FileNotFoundError: Se il file non esiste
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")

        if not file_path.is_file():
            raise ParseError(f"Il path specificato non e un file: {file_path}")

        entries = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception as e:
                raise ParseError(f"Impossibile leggere il file {file_path}: {e}")
        except Exception as e:
            raise ParseError(f"Errore nella lettura del file {file_path}: {e}")

        line_number = 0
        for line in content.splitlines():
            line_number += 1
            line = line.strip()

            # Ignora righe vuote e commenti
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
                        f"Errore alla riga {line_number} di {file_path}: {e}"
                    )
            else:
                raise ParseError(
                    f"Formato non valido alla riga {line_number} di {file_path}: {line}"
                )

        return entries


class DokkParserFactory:
    """Factory per creare parser appropriati per i file .dokk"""

    def __init__(self):
        self._parsers: List[BaseParser] = [
            StandardDokkParser(),
        ]

    def register_parser(self, parser: BaseParser):
        """Registra un nuovo parser personalizzato"""
        self._parsers.insert(0, parser)  # I parser personalizzati hanno priorita

    def create_parser(self, file_path: Path) -> Optional[BaseParser]:
        """
        Crea il parser appropriato per il file specificato

        Args:
            file_path: Path del file da parsare

        Returns:
            BaseParser: Parser appropriato o None se nessun parser puo gestire il file
        """
        for parser in self._parsers:
            if parser.can_handle(file_path):
                return parser
        return None

    def parse_file(self, file_path: Path) -> List[DokkEntry]:
        """
        Parsa un file utilizzando il parser appropriato

        Args:
            file_path: Path del file da parsare

        Returns:
            List[DokkEntry]: Lista delle entry trovate

        Raises:
            ParseError: Se il file non puo essere parsato
        """
        parser = self.create_parser(file_path)
        if parser is None:
            raise ParseError(f"Nessun parser disponibile per il file: {file_path}")

        return parser.parse(file_path)


class DokkFileScanner:
    """Scanner per trovare tutti i file .dokk in una directory e sottodirectory"""

    def __init__(self, parser_factory: DokkParserFactory = None):
        self.parser_factory = parser_factory or DokkParserFactory()

    def scan_directory(
        self, root_path: Path, recursive: bool = True
    ) -> Dict[Path, List[DokkEntry]]:
        """
        Scansiona una directory per trovare tutti i file .dokk

        Args:
            root_path: Directory radice da scansionare
            recursive: Se True, scansiona anche le sottodirectory

        Returns:
            Dict[Path, List[DokkEntry]]: Dizionario con path del file come chiave e lista di entry come valore
        """
        if not root_path.exists():
            raise FileNotFoundError(f"Directory non trovata: {root_path}")

        if not root_path.is_dir():
            raise NotADirectoryError(
                f"Il path specificato non e una directory: {root_path}"
            )

        results = {}
        pattern = "**/*.dokk" if recursive else "*.dokk"

        for file_path in root_path.glob(pattern):
            try:
                entries = self.parser_factory.parse_file(file_path)
                if entries:  # Solo se ci sono entry valide
                    results[file_path] = entries
            except Exception as e:
                # Log dell'errore ma continua la scansione
                print(f"Attenzione: Errore nel parsing di {file_path}: {e}")
                continue

        return results

    def get_all_entries(
        self, root_path: Path, recursive: bool = True
    ) -> List[DokkEntry]:
        """
        Ottiene tutte le entry da tutti i file .dokk trovati

        Args:
            root_path: Directory radice da scansionare
            recursive: Se True, scansiona anche le sottodirectory

        Returns:
            List[DokkEntry]: Lista di tutte le entry trovate
        """
        file_entries = self.scan_directory(root_path, recursive)
        all_entries = []

        for entries in file_entries.values():
            all_entries.extend(entries)

        return all_entries
