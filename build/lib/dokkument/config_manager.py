"""
ConfigManager - Gestisce configurazioni e preferenze dell'applicazione
Implementa il pattern Singleton per la configurazione globale
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
import threading


class ConfigManager:
    """Singleton per la gestione della configurazione dell'applicazione"""
    
    _instance: Optional['ConfigManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Evita la reinizializzazione se l'istanza esiste già
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._config: Dict[str, Any] = {}
        self._config_file: Optional[Path] = None
        self._load_default_config()
        self._find_and_load_config_file()
    
    def _load_default_config(self):
        """Carica la configurazione predefinita"""
        self._config = {
            # Impostazioni di scansione
            'scanning': {
                'recursive': True,
                'max_depth': 10,
                'excluded_dirs': ['.git', '__pycache__', 'node_modules', '.venv', 'venv'],
                'file_patterns': ['*.dokk']
            },
            
            # Impostazioni di visualizzazione
            'display': {
                'enable_colors': True,
                'enable_hyperlinks': True,
                'group_by_file': True,
                'max_description_length': 80,
                'show_file_names': True,
                'confirm_open_all': True
            },
            
            # Impostazioni browser
            'browser': {
                'preferred_browser': None,  # None = browser predefinito del sistema
                'open_delay_seconds': 0.5,
                'max_concurrent_opens': 10
            },
            
            # Impostazioni di sicurezza
            'security': {
                'validate_urls': True,
                'allowed_schemes': ['http', 'https'],
                'warn_on_suspicious_urls': True
            },
            
            # Impostazioni avanzate
            'advanced': {
                'cache_scan_results': False,
                'auto_reload_on_change': False,
                'debug_mode': False,
                'log_level': 'INFO'
            }
        }
    
    def _find_and_load_config_file(self):
        """Trova e carica il file di configurazione dall'utente"""
        possible_locations = [
            # Directory corrente
            Path.cwd() / '.dokkument.json',
            Path.cwd() / 'dokkument.json',
            
            # Directory home dell'utente
            Path.home() / '.dokkument.json',
            Path.home() / '.config' / 'dokkument' / 'config.json',
            
            # Directory di configurazione specifiche del sistema
        ]
        
        # Su Windows, aggiungi AppData
        if os.name == 'nt':
            appdata = os.environ.get('APPDATA')
            if appdata:
                possible_locations.append(Path(appdata) / 'dokkument' / 'config.json')
        
        # Su Unix-like, aggiungi XDG_CONFIG_HOME
        else:
            xdg_config = os.environ.get('XDG_CONFIG_HOME')
            if xdg_config:
                possible_locations.append(Path(xdg_config) / 'dokkument' / 'config.json')
        
        for config_path in possible_locations:
            if config_path.exists() and config_path.is_file():
                try:
                    self._load_config_from_file(config_path)
                    self._config_file = config_path
                    break
                except Exception as e:
                    print(f"Attenzione: Errore nel caricamento della configurazione da {config_path}: {e}")
                    continue
    
    def _load_config_from_file(self, config_path: Path):
        """Carica la configurazione da un file JSON"""
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        
        # Merge ricorsivo della configurazione utente con quella predefinita
        self._merge_config(self._config, user_config)
    
    def _merge_config(self, default: Dict, user: Dict):
        """Merge ricorsivo di due dizionari di configurazione"""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Ottiene un valore di configurazione usando la notazione a punti
        
        Args:
            key_path: Percorso della chiave (es. 'display.enable_colors')
            default: Valore predefinito se la chiave non esiste
            
        Returns:
            Il valore della configurazione o il default
        """
        keys = key_path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Imposta un valore di configurazione usando la notazione a punti
        
        Args:
            key_path: Percorso della chiave (es. 'display.enable_colors')
            value: Valore da impostare
        """
        keys = key_path.split('.')
        current = self._config
        
        # Naviga fino al penultimo livello
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Imposta il valore finale
        current[keys[-1]] = value
    
    def save_config(self, config_path: Path = None) -> bool:
        """
        Salva la configurazione corrente su file
        
        Args:
            config_path: Percorso del file (opzionale, usa quello corrente se non specificato)
            
        Returns:
            bool: True se il salvataggio ha avuto successo
        """
        if config_path is None:
            if self._config_file is None:
                # Se non c'è un file di configurazione esistente, crea uno nella home
                config_path = Path.home() / '.dokkument.json'
            else:
                config_path = self._config_file
        
        try:
            # Crea la directory se non esiste
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            self._config_file = config_path
            return True
            
        except Exception as e:
            print(f"Errore nel salvataggio della configurazione: {e}")
            return False
    
    def reset_to_defaults(self):
        """Ripristina la configurazione ai valori predefiniti"""
        self._load_default_config()
    
    def get_config_file_path(self) -> Optional[Path]:
        """Restituisce il percorso del file di configurazione corrente"""
        return self._config_file
    
    def get_all_config(self) -> Dict[str, Any]:
        """Restituisce una copia di tutta la configurazione"""
        import copy
        return copy.deepcopy(self._config)
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Aggiorna la configurazione con un nuovo dizionario
        
        Args:
            new_config: Nuovo dizionario di configurazione
        """
        self._merge_config(self._config, new_config)
    
    def validate_config(self) -> List[str]:
        """
        Valida la configurazione corrente
        
        Returns:
            List[str]: Lista di errori di validazione (vuota se tutto OK)
        """
        errors = []
        
        try:
            # Valida le impostazioni di scansione
            if not isinstance(self.get('scanning.recursive'), bool):
                errors.append("scanning.recursive deve essere un booleano")
            
            if not isinstance(self.get('scanning.max_depth'), int) or self.get('scanning.max_depth') < 1:
                errors.append("scanning.max_depth deve essere un intero positivo")
            
            # Valida le impostazioni di visualizzazione
            if not isinstance(self.get('display.enable_colors'), bool):
                errors.append("display.enable_colors deve essere un booleano")
            
            # Valida le impostazioni browser
            browser = self.get('browser.preferred_browser')
            if browser is not None and not isinstance(browser, str):
                errors.append("browser.preferred_browser deve essere None o una stringa")
            
            # Valida gli schemi URL permessi
            allowed_schemes = self.get('security.allowed_schemes', [])
            if not isinstance(allowed_schemes, list):
                errors.append("security.allowed_schemes deve essere una lista")
            elif not all(isinstance(scheme, str) for scheme in allowed_schemes):
                errors.append("Tutti gli elementi in security.allowed_schemes devono essere stringhe")
        
        except Exception as e:
            errors.append(f"Errore generale nella validazione: {e}")
        
        return errors
    
    def print_config_info(self):
        """Stampa informazioni sulla configurazione corrente"""
        print("=Ë Informazioni Configurazione dokkument")
        print("=" * 50)
        
        if self._config_file:
            print(f"=Á File configurazione: {self._config_file}")
        else:
            print("=Á File configurazione: Nessuno (usando configurazione predefinita)")
        
        print(f"= Scansione ricorsiva: {self.get('scanning.recursive')}")
        print(f"<¨ Colori abilitati: {self.get('display.enable_colors')}")
        print(f"= Link cliccabili: {self.get('display.enable_hyperlinks')}")
        print(f"< Browser preferito: {self.get('browser.preferred_browser') or 'Predefinito del sistema'}")
        print(f"= Validazione URL: {self.get('security.validate_urls')}")
        print(f"= Modalità debug: {self.get('advanced.debug_mode')}")
        
        # Validazione
        errors = self.validate_config()
        if errors:
            print("\n   Errori di configurazione:")
            for error in errors:
                print(f"   " {error}")
        else:
            print("\n Configurazione valida")
    
    def export_config_template(self, output_path: Path = None) -> bool:
        """
        Esporta un template di configurazione commentato
        
        Args:
            output_path: Percorso del file di output (default: dokkument-config-template.json)
            
        Returns:
            bool: True se l'esportazione ha avuto successo
        """
        if output_path is None:
            output_path = Path.cwd() / 'dokkument-config-template.json'
        
        template = {
            "_comment": "Template di configurazione per dokkument - Rimuovi questo commento per usarlo",
            "_instructions": "Copia questo file come .dokkument.json nella tua directory home o nel progetto",
            
            "scanning": {
                "_comment": "Impostazioni per la scansione dei file .dokk",
                "recursive": True,
                "max_depth": 10,
                "excluded_dirs": [".git", "__pycache__", "node_modules", ".venv", "venv"],
                "file_patterns": ["*.dokk"]
            },
            
            "display": {
                "_comment": "Impostazioni di visualizzazione dell'interfaccia",
                "enable_colors": True,
                "enable_hyperlinks": True,
                "group_by_file": True,
                "max_description_length": 80,
                "show_file_names": True,
                "confirm_open_all": True
            },
            
            "browser": {
                "_comment": "Impostazioni browser - preferred_browser: null, 'firefox', 'chrome', ecc.",
                "preferred_browser": None,
                "open_delay_seconds": 0.5,
                "max_concurrent_opens": 10
            },
            
            "security": {
                "_comment": "Impostazioni di sicurezza per la validazione URL",
                "validate_urls": True,
                "allowed_schemes": ["http", "https"],
                "warn_on_suspicious_urls": True
            },
            
            "advanced": {
                "_comment": "Impostazioni avanzate - modificare solo se si sa cosa si fa",
                "cache_scan_results": False,
                "auto_reload_on_change": False,
                "debug_mode": False,
                "log_level": "INFO"
            }
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Errore nell'esportazione del template: {e}")
            return False


# Funzione di convenienza per ottenere l'istanza singleton
def get_config() -> ConfigManager:
    """Restituisce l'istanza singleton del ConfigManager"""
    return ConfigManager()