"""
Commands - Implementa il pattern Command per gestire i comandi dell'applicazione
Fornisce un'architettura flessibile per aggiungere nuovi comandi
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path

from .parser import DokkEntry
from .link_manager import LinkManager
from .browser_opener import BrowserOpener
from .cli_display import CLIDisplay
from .config_manager import get_config


class Command(ABC):
    """Classe base astratta per tutti i comandi"""

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
        Esegue il comando

        Returns:
            bool: True se il comando deve continuare il loop, False per uscire
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Restituisce la descrizione del comando"""
        pass


class OpenLinkCommand(Command):
    """Comando per aprire un singolo link"""

    def execute(self, index: int) -> bool:
        entry = self.link_manager.get_entry_by_index(index)
        if entry is None:
            self.cli_display.print_error_message(f"Numero non valido: {index}")
            return True

        self.cli_display.print_opening_message(entry)

        preferred_browser = self.config.get("browser.preferred_browser")
        success = self.browser_opener.open_url(entry.url, preferred_browser)

        if success:
            self.cli_display.print_success_message("Link aperto con successo!")
        else:
            self.cli_display.print_error_message("Impossibile aprire il link")

        return True

    def get_description(self) -> str:
        return "Apre un link specifico nel browser"


class OpenAllLinksCommand(Command):
    """Comando per aprire tutti i link"""

    def execute(self) -> bool:
        entries = self.link_manager.get_all_entries()
        if not entries:
            self.cli_display.print_warning_message("Nessun link da aprire")
            return True

        # Conferma se richiesta dalla configurazione
        if self.config.get("display.confirm_open_all", True):
            self.cli_display.print_opening_all_message(len(entries))
            if not self.cli_display.confirm_action("Continuare?"):
                self.cli_display.print_info_message("Operazione annullata")
                return True

        # Limita il numero di link aperti contemporaneamente
        max_concurrent = self.config.get("browser.max_concurrent_opens", 10)
        if len(entries) > max_concurrent:
            self.cli_display.print_warning_message(
                f"Troppi link ({len(entries)}), verranno aperti solo i primi {max_concurrent}"
            )
            entries = entries[:max_concurrent]

        # Apri tutti i link
        preferred_browser = self.config.get("browser.preferred_browser")
        delay = self.config.get("browser.open_delay_seconds", 0.5)

        urls = [entry.url for entry in entries]
        results = self.browser_opener.open_multiple_urls(urls, preferred_browser, delay)

        success_count = sum(1 for result in results if result)
        self.cli_display.print_success_message(
            f"Aperti {success_count} link su {len(entries)}"
        )

        return True

    def get_description(self) -> str:
        return "Apre tutti i link contemporaneamente"


class ListLinksCommand(Command):
    """Comando per mostrare solo la lista dei link"""

    def execute(self) -> bool:
        entries = self.link_manager.get_all_entries()
        show_files = self.config.get("display.group_by_file", True)

        self.cli_display.print_header("Lista Completa dei Link")
        self.cli_display.print_menu(entries, show_files)

        return True

    def get_description(self) -> str:
        return "Mostra la lista completa dei link senza aprirli"


class ReloadCommand(Command):
    """Comando per ricaricare/riscansionare i file .dokk"""

    def execute(self) -> bool:
        self.cli_display.print_info_message("Riscansionando i file .dokk...")

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

        except Exception as e:
            self.cli_display.print_error_message(f"Errore durante la riscansione: {e}")

        return True

    def get_description(self) -> str:
        return "Ricarica e riscansiona i file .dokk"


class StatisticsCommand(Command):
    """Comando per mostrare statistiche sui link"""

    def execute(self) -> bool:
        stats = self.link_manager.get_statistics()
        self.cli_display.print_statistics(stats)

        # Informazioni aggiuntive se richieste
        if self.config.get("advanced.debug_mode", False):
            entries_by_file = self.link_manager.get_entries_by_file()
            print("\n" + self.cli_display.colorize("=Dettagli Debug:", "info"))
            for file_path, entries in entries_by_file.items():
                print(f"  =� {file_path}: {len(entries)} link")

        return True

    def get_description(self) -> str:
        return "Mostra statistiche sui link trovati"


class HelpCommand(Command):
    """Comando per mostrare l'aiuto"""

    def execute(self) -> bool:
        self.cli_display.print_help()
        return True

    def get_description(self) -> str:
        return "Mostra l'aiuto dell'applicazione"


class ConfigCommand(Command):
    """Comando per gestire la configurazione"""

    def execute(self, action: str = "show") -> bool:
        if action == "show":
            self.config.print_config_info()
        elif action == "export":
            template_path = Path.cwd() / "dokkument-config-template.json"
            if self.config.export_config_template(template_path):
                self.cli_display.print_success_message(
                    f"Template esportato in: {template_path}"
                )
            else:
                self.cli_display.print_error_message(
                    "Errore nell'esportazione del template"
                )
        elif action == "validate":
            errors = self.config.validate_config()
            if errors:
                self.cli_display.print_error_message(
                    "Errori di configurazione trovati:"
                )
                for error in errors:
                    print(f"  - {error}")
            else:
                self.cli_display.print_success_message("Configurazione valida")

        return True

    def get_description(self) -> str:
        return "Gestisce la configurazione dell'applicazione"


class ValidateLinksCommand(Command):
    """Comando per validare tutti i link"""

    def execute(self) -> bool:
        self.cli_display.print_info_message("Validando tutti i link...")

        invalid_links = self.link_manager.validate_all_links()

        if invalid_links:
            self.cli_display.print_warning_message(
                f"Trovati {len(invalid_links)} link non validi:"
            )
            for entry, error in invalid_links:
                print(f"  L {entry.description}: {error}")
                print(f"     =� File: {entry.file_path}")
                print(f"     = URL: {entry.url}")
                print()
        else:
            self.cli_display.print_success_message("Tutti i link sono validi!")

        return True

    def get_description(self) -> str:
        return "Valida la correttezza di tutti i link"


class ExportCommand(Command):
    """Comando per esportare i link in vari formati"""

    def execute(
        self, format_type: str = "text", output_file: Optional[str] = None
    ) -> bool:
        try:
            content = self.link_manager.export_to_format(format_type)

            if output_file:
                output_path = Path(output_file)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.cli_display.print_success_message(
                    f"Link esportati in: {output_path}"
                )
            else:
                print(content)

        except ValueError as e:
            self.cli_display.print_error_message(f"Formato non supportato: {e}")
        except Exception as e:
            self.cli_display.print_error_message(f"Errore durante l'esportazione: {e}")

        return True

    def get_description(self) -> str:
        return "Esporta i link in vari formati (text, markdown, html, json)"


class SearchCommand(Command):
    """Comando per cercare link per descrizione"""

    def execute(self, search_term: str) -> bool:
        if not search_term.strip():
            self.cli_display.print_warning_message("Termine di ricerca vuoto")
            return True

        matching_entries = self.link_manager.filter_entries(search_term)

        if not matching_entries:
            self.cli_display.print_warning_message(
                f"Nessun link trovato per: '{search_term}'"
            )
        else:
            self.cli_display.print_header(f"Risultati ricerca: '{search_term}'")
            show_files = self.config.get("display.show_file_names", True)
            self.cli_display.print_menu(matching_entries, show_files)

        return True

    def get_description(self) -> str:
        return "Cerca link per termine nella descrizione"


class QuitCommand(Command):
    """Comando per uscire dall'applicazione"""

    def execute(self) -> bool:
        self.cli_display.print_farewell()
        return False  # Interrompe il loop principale

    def get_description(self) -> str:
        return "Esce dall'applicazione"


class CommandInvoker:
    """Invoker per il pattern Command - gestisce l'esecuzione dei comandi"""

    def __init__(
        self,
        link_manager: LinkManager,
        browser_opener: BrowserOpener,
        cli_display: CLIDisplay,
    ):
        self.link_manager = link_manager
        self.browser_opener = browser_opener
        self.cli_display = cli_display

        # Registra tutti i comandi disponibili
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
        Esegue un comando specifico

        Args:
            command_name: Nome del comando da eseguire
            *args, **kwargs: Argomenti da passare al comando

        Returns:
            bool: True per continuare, False per uscire
        """
        command = self.commands.get(command_name)
        if command:
            try:
                return command.execute(*args, **kwargs)  # type: ignore
            except Exception as e:
                self.cli_display.print_error_message(
                    f"Errore nell'esecuzione del comando: {e}"
                )
                return True
        else:
            self.cli_display.print_error_message(
                f"Comando non riconosciuto: {command_name}"
            )
            return True

    def get_available_commands(self) -> Dict[str, str]:
        """Restituisce un dizionario di comandi disponibili con le loro descrizioni"""
        return {name: cmd.get_description() for name, cmd in self.commands.items()}

    def register_command(self, name: str, command: Command):
        """Registra un nuovo comando personalizzato"""
        self.commands[name] = command

    def parse_and_execute_user_input(self, user_input: str, total_entries: int) -> bool:
        """
        Parsa l'input dell'utente ed esegue il comando appropriato

        Args:
            user_input: Input dell'utente
            total_entries: Numero totale di entry disponibili

        Returns:
            bool: True per continuare, False per uscire
        """
        user_input = user_input.strip().lower()

        if not user_input:
            return True

        # Gestisci numeri (apertura link specifico)
        if user_input.isdigit():
            index = int(user_input)
            if 1 <= index <= total_entries:
                return self.execute_command("open_link", index)  # type: ignore
            else:
                self.cli_display.print_error_message(
                    f"Numero non valido. Inserisci un numero tra 1 e {total_entries}"
                )
                return True

        # Gestisci comandi singoli
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

        # Gestisci comandi con argomenti
        parts = user_input.split()
        if len(parts) > 1:
            cmd = parts[0]
            args = parts[1:]

            if cmd == "search" or cmd == "find":
                search_term = " ".join(args)
                return self.execute_command("search", search_term)
            elif cmd == "export":
                format_type = args[0] if args else "text"
                output_file = args[1] if len(args) > 1 else None
                return self.execute_command("export", format_type, output_file)
            elif cmd == "config" or cmd == "c":
                action = args[0] if args else "show"
                return self.execute_command("config", action)

        # Gestisci comandi singoli
        command = command_map.get(user_input)
        if command:
            return self.execute_command(command)

        # Comando non riconosciuto
        self.cli_display.print_error_message(
            f"Comando non riconosciuto: '{user_input}'"
        )
        self.cli_display.print_info_message("Digita 'h' per vedere l'aiuto")
        return True
