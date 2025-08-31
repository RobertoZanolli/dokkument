"""
LinkManager - Gestisce la collezione di link e descrizioni
Centralizza la logica per gestire i link trovati nei file .dokk
"""

from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
import hashlib

from .parser import DokkEntry, DokkFileScanner, DokkParserFactory


class LinkManager:
    """Gestisce la collezione di link e le operazioni su di essi"""
    
    def __init__(self, parser_factory: DokkParserFactory = None):
        self.scanner = DokkFileScanner(parser_factory)
        self._entries: List[DokkEntry] = []
        self._entries_by_file: Dict[Path, List[DokkEntry]] = {}
        self._last_scan_path: Optional[Path] = None
        self._file_colors: Dict[Path, str] = {}
        
        # Colori ANSI per terminale
        self.COLORS = [
            '\033[91m',  # Rosso
            '\033[92m',  # Verde  
            '\033[93m',  # Giallo
            '\033[94m',  # Blu
            '\033[95m',  # Magenta
            '\033[96m',  # Ciano
            '\033[97m',  # Bianco
        ]
        self.RESET_COLOR = '\033[0m'
    
    def scan_for_links(self, root_path: Path = None, recursive: bool = True) -> int:
        """
        Scansiona per file .dokk e carica i link
        
        Args:
            root_path: Directory da scansionare (default: directory corrente)
            recursive: Se True, scansiona sottodirectory
            
        Returns:
            int: Numero totale di link trovati
        """
        if root_path is None:
            root_path = Path.cwd()
        
        self._last_scan_path = root_path
        self._entries.clear()
        self._entries_by_file.clear()
        self._file_colors.clear()
        
        try:
            file_entries = self.scanner.scan_directory(root_path, recursive)
            
            # Assegna colori ai file
            color_index = 0
            for file_path in file_entries.keys():
                self._file_colors[file_path] = self.COLORS[color_index % len(self.COLORS)]
                color_index += 1
            
            # Aggiungi tutte le entry
            for file_path, entries in file_entries.items():
                self._entries_by_file[file_path] = entries
                self._entries.extend(entries)
            
            return len(self._entries)
            
        except Exception as e:
            raise RuntimeError(f"Errore durante la scansione: {e}")
    
    def get_all_entries(self) -> List[DokkEntry]:
        """Restituisce tutte le entry caricate"""
        return self._entries.copy()
    
    def get_entries_by_file(self) -> Dict[Path, List[DokkEntry]]:
        """Restituisce le entry raggruppate per file"""
        return self._entries_by_file.copy()
    
    def get_entry_by_index(self, index: int) -> Optional[DokkEntry]:
        """
        Restituisce una entry per indice (1-based per l'utente)
        
        Args:
            index: Indice 1-based della entry
            
        Returns:
            DokkEntry o None se l'indice non è valido
        """
        if 1 <= index <= len(self._entries):
            return self._entries[index - 1]
        return None
    
    def get_file_color(self, file_path: Path) -> str:
        """Restituisce il colore ANSI associato a un file"""
        return self._file_colors.get(file_path, '')
    
    def get_colored_description(self, entry: DokkEntry) -> str:
        """
        Restituisce la descrizione colorata per il terminale
        
        Args:
            entry: Entry di cui colorare la descrizione
            
        Returns:
            str: Descrizione con codici colore ANSI
        """
        color = self.get_file_color(entry.file_path)
        return f"{color}{entry.description}{self.RESET_COLOR}"
    
    def get_colored_url(self, entry: DokkEntry, make_clickable: bool = True) -> str:
        """
        Restituisce l'URL colorato e opzionalmente cliccabile
        
        Args:
            entry: Entry di cui colorare l'URL
            make_clickable: Se True, rende l'URL cliccabile se supportato dal terminale
            
        Returns:
            str: URL con codici colore e possibilmente cliccabile
        """
        color = self.get_file_color(entry.file_path)
        
        if make_clickable:
            # Formato OSC 8 per link ipertestuali nei terminali compatibili
            clickable_url = f"\033]8;;{entry.url}\033\\{entry.url}\033]8;;\033\\"
            return f"{color}{clickable_url}{self.RESET_COLOR}"
        else:
            return f"{color}{entry.url}{self.RESET_COLOR}"
    
    def filter_entries(self, search_term: str) -> List[DokkEntry]:
        """
        Filtra le entry in base a un termine di ricerca
        
        Args:
            search_term: Termine da cercare nelle descrizioni
            
        Returns:
            List[DokkEntry]: Entry che contengono il termine di ricerca
        """
        search_lower = search_term.lower()
        return [
            entry for entry in self._entries
            if search_lower in entry.description.lower()
        ]
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Restituisce statistiche sui link caricati
        
        Returns:
            Dict con statistiche (total_links, total_files, unique_domains)
        """
        if not self._entries:
            return {
                'total_links': 0,
                'total_files': 0,
                'unique_domains': 0
            }
        
        # Estrai domini unici
        domains = set()
        for entry in self._entries:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(entry.url)
                if parsed.netloc:
                    domains.add(parsed.netloc.lower())
            except:
                continue
        
        return {
            'total_links': len(self._entries),
            'total_files': len(self._entries_by_file),
            'unique_domains': len(domains)
        }
    
    def validate_all_links(self) -> List[Tuple[DokkEntry, str]]:
        """
        Valida tutti i link (controllo di base del formato)
        
        Returns:
            List[Tuple[DokkEntry, str]]: Lista di (entry, messaggio_errore) per link non validi
        """
        invalid_links = []
        
        for entry in self._entries:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(entry.url)
                
                if not parsed.scheme or parsed.scheme not in ['http', 'https']:
                    invalid_links.append((entry, "Schema URL non valido"))
                elif not parsed.netloc:
                    invalid_links.append((entry, "Dominio mancante nell'URL"))
                    
            except Exception as e:
                invalid_links.append((entry, f"Errore nel parsing dell'URL: {e}"))
        
        return invalid_links
    
    def export_to_format(self, format_type: str = 'text') -> str:
        """
        Esporta i link in vari formati
        
        Args:
            format_type: Formato di esportazione ('text', 'markdown', 'html', 'json')
            
        Returns:
            str: Contenuto esportato nel formato richiesto
        """
        if format_type == 'text':
            return self._export_to_text()
        elif format_type == 'markdown':
            return self._export_to_markdown()
        elif format_type == 'html':
            return self._export_to_html()
        elif format_type == 'json':
            return self._export_to_json()
        else:
            raise ValueError(f"Formato non supportato: {format_type}")
    
    def _export_to_text(self) -> str:
        """Esporta in formato testo semplice"""
        lines = ["Documentazione Links\n", "=" * 50, ""]
        
        for file_path, entries in self._entries_by_file.items():
            lines.append(f"File: {file_path}")
            lines.append("-" * 40)
            for i, entry in enumerate(entries, 1):
                lines.append(f"{i:2d}. {entry.description}")
                lines.append(f"    {entry.url}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _export_to_markdown(self) -> str:
        """Esporta in formato Markdown"""
        lines = ["# Documentazione Links", ""]
        
        for file_path, entries in self._entries_by_file.items():
            lines.append(f"## {file_path.name}")
            lines.append("")
            for entry in entries:
                lines.append(f"- [{entry.description}]({entry.url})")
            lines.append("")
        
        return "\n".join(lines)
    
    def _export_to_html(self) -> str:
        """Esporta in formato HTML"""
        html = ["<!DOCTYPE html>", "<html>", "<head>", 
                "<title>Documentazione Links</title>", "</head>", "<body>",
                "<h1>Documentazione Links</h1>"]
        
        for file_path, entries in self._entries_by_file.items():
            html.append(f"<h2>{file_path.name}</h2>")
            html.append("<ul>")
            for entry in entries:
                html.append(f'<li><a href="{entry.url}">{entry.description}</a></li>')
            html.append("</ul>")
        
        html.extend(["</body>", "</html>"])
        return "\n".join(html)
    
    def _export_to_json(self) -> str:
        """Esporta in formato JSON"""
        import json
        
        data = {
            "scan_info": {
                "scan_path": str(self._last_scan_path) if self._last_scan_path else None,
                "total_entries": len(self._entries),
                "total_files": len(self._entries_by_file)
            },
            "files": []
        }
        
        for file_path, entries in self._entries_by_file.items():
            file_data = {
                "file_path": str(file_path),
                "entries": [
                    {
                        "description": entry.description,
                        "url": entry.url
                    }
                    for entry in entries
                ]
            }
            data["files"].append(file_data)
        
        return json.dumps(data, indent=2, ensure_ascii=False)