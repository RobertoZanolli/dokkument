"""
dokkument - Gestore CLI per documentazione aziendale tramite file .dokk

Questo pacchetto fornisce strumenti per gestire e accedere rapidamente
alla documentazione aziendale utilizzando file .dokk che contengono
collegamenti organizzati.

Componenti principali:
- DokkFileParser: Parser per file .dokk
- LinkManager: Gestione dei link e delle collezioni
- BrowserOpener: Apertura URL nel browser
- CLIDisplay: Interfaccia utente a riga di comando
- ConfigManager: Gestione configurazione
- Commands: Sistema di comandi con pattern Command
"""

__version__ = "1.0.0"
__author__ = "Dokkument Team"
__description__ = "Gestore CLI per documentazione aziendale tramite file .dokk"

# Import principali per facilitare l'uso del modulo
from .parser import DokkEntry, DokkParserFactory, DokkFileScanner, ParseError

from .link_manager import LinkManager
from .browser_opener import BrowserOpener
from .cli_display import CLIDisplay
from .config_manager import ConfigManager, get_config
from .commands import CommandInvoker
from .main import DokkumentApp, main

# Export dei simboli pubblici
__all__ = [
    # Classi principali
    "DokkumentApp",
    "LinkManager",
    "BrowserOpener",
    "CLIDisplay",
    "ConfigManager",
    "CommandInvoker",
    # Parser
    "DokkEntry",
    "DokkParserFactory",
    "DokkFileScanner",
    "ParseError",
    # Funzioni utility
    "get_config",
    "main",
    # Metadati
    "__version__",
    "__author__",
    "__description__",
]
