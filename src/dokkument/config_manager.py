"""
ConfigManager - Manages application configurations and preferences
Implements the Singleton pattern for global configuration
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import threading


class ConfigManager:
    """Singleton for managing application configuration"""

    _instance: Optional["ConfigManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Avoid reinitialization if the instance exists
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._config: Dict[str, Any] = {}
        self._config_file: Optional[Path] = None
        self._load_default_config()
        self._find_and_load_config_file()

    def _load_default_config(self):
        """Load the default configuration"""
        self._config = {
            "scanning": {
                "recursive": True,
                "max_depth": 10,
                "excluded_dirs": [
                    ".git",
                    "__pycache__",
                    "node_modules",
                    ".venv",
                    "venv",
                ],
                "file_patterns": ["*.dokk"],
            },
            "display": {
                "enable_colors": True,
                "enable_hyperlinks": True,
                "group_by_file": True,
                "max_description_length": 80,
                "show_file_names": True,
                "confirm_open_all": True,
            },
            "browser": {
                "preferred_browser": None,                
                "open_delay_seconds": 0.5,
                "max_concurrent_opens": 10,
            },
            "security": {
                "validate_urls": True,
                "allowed_schemes": ["http", "https"],
                "warn_on_suspicious_urls": True,
            },
            "advanced": {
                "cache_scan_results": False,
                "auto_reload_on_change": False,
                "debug_mode": False,
                "log_level": "INFO",
            },
        }

    def _find_and_load_config_file(self):
        """Find and load the user's configuration file"""
        possible_locations = [
            Path.cwd() / ".dokkument.json",
            Path.cwd() / "dokkument.json",
            Path.home() / ".dokkument.json",
            Path.home() / ".config" / "dokkument" / "config.json",
        ]

        # On Windows, add AppData
        if os.name == "nt":
            appdata = os.environ.get("APPDATA")
            if appdata:
                possible_locations.append(Path(appdata) / "dokkument" / "config.json")

        # On Unix-like, add XDG_CONFIG_HOME
        else:
            xdg_config = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config:
                possible_locations.append(
                    Path(xdg_config) / "dokkument" / "config.json"
                )

        for config_path in possible_locations:
            if config_path.exists() and config_path.is_file():
                try:
                    self._load_config_from_file(config_path)
                    self._config_file = config_path
                    break
                except Exception as config_error:  # pylint: disable=broad-except
                    print(
                        f"Warning: Error loading configuration from {config_path}: {config_error}"
                    )
                    continue

    def _load_config_from_file(self, config_path: Path):
        """Load configuration from a JSON file"""
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)

        # Recursive merge of user configuration with default
        self._merge_config(self._config, user_config)

    def _merge_config(self, default: Dict, user: Dict):
        """Recursive merge of two configuration dictionaries"""
        for key, value in user.items():
            if (
                key in default
                and isinstance(default[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_config(default[key], value)
            else:
                default[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation

        Args:
            key_path: Key path (e.g. 'display.enable_colors')
            default: Default value if key doesn't exist

        Returns:
            The configuration value or the default
        """
        keys = key_path.split(".")
        current = self._config

        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any):
        """
        Set a configuration value using dot notation

        Args:
            key_path: Key path (e.g. 'display.enable_colors')
            value: Value to set
        """
        keys = key_path.split(".")
        current = self._config

        # Navigate to the penultimate level
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the final value
        current[keys[-1]] = value

    def save_config(self, config_path: Path = None) -> bool:
        """
        Save the current configuration to file

        Args:
            config_path: File path (optional, uses current if not specified)

        Returns:
            bool: True if save was successful
        """
        if config_path is None:
            if self._config_file is None:
                # If there is no existing configuration file, create one in home
                config_path = Path.home() / ".dokkument.json"
            else:
                config_path = self._config_file

        try:
            # Create the directory if it doesn't exist
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

            self._config_file = config_path
            return True

        except Exception as config_error:  # pylint: disable=broad-except
            print(f"Error saving configuration: {config_error}")
            return False

    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self._load_default_config()

    def get_config_file_path(self) -> Optional[Path]:
        """Return the path of the current configuration file"""
        return self._config_file

    def get_all_config(self) -> Dict[str, Any]:
        """Return a copy of all configuration"""
        import copy  # pylint: disable=import-outside-toplevel

        return copy.deepcopy(self._config)

    def update_config(self, new_config: Dict[str, Any]):
        """
        Update configuration with a new dictionary

        Args:
            new_config: New configuration dictionary
        """
        self._merge_config(self._config, new_config)

    def validate_config(self) -> List[str]:
        """
        Validate the current configuration

        Returns:
            List[str]: List of validation errors (empty if all OK)
        """
        errors = []

        try:
            # Validate scanning settings
            if not isinstance(self.get("scanning.recursive"), bool):
                errors.append("scanning.recursive must be a boolean")

            if (
                not isinstance(self.get("scanning.max_depth"), int)
                or self.get("scanning.max_depth") < 1
            ):
                errors.append("scanning.max_depth must be a positive integer")

            # Validate display settings
            if not isinstance(self.get("display.enable_colors"), bool):
                errors.append("display.enable_colors must be a boolean")

            # Validate browser settings
            browser = self.get("browser.preferred_browser")
            if browser is not None and not isinstance(browser, str):
                errors.append(
                    "browser.preferred_browser must be None or a string"
                )

            # Validate allowed URL schemes
            allowed_schemes = self.get("security.allowed_schemes", [])
            if not isinstance(allowed_schemes, list):
                errors.append("security.allowed_schemes must be a list")
            elif not all(isinstance(scheme, str) for scheme in allowed_schemes):
                errors.append(
                    "All elements in security.allowed_schemes must be strings"
                )

        except Exception as config_error:  # pylint: disable=broad-except
            errors.append(f"General error in validation: {config_error}")

        return errors

    def print_config_info(self):
        """Print information about the current configuration"""
        print(" Configuration Information dokkument")
        print("=" * 50)

        if self._config_file:
            print(f" Configuration file: {self._config_file}")
        else:
            print(" Configuration file: None (using default configuration)")

        print(f"= Recursive scanning: {self.get('scanning.recursive')}")
        print(f" Colors enabled: {self.get('display.enable_colors')}")
        print(f"= Clickable links: {self.get('display.enable_hyperlinks')}")
        print(
            f"< Preferred browser: {self.get('browser.preferred_browser') or 'System default'}"
        )
        print(f"= URL validation: {self.get('security.validate_urls')}")
        print(f"= Debug mode: {self.get('advanced.debug_mode')}")

        # Validation
        errors = self.validate_config()
        if errors:
            print("\n Configuration errors:")
            for error in errors:
                print(f"    {error}")
        else:
            print("\n Configuration is valid")

    def export_config_template(self, output_path: Path = None) -> bool:
        """
        Export a commented configuration template

        Args:
            output_path: Output file path (default: dokkument-config-template.json)

        Returns:
            bool: True if export was successful
        """
        if output_path is None:
            output_path = Path.cwd() / "dokkument-config-template.json"

        template = {
            "_comment": "Configuration template for dokkument - Remove this comment to use it",
            "_instructions": "Copy this file as .dokkument.json in your home directory or project",
            "scanning": {
                "_comment": "Settings for scanning .dokk files",
                "recursive": True,
                "max_depth": 10,
                "excluded_dirs": [
                    ".git",
                    "__pycache__",
                    "node_modules",
                    ".venv",
                    "venv",
                ],
                "file_patterns": ["*.dokk"],
            },
            "display": {
                "_comment": "Interface display settings",
                "enable_colors": True,
                "enable_hyperlinks": True,
                "group_by_file": True,
                "max_description_length": 80,
                "show_file_names": True,
                "confirm_open_all": True,
            },
            "browser": {
                "_comment": "Browser settings - preferred_browser: null, 'firefox', 'chrome', etc.",
                "preferred_browser": None,
                "open_delay_seconds": 0.5,
                "max_concurrent_opens": 10,
            },
            "security": {
                "_comment": "Security settings for URL validation",
                "validate_urls": True,
                "allowed_schemes": ["http", "https"],
                "warn_on_suspicious_urls": True,
            },
            "advanced": {
                "_comment": "Advanced settings - modify only if you know what you're doing",
                "cache_scan_results": False,
                "auto_reload_on_change": False,
                "debug_mode": False,
                "log_level": "INFO",
            },
        }

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            return True
        except Exception as config_error:  # pylint: disable=broad-except
            print(f"Error exporting template: {config_error}")
            return False


# Convenience function to get the singleton instance
def get_config() -> ConfigManager:
    """Return the singleton instance of ConfigManager"""
    return ConfigManager()
