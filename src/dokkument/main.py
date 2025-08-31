"""
Main - Entry point principale dell'applicazione dokkument
Gestisce argparse e orchestrazione dei componenti principali
"""

import argparse
import sys
from pathlib import Path

from .parser import DokkParserFactory
from .link_manager import LinkManager
from .browser_opener import BrowserOpener
from .cli_display import CLIDisplay
from .commands import CommandInvoker
from .config_manager import get_config


class DokkumentApp:
    """Classe principale dell'applicazione dokkument"""

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
        Esegue l'applicazione in modalit� interattiva

        Args:
            scan_path: Directory da scansionare (default: directory corrente)
        """
        if scan_path is None:
            scan_path = Path.cwd()

        # Header dell'applicazione
        self.cli_display.print_header("dokkument - Gestore Documentazione Aziendale")
        self.cli_display.print_scanning_message(scan_path)

        # Scansiona per file .dokk
        try:
            recursive = self.config.get("scanning.recursive", True)
            total_links = self.link_manager.scan_for_links(scan_path, recursive)

            # Mostra risultati scansione
            stats = self.link_manager.get_statistics()
            self.cli_display.print_scan_results(total_links, stats["total_files"])

            if total_links == 0:
                return

            # Loop principale interattivo
            while True:
                entries = self.link_manager.get_all_entries()
                show_files = self.config.get("display.show_file_names", True)

                self.cli_display.print_menu(entries, show_files)
                self.cli_display.print_menu_footer(len(entries))

                user_input = self.cli_display.get_user_input()

                # Esegui comando
                should_continue = self.command_invoker.parse_and_execute_user_input(
                    user_input, len(entries)
                )

                if not should_continue:
                    break

                print()  # Riga vuota tra le iterazioni

        except KeyboardInterrupt:
            self.cli_display.print_farewell()
        except Exception as e:
            self.cli_display.print_error_message(f"Errore critico: {e}")
            if self.config.get("advanced.debug_mode", False):
                import traceback

                traceback.print_exc()
            sys.exit(1)

    def run_list_mode(self, scan_path: Path = None, format_type: str = "text"):
        """
        Esegue l'applicazione in modalit� lista (non interattiva)

        Args:
            scan_path: Directory da scansionare
            format_type: Formato di output
        """
        if scan_path is None:
            scan_path = Path.cwd()

        try:
            recursive = self.config.get("scanning.recursive", True)
            total_links = self.link_manager.scan_for_links(scan_path, recursive)

            if total_links == 0:
                print("Nessun file .dokk trovato")
                return

            # Output in base al formato richiesto
            if format_type in ["json", "markdown", "html"]:
                content = self.link_manager.export_to_format(format_type)
                print(content)
            else:
                # Output testuale semplice
                entries = self.link_manager.get_all_entries()
                for i, entry in enumerate(entries, 1):
                    print(f"{i:2d}. {entry.description}")
                    print(f"    {entry.url}")
                    print(f"    =� {entry.file_path}")
                    print()

        except Exception as e:
            print(f"Errore: {e}", file=sys.stderr)
            sys.exit(1)

    def run_open_mode(
        self, scan_path: Path = None, link_indices: list = None, open_all: bool = False
    ):
        """
        Esegue l'applicazione in modalit� apertura diretta

        Args:
            scan_path: Directory da scansionare
            link_indices: Lista di indici di link da aprire
            open_all: Se True, apre tutti i link
        """
        if scan_path is None:
            scan_path = Path.cwd()

        try:
            recursive = self.config.get("scanning.recursive", True)
            total_links = self.link_manager.scan_for_links(scan_path, recursive)

            if total_links == 0:
                print("Nessun file .dokk trovato")
                return

            entries = self.link_manager.get_all_entries()

            if open_all:
                # Apri tutti i link
                urls = [entry.url for entry in entries]
                preferred_browser = self.config.get("browser.preferred_browser")
                delay = self.config.get("browser.open_delay_seconds", 0.5)

                print(f"Apertura di {len(urls)} link...")
                results = self.browser_opener.open_multiple_urls(
                    urls, preferred_browser, delay
                )
                success_count = sum(1 for result in results if result)
                print(f"Aperti {success_count} link su {len(urls)}")

            elif link_indices:
                # Apri link specifici
                preferred_browser = self.config.get("browser.preferred_browser")

                for index in link_indices:
                    if 1 <= index <= len(entries):
                        entry = entries[index - 1]
                        print(f"Apertura: {entry.description}")
                        success = self.browser_opener.open_url(
                            entry.url, preferred_browser
                        )
                        if not success:
                            print(f"Errore nell'apertura di: {entry.description}")
                    else:
                        print(f"Indice non valido: {index}")

        except Exception as e:
            print(f"Errore: {e}", file=sys.stderr)
            sys.exit(1)


def create_argument_parser() -> argparse.ArgumentParser:
    """Crea e configura il parser per gli argomenti della riga di comando"""

    parser = argparse.ArgumentParser(
        prog="dokkument",
        description="Gestore CLI per documentazione aziendale tramite file .dokk",
        epilog="""
Esempi di uso:
  dokkument                        # Modalità interattiva
  dokkument --list                 # Lista tutti i link
  dokkument --list --format json  # Lista in formato JSON
  dokkument --open-all             # Apre tutti i link
  dokkument --open 1 3 5           # Apre i link 1, 3 e 5
  dokkument --path /docs           # Scansiona directory specifica
  dokkument --config show          # Mostra configurazione
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Argomenti generali
    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=None,
        help="Directory da scansionare per file .dokk (default: directory corrente)",
    )

    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Scansiona ricorsivamente le sottodirectory",
    )

    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Non scansionare ricorsivamente (sovrascrive configurazione)",
    )

    # Modalit� operative (mutuamente esclusive)
    mode_group = parser.add_mutually_exclusive_group()

    mode_group.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="Mostra solo la lista dei link senza modalit� interattiva",
    )

    mode_group.add_argument(
        "--open-all", "-a", action="store_true", help="Apre tutti i link trovati e esce"
    )

    mode_group.add_argument(
        "--open",
        "-o",
        nargs="+",
        type=int,
        metavar="INDEX",
        help="Apre i link con gli indici specificati (es. --open 1 3 5)",
    )

    # Opzioni per la modalit� lista
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown", "html"],
        default="text",
        help="Formato di output per la modalit� lista (default: text)",
    )

    # Opzioni di configurazione
    parser.add_argument(
        "--config",
        "-c",
        choices=["show", "export", "validate"],
        help="Operazioni sulla configurazione",
    )

    parser.add_argument(
        "--browser",
        "-b",
        type=str,
        help="Browser specifico da usare (sovrascrive configurazione)",
    )

    # Opzioni di output
    parser.add_argument(
        "--no-color", action="store_true", help="Disabilita i colori nell'output"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Abilita la modalit� debug con informazioni aggiuntive",
    )

    parser.add_argument("--version", "-v", action="version", version="dokkument 1.0.0")

    # Opzioni per testing e sviluppo
    parser.add_argument(
        "--validate", action="store_true", help="Valida tutti i link trovati"
    )

    parser.add_argument(
        "--stats", action="store_true", help="Mostra solo le statistiche"
    )

    return parser


def main():
    """Funzione main principale"""

    # Crea parser argomenti
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()

    # Crea applicazione
    app = DokkumentApp()

    # Applica override di configurazione da argomenti
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

    # Gestione comandi di configurazione
    if args.config:
        app.command_invoker.execute_command("config", args.config)
        return

    # Gestione modalit� specifiche
    if args.validate:
        # Scansiona prima
        scan_path = args.path or Path.cwd()
        recursive = app.config.get("scanning.recursive", True)
        app.link_manager.scan_for_links(scan_path, recursive)

        # Poi valida
        app.command_invoker.execute_command("validate")
        return

    if args.stats:
        # Scansiona prima
        scan_path = args.path or Path.cwd()
        recursive = app.config.get("scanning.recursive", True)
        app.link_manager.scan_for_links(scan_path, recursive)

        # Poi mostra statistiche
        app.command_invoker.execute_command("statistics")
        return

    # Modalit� principali
    if args.list:
        app.run_list_mode(args.path, args.format)
    elif args.open_all:
        app.run_open_mode(args.path, open_all=True)
    elif args.open:
        app.run_open_mode(args.path, link_indices=args.open)
    else:
        # Modalit� interattiva (default)
        app.run_interactive_mode(args.path)


if __name__ == "__main__":
    main()
