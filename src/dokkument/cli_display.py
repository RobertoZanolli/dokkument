"""
CLIDisplay - Gestisce la visualizzazione del menu interattivo
Fornisce un'interfaccia user-friendly con colori e formattazione
"""

import sys
import os
from typing import List, Dict
from pathlib import Path

from .parser import DokkEntry
from .link_manager import LinkManager


class CLIDisplay:
    """Gestisce la visualizzazione dell'interfaccia a riga di comando"""

    def __init__(self, link_manager: LinkManager):
        self.link_manager = link_manager
        self.supports_color = self._check_color_support()
        self.supports_hyperlinks = self._check_hyperlink_support()

        # Codici colore ANSI
        self.COLORS = {
            "header": "\033[1;36m",  # Ciano grassetto
            "success": "\033[1;32m",  # Verde grassetto
            "warning": "\033[1;33m",  # Giallo grassetto
            "error": "\033[1;31m",  # Rosso grassetto
            "info": "\033[1;34m",  # Blu grassetto
            "prompt": "\033[1;35m",  # Magenta grassetto
            "reset": "\033[0m",  # Reset
            "dim": "\033[2m",  # Testo sfumato
            "bold": "\033[1m",  # Grassetto
        }

        # Se il terminale non supporta i colori, usa stringhe vuote
        if not self.supports_color:
            self.colors = {key: "" for key in self.COLORS}
        else:
            self.colors = self.COLORS

    def _check_color_support(self) -> bool:
        """Verifica se il terminale supporta i colori ANSI"""
        # Controlla variabili d'ambiente comuni
        term = os.environ.get("TERM", "")
        colorterm = os.environ.get("COLORTERM", "")

        # Su Windows, controlla se stiamo usando un terminale moderno
        if sys.platform == "win32":
            # Windows Terminal, VS Code terminal, ecc. supportano i colori
            if any(env in os.environ for env in ["WT_SESSION", "VSCODE_PID"]):
                return True
            # Prova ad abilitare il supporto colore su Windows 10+
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except:
                pass

        # Su Unix-like, controlla TERM
        color_terms = ["xterm", "xterm-256color", "screen", "tmux", "linux"]
        return any(color_term in term for color_term in color_terms) or bool(colorterm)

    def _check_hyperlink_support(self) -> bool:
        """Verifica se il terminale supporta i link ipertestuali OSC 8"""
        # Lista di terminali che supportano OSC 8
        term = os.environ.get("TERM", "").lower()
        term_program = os.environ.get("TERM_PROGRAM", "").lower()

        hyperlink_terminals = ["iterm", "vte", "gnome-terminal", "konsole", "alacritty"]

        return (
            any(ht in term for ht in hyperlink_terminals)
            or any(ht in term_program for ht in hyperlink_terminals)
            or "VSCODE_PID" in os.environ
            or "WT_SESSION" in os.environ
        )

    def colorize(self, text: str, color_key: str) -> str:
        """Applica colore al testo se supportato"""
        color = self.colors.get(color_key, "")
        reset = self.colors.get("reset", "")
        return f"{color}{text}{reset}" if color else text

    def print_header(self, title: str):
        """Stampa un'intestazione formattata"""
        print()
        print(self.colorize("=" * 60, "header"))
        print(self.colorize(f"  {title.center(56)}", "header"))
        print(self.colorize("=" * 60, "header"))
        print()

    def print_scanning_message(self, path: Path):
        """Stampa messaggio durante la scansione"""
        print(self.colorize(f"🔍 Scansionando directory: {path}", "info"))
        print()

    def print_scan_results(self, total_links: int, total_files: int):
        """Stampa i risultati della scansione"""
        if total_links == 0:
            print(
                self.colorize(
                    "⚠️ Nessun file .dokk trovato nella directory corrente", "warning"
                )
            )
            print(
                self.colorize(
                    "ℹ️ Assicurati che ci siano file .dokk nel formato:", "info"
                )
            )
            print(
                self.colorize(
                    '   "Descrizione del link" -> "https://esempio.com"', "dim"
                )
            )
            return

        print(
            self.colorize(
                f"✅ Trovati {total_links} link in {total_files} file", "success"
            )
        )
        print()

    def print_menu(self, entries: List[DokkEntry], show_files: bool = True):
        """
        Stampa il menu principale con le opzioni

        Args:
            entries: Lista delle entry da mostrare
            show_files: Se True, mostra anche i nomi dei file
        """
        if not entries:
            print(self.colorize("Nessun link disponibile", "warning"))
            return

        print(self.colorize("📋 Link disponibili:", "header"))
        print()

        # Raggruppa per file se richiesto
        if show_files:
            entries_by_file = {}
            for entry in entries:
                if entry.file_path not in entries_by_file:
                    entries_by_file[entry.file_path] = []
                entries_by_file[entry.file_path].append(entry)

            index = 1
            for file_path, file_entries in entries_by_file.items():
                # Nome del file con colore
                file_color = self.link_manager.get_file_color(file_path)
                print(self.colorize(f"📁 {file_path.name}", "dim"))

                for entry in file_entries:
                    description = self.link_manager.get_colored_description(entry)
                    url = self.link_manager.get_colored_url(
                        entry, self.supports_hyperlinks
                    )

                    print(f"{self.colorize(f'[{index:2d}]', 'prompt')} {description}")
                    if not self.supports_hyperlinks:
                        print(f"     {url}")

                    index += 1
                print()
        else:
            # Menu semplice senza raggruppamento
            for i, entry in enumerate(entries, 1):
                description = self.link_manager.get_colored_description(entry)
                url = self.link_manager.get_colored_url(entry, self.supports_hyperlinks)

                print(f"{self.colorize(f'[{i:2d}]', 'prompt')} {description}")
                if not self.supports_hyperlinks:
                    print(f"     {url}")

        print()

    def print_menu_footer(self, total_entries: int):
        """Stampa il footer del menu con le opzioni"""
        print(self.colorize(" " * 60, "dim"))
        print(self.colorize("Opzioni disponibili:", "info"))
        print(
            f"  {self.colorize('1-' + str(total_entries), 'prompt')}: Apri il link corrispondente"
        )
        print(f"  {self.colorize('a', 'prompt')}: Apri tutti i link")
        print(f"  {self.colorize('l', 'prompt')}: Mostra solo la lista (senza aprire)")
        print(f"  {self.colorize('r', 'prompt')}: Ricarica/Riscansiona")
        print(f"  {self.colorize('s', 'prompt')}: Statistiche")
        print(f"  {self.colorize('h', 'prompt')}: Aiuto")
        print(f"  {self.colorize('q', 'prompt')}: Esci")
        print()

    def get_user_input(self, prompt: str = "Seleziona un'opzione") -> str:
        """Ottiene input dall'utente con prompt colorato"""
        colored_prompt = self.colorize(f"{prompt}: ", "prompt")
        try:
            return input(colored_prompt).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return "q"  # Esce in caso di Ctrl+C o Ctrl+D

    def print_opening_message(self, entry: DokkEntry):
        """Stampa messaggio quando si apre un link"""
        print(self.colorize(f"🚀 Apertura di: {entry.description}", "info"))
        print(self.colorize(f"🔗 URL: {entry.url}", "dim"))

    def print_opening_all_message(self, count: int):
        """Stampa messaggio quando si aprono tutti i link"""
        print(self.colorize(f"🚀 Apertura di tutti i {count} link...", "warning"))
        print(
            self.colorize(
                "⚠️  Questo potrebbe aprire molte schede del browser!", "warning"
            )
        )

    def print_success_message(self, message: str):
        """Stampa un messaggio di successo"""
        print(self.colorize(f"✅ {message}", "success"))

    def print_error_message(self, message: str):
        """Stampa un messaggio di errore"""
        print(self.colorize(f"❌ {message}", "error"))

    def print_warning_message(self, message: str):
        """Stampa un messaggio di avviso"""
        print(self.colorize(f"⚠️  {message}", "warning"))

    def print_info_message(self, message: str):
        """Stampa un messaggio informativo"""
        print(self.colorize(f"ℹ️  {message}", "info"))

    def print_statistics(self, stats: Dict[str, int]):
        """Stampa le statistiche dei link"""
        print()
        print(self.colorize("📊 Statistiche", "header"))
        print(self.colorize("-" * 30, "dim"))
        print(
            f"📁 File .dokk trovati: {self.colorize(str(stats['total_files']), 'info')}"
        )
        print(f"🔗 Link totali: {self.colorize(str(stats['total_links']), 'info')}")
        print(f"🌐 Domini unici: {self.colorize(str(stats['unique_domains']), 'info')}")

        if stats["total_files"] > 0:
            avg_links = stats["total_links"] / stats["total_files"]
            print(
                f"📈 Media link per file: {self.colorize(f'{avg_links:.1f}', 'info')}"
            )
        print()

    def print_help(self):
        """Stampa l'aiuto per l'utente"""
        print()
        print(self.colorize("❓ Aiuto - dokkument", "header"))
        print()
        print(self.colorize("Formato file .dokk:", "info"))
        print('  "Descrizione del link" -> "https://esempio.com"')
        print('  "Documentazione API" -> "https://api.example.com/docs"')
        print()
        print(self.colorize("Comandi disponibili:", "info"))
        print("  • Numero (1-N): Apre il link corrispondente")
        print("  • a: Apre tutti i link contemporaneamente")
        print("  • l: Mostra solo la lista senza aprire nulla")
        print("  • r: Ricarica e riscansiona i file .dokk")
        print("  • s: Mostra statistiche sui link trovati")
        print("  • h: Mostra questo aiuto")
        print("  • q: Esce dall'applicazione")
        print()
        print(self.colorize("Note:", "warning"))
        print("  • I link dello stesso file hanno lo stesso colore")
        print("  • Su terminali compatibili i link sono cliccabili")
        print("  • L'applicazione cerca file .dokk ricorsivamente")
        print()

    def confirm_action(self, message: str, default: bool = True) -> bool:
        """
        Chiede conferma all'utente

        Args:
            message: Messaggio da mostrare
            default: Valore predefinito se l'utente preme solo Invio

        Returns:
            bool: True se l'utente conferma
        """
        default_text = "S/n" if default else "s/N"
        response = (
            input(self.colorize(f"{message} ({default_text}): ", "prompt"))
            .strip()
            .lower()
        )

        if response == "":
            return default
        elif response in ["s", "si", "y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            return default

    def clear_screen(self):
        """Pulisce lo schermo se possibile"""
        try:
            if sys.platform == "win32":
                os.system("cls")
            else:
                os.system("clear")
        except:
            # Se non riesce a pulire, stampa alcune righe vuote
            print("\n" * 3)

    def print_farewell(self):
        """Stampa messaggio di addio"""
        print()
        print(
            self.colorize("👋 Arrivederci! Grazie per aver usato dokkument", "success")
        )
        print()
