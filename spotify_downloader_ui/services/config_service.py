"""
Configuration service for the Spotify Downloader UI.
"""

import os
import logging
import json
from typing import Any, Dict, Optional
from PySide6.QtCore import QSettings

logger = logging.getLogger(__name__)

class ConfigService:
    """Service for managing application configuration and settings."""
    
    def __init__(self):
        """Initialize the configuration service."""
        self.settings = QSettings()
        self._initialize_default_settings()
        logger.info("Configuration service initialized")
    
    def _initialize_default_settings(self):
        """Initialize default settings if they don't exist."""
        # Default appearance settings
        if not self.settings.contains("appearance/theme"):
            self.settings.setValue("appearance/theme", "light")
        
        # Default output settings
        if not self.settings.contains("output/directory"):
            default_output = os.path.join(os.path.expanduser("~"), "SpotifyDownloader")
            self.settings.setValue("output/directory", default_output)
            
            # Create the directory if it doesn't exist
            if not os.path.exists(default_output):
                try:
                    os.makedirs(default_output)
                    logger.info(f"Created default output directory: {default_output}")
                except Exception as e:
                    logger.error(f"Failed to create default output directory: {e}")
        
        # Default playlist settings
        if not self.settings.contains("playlist/create_subfolders"):
            self.settings.setValue("playlist/create_subfolders", True)
        
        # Default Spotify API settings
        if not self.settings.contains("spotify/credentials_path"):
            self.settings.setValue("spotify/credentials_path", ".env")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value.
        
        Args:
            key: The setting key in format "section/name"
            default: Default value if setting doesn't exist
            
        Returns:
            The setting value or default if not found
        """
        return self.settings.value(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value.
        
        Args:
            key: The setting key in format "section/name"
            value: The value to set
        """
        self.settings.setValue(key, value)
        logger.debug(f"Setting updated: {key} = {value}")
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary.
        
        Returns:
            Dictionary of all settings
        """
        result = {}
        self.settings.sync()
        
        # Iterate through all keys and values
        for key in self.settings.allKeys():
            result[key] = self.settings.value(key)
        
        return result
    
    def export_settings(self, filepath: str) -> bool:
        """Export settings to a JSON file.
        
        Args:
            filepath: Path to save the settings file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            settings_dict = self.get_all_settings()
            with open(filepath, 'w') as f:
                json.dump(settings_dict, f, indent=2)
            logger.info(f"Settings exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return False
    
    def import_settings(self, filepath: str) -> bool:
        """Import settings from a JSON file.
        
        Args:
            filepath: Path to the settings file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                settings_dict = json.load(f)
            
            # Apply all settings
            for key, value in settings_dict.items():
                self.settings.setValue(key, value)
            
            self.settings.sync()
            logger.info(f"Settings imported from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.settings.clear()
        self._initialize_default_settings()
        logger.info("Settings reset to defaults") 