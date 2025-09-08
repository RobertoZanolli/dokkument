"""
Tests for the link_manager module
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from dokkument.link_manager import LinkManager
from dokkument.parser import DokkEntry, DokkFileScanner


class TestLinkManager:
    """Tests for the LinkManager class"""

    def setup_method(self):
        """Setup for each test"""
        self.link_manager = LinkManager()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Cleanup after each test"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_scan_for_links_success(self):
        """Test successful link scanning"""
        # Create test file
        (self.temp_dir / "test.dokk").write_text('"Test Link" -> "https://example.com"')

        total_links = self.link_manager.scan_for_links(self.temp_dir)

        assert total_links == 1
        entries = self.link_manager.get_all_entries()
        assert len(entries) == 1
        assert entries[0].description == "Test Link"
        assert entries[0].url == "https://example.com"

    def test_scan_for_links_multiple_files(self):
        """Test scanning with multiple files"""
        (self.temp_dir / "file1.dokk").write_text('"Link 1" -> "https://example1.com"')
        (self.temp_dir / "file2.dokk").write_text('"Link 2" -> "https://example2.com"')

        total_links = self.link_manager.scan_for_links(self.temp_dir)

        assert total_links == 2
        entries_by_file = self.link_manager.get_entries_by_file()
        assert len(entries_by_file) == 2

    def test_scan_for_links_no_files(self):
        """Test scanning without .dokk files"""
        total_links = self.link_manager.scan_for_links(self.temp_dir)

        assert total_links == 0
        assert len(self.link_manager.get_all_entries()) == 0

    def test_get_entry_by_index(self):
        """Test ottenimento entry per indice"""
        (self.temp_dir / "test.dokk").write_text(
            '"Link 1" -> "https://example1.com"\n"Link 2" -> "https://example2.com"'
        )

        self.link_manager.scan_for_links(self.temp_dir)

        # Test indici validi (1-based)
        entry1 = self.link_manager.get_entry_by_index(1)
        entry2 = self.link_manager.get_entry_by_index(2)

        assert entry1 is not None
        assert entry1.description == "Link 1"
        assert entry2 is not None
        assert entry2.description == "Link 2"

        # Test indici non validi
        assert self.link_manager.get_entry_by_index(0) is None
        assert self.link_manager.get_entry_by_index(3) is None
        assert self.link_manager.get_entry_by_index(-1) is None

    def test_color_assignment(self):
        """Test assegnazione colori ai file"""
        (self.temp_dir / "file1.dokk").write_text('"Link 1" -> "https://example1.com"')
        (self.temp_dir / "file2.dokk").write_text('"Link 2" -> "https://example2.com"')

        self.link_manager.scan_for_links(self.temp_dir)

        entries_by_file = self.link_manager.get_entries_by_file()
        files = list(entries_by_file.keys())

        # Ogni file dovrebbe avere un colore assegnato
        color1 = self.link_manager.get_file_color(files[0])
        color2 = self.link_manager.get_file_color(files[1])

        assert color1 != ""
        assert color2 != ""
        # I colori dovrebbero essere diversi (se ci sono abbastanza colori)
        assert color1 != color2

    def test_colored_description(self):
        """Test descrizione colorata"""
        (self.temp_dir / "test.dokk").write_text('"Test Link" -> "https://example.com"')

        self.link_manager.scan_for_links(self.temp_dir)
        entry = self.link_manager.get_all_entries()[0]

        colored_desc = self.link_manager.get_colored_description(entry)

        # Dovrebbe contenere il colore ANSI e il reset
        assert "Test Link" in colored_desc
        assert (
            "\033[" in colored_desc or colored_desc == "Test Link"
        )  # Fallback se no color

    def test_colored_url(self):
        """Test URL colorato"""
        (self.temp_dir / "test.dokk").write_text('"Test Link" -> "https://example.com"')

        self.link_manager.scan_for_links(self.temp_dir)
        entry = self.link_manager.get_all_entries()[0]

        # Test URL normale
        colored_url = self.link_manager.get_colored_url(entry, make_clickable=False)
        assert "https://example.com" in colored_url

        # Test URL cliccabile
        clickable_url = self.link_manager.get_colored_url(entry, make_clickable=True)
        assert "https://example.com" in clickable_url

    def test_filter_entries(self):
        """Test filtro delle entry"""
        (self.temp_dir / "test.dokk").write_text(
            '"API Documentation" -> "https://api.example.com"\n'
            '"User Guide" -> "https://guide.example.com"\n'
            '"API Reference" -> "https://ref.example.com"'
        )

        self.link_manager.scan_for_links(self.temp_dir)

        # Filtra per "API"
        api_entries = self.link_manager.filter_entries("API")
        assert len(api_entries) == 2
        assert all("API" in entry.description for entry in api_entries)

        # Filtra per termine non esistente
        no_entries = self.link_manager.filter_entries("NonExistent")
        assert len(no_entries) == 0

        # Test case-insensitive
        case_entries = self.link_manager.filter_entries("api")
        assert len(case_entries) == 2

    def test_statistics(self):
        """Test generazione statistiche"""
        (self.temp_dir / "file1.dokk").write_text(
            '"Link 1" -> "https://example.com"\n"Link 2" -> "https://github.com/test"'
        )
        (self.temp_dir / "file2.dokk").write_text('"Link 3" -> "https://example.com"')

        self.link_manager.scan_for_links(self.temp_dir)
        stats = self.link_manager.get_statistics()

        assert stats["total_links"] == 3
        assert stats["total_files"] == 2
        assert stats["unique_domains"] == 2  

    def test_validate_all_links(self):
        """Test validazione di tutti i link"""
        (self.temp_dir / "test.dokk").write_text(
            '"Valid Link" -> "https://example.com"\n"Invalid Link" -> "not-a-url"'
        )

        self.link_manager.scan_for_links(self.temp_dir)
        invalid_links = self.link_manager.validate_all_links()

        assert len(invalid_links) == 0

    def test_export_to_text(self):
        """Test esportazione in formato testo"""
        (self.temp_dir / "test.dokk").write_text('"Test Link" -> "https://example.com"')

        self.link_manager.scan_for_links(self.temp_dir)
        text_export = self.link_manager.export_to_format("text")

        assert "Documentation Links" in text_export
        assert "Test Link" in text_export
        assert "https://example.com" in text_export

    def test_export_to_markdown(self):
        """Test esportazione in formato Markdown"""
        (self.temp_dir / "test.dokk").write_text('"Test Link" -> "https://example.com"')

        self.link_manager.scan_for_links(self.temp_dir)
        md_export = self.link_manager.export_to_format("markdown")

        assert "# Documentation Links" in md_export
        assert "[Test Link](https://example.com)" in md_export

    def test_export_to_html(self):
        """Test esportazione in formato HTML"""
        (self.temp_dir / "test.dokk").write_text('"Test Link" -> "https://example.com"')

        self.link_manager.scan_for_links(self.temp_dir)
        html_export = self.link_manager.export_to_format("html")

        assert "<!DOCTYPE html>" in html_export
        assert '<a href="https://example.com">Test Link</a>' in html_export

    def test_export_to_json(self):
        """Test esportazione in formato JSON"""
        (self.temp_dir / "test.dokk").write_text('"Test Link" -> "https://example.com"')

        self.link_manager.scan_for_links(self.temp_dir)
        json_export = self.link_manager.export_to_format("json")

        import json

        data = json.loads(json_export)

        assert "scan_info" in data
        assert "files" in data
        assert data["scan_info"]["total_entries"] == 1
        assert len(data["files"]) == 1
        assert data["files"][0]["entries"][0]["description"] == "Test Link"

    def test_export_unsupported_format(self):
        """Test esportazione formato non supportato"""
        with pytest.raises(ValueError, match="Unsupported format"):
            self.link_manager.export_to_format("unsupported")

    @patch("dokkument.link_manager.DokkFileScanner")
    def test_scan_error_handling(self, mock_scanner_class):
        """Test error handling during scanning"""
        # Configura il mock per sollevare un'eccezione
        mock_scanner = Mock()
        mock_scanner.scan_directory.side_effect = Exception("Test error")
        mock_scanner_class.return_value = mock_scanner

        link_manager = LinkManager()

        with pytest.raises(RuntimeError, match="Error during scanning"):
            link_manager.scan_for_links(self.temp_dir)

    def test_empty_statistics(self):
        """Test statistiche con nessun link"""
        stats = self.link_manager.get_statistics()

        assert stats["total_links"] == 0
        assert stats["total_files"] == 0
        assert stats["unique_domains"] == 0
