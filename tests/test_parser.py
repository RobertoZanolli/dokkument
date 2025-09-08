"""
Tests for the parser module
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from dokkument.parser import (
    DokkEntry,
    StandardDokkParser,
    DokkParserFactory,
    DokkFileScanner,
    ParseError,
)


class TestDokkEntry:
    """Tests for the DokkEntry class"""

    def test_valid_entry_creation(self):
        """Test valid entry creation"""
        entry = DokkEntry(
            "Documentazione API", "https://api.example.com/docs", Path("/tmp/test.dokk")
        )
        assert entry.description == "Documentazione API"
        assert entry.url == "https://api.example.com/docs"
        assert entry.file_path == Path("/tmp/test.dokk")

    def test_entry_strips_whitespace(self):
        """Test che l'entry rimuova spazi bianchi in eccesso"""
        entry = DokkEntry(
            "  Documentazione API  ",
            "  https://api.example.com/docs  ",
            Path("/tmp/test.dokk"),
        )
        assert entry.description == "Documentazione API"
        assert entry.url == "https://api.example.com/docs"

    def test_empty_description_raises_error(self):
        """Test that empty description raises error"""
        with pytest.raises(ParseError):
            DokkEntry("", "https://api.example.com/docs", Path("/tmp/test.dokk"))

    def test_empty_url_raises_error(self):
        """Test that empty URL raises error"""
        with pytest.raises(ParseError):
            DokkEntry("Documentazione API", "", Path("/tmp/test.dokk"))

    def test_invalid_url_scheme_raises_error(self):
        """Test that invalid URL scheme raises error"""
        with pytest.raises(ParseError):
            DokkEntry("Documentazione API", "ftp://example.com", Path("/tmp/test.dokk"))

    def test_entry_string_representation(self):
        """Test rappresentazione string dell'entry"""
        entry = DokkEntry("Test", "https://example.com", Path("/tmp/test.dokk"))
        assert str(entry) == "Test -> https://example.com"


class TestStandardDokkParser:
    """Tests for the standard parser"""

    def setup_method(self):
        """Setup per ogni test"""
        self.parser = StandardDokkParser()

    def test_can_handle_dokk_files(self):
        """Test che il parser riconosca i file .dokk"""
        assert self.parser.can_handle(Path("test.dokk"))
        assert self.parser.can_handle(Path("TEST.DOKK"))
        assert not self.parser.can_handle(Path("test.txt"))
        assert not self.parser.can_handle(Path("test.md"))

    def test_parse_valid_file(self):
        """Test parsing di file valido"""
        content = '''# Commento ignorato
"Documentazione API" -> "https://api.example.com/docs"
"Repository GitLab" -> "https://gitlab.com/company/project"

# Altro commento
"Dashboard Monitoring" -> "https://grafana.example.com"'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".dokk", delete=False) as f:
            f.write(content)
            f.flush()

            entries = self.parser.parse(Path(f.name))
            assert len(entries) == 3

            assert entries[0].description == "Documentazione API"
            assert entries[0].url == "https://api.example.com/docs"

            assert entries[1].description == "Repository GitLab"
            assert entries[1].url == "https://gitlab.com/company/project"

            assert entries[2].description == "Dashboard Monitoring"
            assert entries[2].url == "https://grafana.example.com"

    def test_parse_file_with_invalid_format(self):
        """Test parsing di file con formato non valido"""
        content = """Formato non valido
"Documentazione API" -> "https://api.example.com/docs"
Questa riga non va bene"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".dokk", delete=False) as f:
            f.write(content)
            f.flush()

            with pytest.raises(ParseError, match="Invalid format"):
                self.parser.parse(Path(f.name))

    def test_parse_empty_file(self):
        """Test parsing di file vuoto"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dokk", delete=False) as f:
            f.write("")
            f.flush()

            entries = self.parser.parse(Path(f.name))
            assert len(entries) == 0

    def test_parse_file_with_only_comments(self):
        """Test parsing di file con solo commenti"""
        content = """# Solo commenti
# Nessuna entry valida
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".dokk", delete=False) as f:
            f.write(content)
            f.flush()

            entries = self.parser.parse(Path(f.name))
            assert len(entries) == 0

    def test_parse_nonexistent_file(self):
        """Test parsing di file inesistente"""
        with pytest.raises(FileNotFoundError):
            self.parser.parse(Path("/nonexistent/file.dokk"))


class TestDokkParserFactory:
    """Tests for the parser factory"""

    def setup_method(self):
        """Setup per ogni test"""
        self.factory = DokkParserFactory()

    def test_create_parser_for_dokk_file(self):
        """Test parser creation for .dokk file"""
        parser = self.factory.create_parser(Path("test.dokk"))
        assert parser is not None
        assert isinstance(parser, StandardDokkParser)

    def test_create_parser_for_unsupported_file(self):
        """Test parser creation for unsupported file"""
        parser = self.factory.create_parser(Path("test.txt"))
        assert parser is None

    def test_parse_file_success(self):
        """Test parsing file con successo"""
        content = '"Test" -> "https://example.com"'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".dokk", delete=False) as f:
            f.write(content)
            f.flush()

            entries = self.factory.parse_file(Path(f.name))
            assert len(entries) == 1
            assert entries[0].description == "Test"
            assert entries[0].url == "https://example.com"

    def test_parse_file_no_parser(self):
        """Test parsing file senza parser disponibile"""
        with pytest.raises(ParseError, match="No parser available"):
            self.factory.parse_file(Path("test.txt"))


class TestDokkFileScanner:
    """Tests for the file scanner"""

    def setup_method(self):
        """Setup per ogni test"""
        self.scanner = DokkFileScanner()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Cleanup dopo ogni test"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_scan_directory_with_dokk_files(self):
        """Test directory scanning with .dokk files"""
        # Create test file
        (self.temp_dir / "test1.dokk").write_text('"Link 1" -> "https://example1.com"')
        (self.temp_dir / "test2.dokk").write_text('"Link 2" -> "https://example2.com"')
        (self.temp_dir / "other.txt").write_text("Not a dokk file")

        results = self.scanner.scan_directory(self.temp_dir, recursive=False)

        assert len(results) == 2

        # Verifica che entrambi i file siano stati trovati
        file_names = [path.name for path in results.keys()]
        assert "test1.dokk" in file_names
        assert "test2.dokk" in file_names

        # Verifica le entry
        total_entries = sum(len(entries) for entries in results.values())
        assert total_entries == 2

    def test_scan_directory_recursive(self):
        """Test recursive scanning"""
        # Create directory structure
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()

        (self.temp_dir / "root.dokk").write_text('"Root Link" -> "https://root.com"')
        (subdir / "sub.dokk").write_text('"Sub Link" -> "https://sub.com"')

        results = self.scanner.scan_directory(self.temp_dir, recursive=True)
        assert len(results) == 2

        results_non_recursive = self.scanner.scan_directory(
            self.temp_dir, recursive=False
        )
        assert len(results_non_recursive) == 1

    def test_scan_nonexistent_directory(self):
        """Test scanning non-existent directory"""
        with pytest.raises(FileNotFoundError):
            self.scanner.scan_directory(Path("/nonexistent/directory"))

    def test_get_all_entries(self):
        """Test ottenimento di tutte le entry"""
        (self.temp_dir / "test1.dokk").write_text('"Link 1" -> "https://example1.com"')
        (self.temp_dir / "test2.dokk").write_text('"Link 2" -> "https://example2.com"')

        all_entries = self.scanner.get_all_entries(self.temp_dir)
        assert len(all_entries) == 2
        assert all(isinstance(entry, DokkEntry) for entry in all_entries)


# Test di integrazione
class TestIntegration:
    """Test di integrazione tra i componenti"""

    def test_full_workflow(self):
        """Test complete workflow: file creation -> scanning -> parsing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create .dokk file with valid content
            dokk_content = '''# File di documentazione
"Documentazione API" -> "https://api.example.com/docs"
"Repository GitLab" -> "https://gitlab.com/company/project"
"Dashboard Monitoring" -> "https://grafana.example.com"'''

            dokk_file = temp_path / "documentation.dokk"
            dokk_file.write_text(dokk_content)

            # Usa scanner per trovare e parsare
            scanner = DokkFileScanner()
            results = scanner.scan_directory(temp_path)

            assert len(results) == 1
            assert dokk_file in results

            entries = results[dokk_file]
            assert len(entries) == 3

            # Verifica le entry
            descriptions = [entry.description for entry in entries]
            assert "Documentazione API" in descriptions
            assert "Repository GitLab" in descriptions
            assert "Dashboard Monitoring" in descriptions
