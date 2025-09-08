"""
Tests for the cli_display module
"""

import pytest
from io import StringIO
from pathlib import Path
from unittest.mock import patch, Mock

from dokkument.cli_display import CLIDisplay
from dokkument.link_manager import LinkManager
from dokkument.parser import DokkEntry


class TestCLIDisplay:
    """Tests for the CLIDisplay class"""
    
    def setup_method(self):
        """Setup per ogni test"""
        self.mock_link_manager = Mock(spec=LinkManager)
        self.cli_display = CLIDisplay(self.mock_link_manager)
    
    def test_color_support_check(self):
        """Test verifica supporto colori"""
        # Il supporto colore dipende dall'ambiente, verifichiamo solo che il metodo esista
        assert hasattr(self.cli_display, 'supports_color')
        assert isinstance(self.cli_display.supports_color, bool)
    
    def test_hyperlink_support_check(self):
        """Test verifica supporto hyperlink"""
        assert hasattr(self.cli_display, 'supports_hyperlinks')
        assert isinstance(self.cli_display.supports_hyperlinks, bool)
    
    def test_colorize_with_color_support(self):
        """Test colorizzazione con supporto colori"""
        # Force color support for testing
        self.cli_display.supports_color = True
        # Use the mapping actually used by colorize
        self.cli_display.colors = {'success': '\033[1;32m', 'reset': '\033[0m'}
        
        result = self.cli_display.colorize("Test", 'success')
        assert '\033[1;32m' in result
        assert 'Test' in result
        assert '\033[0m' in result
    
    def test_colorize_without_color_support(self):
        """Test colorizzazione senza supporto colori"""
        # Force no color support
        self.cli_display.supports_color = False
        self.cli_display.colors = {key: '' for key in self.cli_display.colors}
        
        result = self.cli_display.colorize("Test", 'success')
        assert result == "Test"
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_header(self, mock_stdout):
        """Test stampa header"""
        self.cli_display.print_header("Test Title")
        
        output = mock_stdout.getvalue()
        assert "Test Title" in output
        assert "=" in output  # Header decoration
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_scanning_message(self, mock_stdout):
        """Test scanning message"""
        test_path = Path("/test/path")
        self.cli_display.print_scanning_message(test_path)
 
        output = mock_stdout.getvalue()
        assert str(test_path) in output
        assert "Scanning" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_scan_results_with_links(self, mock_stdout):
        """Test scan results with found links"""
        self.cli_display.print_scan_results(5, 2)
 
        output = mock_stdout.getvalue()
        assert "Found 5 links in 2 files" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_scan_results_no_links(self, mock_stdout):
        """Test scan results without links"""
        self.cli_display.print_scan_results(0, 0)
 
        output = mock_stdout.getvalue()
        assert "No .dokk files found" in output
        assert "format:" in output  # format hint
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_menu_with_entries(self, mock_stdout):
        """Test stampa menu con entry"""
        # Create mock entries
        mock_entry1 = Mock(spec=DokkEntry)
        mock_entry1.description = "Test Entry 1"
        mock_entry1.url = "https://example1.com"
        mock_entry1.file_path = Path("test1.dokk")
        
        mock_entry2 = Mock(spec=DokkEntry)
        mock_entry2.description = "Test Entry 2"
        mock_entry2.url = "https://example2.com"
        mock_entry2.file_path = Path("test2.dokk")
        
        entries = [mock_entry1, mock_entry2]
        
        # Configure link manager mocks
        self.mock_link_manager.get_colored_description.side_effect = lambda entry: entry.description
        self.mock_link_manager.get_colored_url.side_effect = lambda entry, _: entry.url
        
        self.cli_display.print_menu(entries, show_files=False)
 
        output = mock_stdout.getvalue()
        assert "Test Entry 1" in output
        assert "Test Entry 2" in output
        assert "[ 1]" in output
        assert "[ 2]" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_menu_empty(self, mock_stdout):
        """Test stampa menu vuoto"""
        self.cli_display.print_menu([])
 
        output = mock_stdout.getvalue()
        assert "No links available" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_menu_footer(self, mock_stdout):
        """Test stampa footer del menu"""
        self.cli_display.print_menu_footer(5)
 
        output = mock_stdout.getvalue()
        assert "1-5" in output  # Range opzioni
        assert "Available options" in output
        assert "Open all" in output
        assert "Exit" in output
    
    @patch('builtins.input', return_value='test input')
    def test_get_user_input(self, mock_input):
        """Test ottenimento input utente"""
        result = self.cli_display.get_user_input("Test prompt")
        assert result == "test input"
    
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_get_user_input_keyboard_interrupt(self, mock_input):
        """Test gestione KeyboardInterrupt nell'input"""
        result = self.cli_display.get_user_input()
        assert result == 'q'  # Should return 'q' to quit
    
    @patch('builtins.input', side_effect=EOFError)
    def test_get_user_input_eof_error(self, mock_input):
        """Test gestione EOFError nell'input"""
        result = self.cli_display.get_user_input()
        assert result == 'q'  # Should return 'q' to quit
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_opening_message(self, mock_stdout):
        """Test messaggio apertura link"""
        mock_entry = Mock(spec=DokkEntry)
        mock_entry.description = "Test Link"
        mock_entry.url = "https://example.com"
        
        self.cli_display.print_opening_message(mock_entry)
 
        output = mock_stdout.getvalue()
        assert "Test Link" in output
        assert "https://example.com" in output
        assert "Opening" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_opening_all_message(self, mock_stdout):
        """Test messaggio apertura tutti i link"""
        self.cli_display.print_opening_all_message(10)
 
        output = mock_stdout.getvalue()
        assert "10 link" in output
        assert "Opening all" in output
        assert "many browser tabs" in output  # Warning
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_success_message(self, mock_stdout):
        """Test messaggio di successo"""
        self.cli_display.print_success_message("Operazione completata")
        
        output = mock_stdout.getvalue()
        assert "Operazione completata" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_error_message(self, mock_stdout):
        """Test error message"""
        self.cli_display.print_error_message("Test error")
        
        output = mock_stdout.getvalue()
        assert "Test error" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_warning_message(self, mock_stdout):
        """Test messaggio di avviso"""
        self.cli_display.print_warning_message("Avviso test")
        
        output = mock_stdout.getvalue()
        assert "Avviso test" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_info_message(self, mock_stdout):
        """Test messaggio informativo"""
        self.cli_display.print_info_message("Info test")
        
        output = mock_stdout.getvalue()
        assert "Info test" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_statistics(self, mock_stdout):
        """Test stampa statistiche"""
        stats = {
            'total_files': 3,
            'total_links': 10,
            'unique_domains': 5
        }
        
        self.cli_display.print_statistics(stats)
 
        output = mock_stdout.getvalue()
        assert "Statistics" in output
        assert "3" in output  # total_files
        assert "10" in output  # total_links
        assert "5" in output  # unique_domains
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_help(self, mock_stdout):
        """Test stampa aiuto"""
        self.cli_display.print_help()
 
        output = mock_stdout.getvalue()
        assert "Help" in output
        assert "File .dokk format" in output
        assert "Available commands" in output
        assert ".dokk" in output
    
    @patch('builtins.input', return_value='s')
    def test_confirm_action_yes(self, mock_input):
        """Test conferma azione - si"""
        result = self.cli_display.confirm_action("Continuare?")
        assert result is True
    
    @patch('builtins.input', return_value='n')
    def test_confirm_action_no(self, mock_input):
        """Test conferma azione - no"""
        result = self.cli_display.confirm_action("Continuare?")
        assert result is False
    
    @patch('builtins.input', return_value='')
    def test_confirm_action_default_true(self, mock_input):
        """Test conferma azione - default True"""
        result = self.cli_display.confirm_action("Continuare?", default=True)
        assert result is True
    
    @patch('builtins.input', return_value='')
    def test_confirm_action_default_false(self, mock_input):
        """Test conferma azione - default False"""
        result = self.cli_display.confirm_action("Continuare?", default=False)
        assert result is False
    
    @patch('builtins.input', return_value='invalid')
    def test_confirm_action_invalid_input(self, mock_input):
        """Test conferma azione - input non valido"""
        result = self.cli_display.confirm_action("Continuare?", default=True)
        assert result is True  # Should return default
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_farewell(self, mock_stdout):
        """Test messaggio di addio"""
        self.cli_display.print_farewell()
 
        output = mock_stdout.getvalue()
        assert "Goodbye" in output
        assert "dokkument" in output
    
    def test_clear_screen(self):
        """Test pulizia schermo"""
        # Questo test verifica solo che il metodo non sollevi eccezioni
        try:
            self.cli_display.clear_screen()
        except Exception as e:
            pytest.fail(f"clear_screen raised an exception: {e}")


class TestCLIDisplayIntegration:
    """Test di integrazione per CLIDisplay"""
    
    def setup_method(self):
        """Setup per ogni test di integrazione"""
        self.link_manager = Mock(spec=LinkManager)
        self.cli_display = CLIDisplay(self.link_manager)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_full_menu_workflow(self, mock_stdout):
        """Test workflow completo del menu"""
        # Setup mock entries
        mock_entry = Mock(spec=DokkEntry)
        mock_entry.description = "Test Entry"
        mock_entry.url = "https://example.com"
        mock_entry.file_path = Path("test.dokk")
        
        entries = [mock_entry]
        
        # Configure link manager
        self.link_manager.get_colored_description.return_value = "Test Entry"
        self.link_manager.get_colored_url.return_value = "https://example.com"
        
        # Test complete menu display
        self.cli_display.print_header("Test Application")
        self.cli_display.print_scan_results(1, 1)
        self.cli_display.print_menu(entries, show_files=False)
        self.cli_display.print_menu_footer(1)
        
        output = mock_stdout.getvalue()
        
        # Verify all components are present
        assert "Test Application" in output
        assert "1 link" in output
        assert "Test Entry" in output
        assert "[ 1]" in output
        assert "Available options" in output