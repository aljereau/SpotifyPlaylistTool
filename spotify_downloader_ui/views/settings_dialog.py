"""
Settings dialog for configuring application settings.
"""

import os
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QCheckBox, QFileDialog, QTabWidget, QWidget, QFormLayout,
    QComboBox, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, Slot

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService, parent=None):
        """Initialize the settings dialog.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.config_service = config_service
        self.error_service = error_service
        
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self._init_ui()
        self._load_settings()
        
        logger.info("Settings dialog initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Output directory
        output_group = QGroupBox("Output Settings")
        output_layout = QFormLayout(output_group)
        
        output_dir_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setReadOnly(True)
        self.output_dir_button = QPushButton("Browse")
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(self.output_dir_button)
        
        output_layout.addRow("Output Directory:", output_dir_layout)
        
        # Folder options
        self.create_folders_checkbox = QCheckBox("Create separate folder for each playlist")
        self.include_artist_checkbox = QCheckBox("Include artist name in filenames")
        
        output_layout.addRow("", self.create_folders_checkbox)
        output_layout.addRow("", self.include_artist_checkbox)
        
        general_layout.addWidget(output_group)
        
        # Appearance
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Dark", "dark")
        
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        general_layout.addWidget(appearance_group)
        
        # Spotify tab
        spotify_tab = QWidget()
        spotify_layout = QVBoxLayout(spotify_tab)
        
        # API credentials
        api_group = QGroupBox("Spotify API Credentials")
        api_layout = QFormLayout(api_group)
        
        self.credentials_path_input = QLineEdit()
        self.credentials_path_input.setReadOnly(True)
        
        credentials_layout = QHBoxLayout()
        credentials_layout.addWidget(self.credentials_path_input)
        
        self.credentials_browse_button = QPushButton("Browse")
        credentials_layout.addWidget(self.credentials_browse_button)
        
        api_layout.addRow("Credentials File:", credentials_layout)
        
        # Client ID and Secret manual input (alternative)
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Spotify Client ID")
        
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("Spotify Client Secret")
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        api_layout.addRow("Client ID:", self.client_id_input)
        api_layout.addRow("Client Secret:", self.client_secret_input)
        
        self.save_credentials_button = QPushButton("Save Credentials")
        api_layout.addRow("", self.save_credentials_button)
        
        spotify_layout.addWidget(api_group)
        
        # Hidden gems options
        gems_group = QGroupBox("Hidden Gems Default Settings")
        gems_layout = QFormLayout(gems_group)
        
        self.default_min_pop = QComboBox()
        for i in range(0, 45, 5):
            self.default_min_pop.addItem(str(i), i)
        
        self.default_max_pop = QComboBox()
        for i in range(20, 65, 5):
            self.default_max_pop.addItem(str(i), i)
            
        self.default_min_score = QComboBox()
        for i in range(0, 55, 5):
            self.default_min_score.addItem(str(i), i)
        
        gems_layout.addRow("Default Min Popularity:", self.default_min_pop)
        gems_layout.addRow("Default Max Popularity:", self.default_max_pop)
        gems_layout.addRow("Default Min Score:", self.default_min_score)
        
        spotify_layout.addWidget(gems_group)
        
        # Advanced tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # Logging
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)
        
        self.enable_logging_checkbox = QCheckBox("Enable logging to file")
        logging_layout.addRow("", self.enable_logging_checkbox)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("Debug", "debug")
        self.log_level_combo.addItem("Info", "info")
        self.log_level_combo.addItem("Warning", "warning")
        self.log_level_combo.addItem("Error", "error")
        
        logging_layout.addRow("Log Level:", self.log_level_combo)
        
        advanced_layout.addWidget(logging_group)
        
        # Data management
        data_group = QGroupBox("Data Management")
        data_layout = QVBoxLayout(data_group)
        
        self.import_settings_button = QPushButton("Import Settings")
        self.export_settings_button = QPushButton("Export Settings")
        self.reset_settings_button = QPushButton("Reset to Defaults")
        
        data_layout.addWidget(self.import_settings_button)
        data_layout.addWidget(self.export_settings_button)
        data_layout.addWidget(self.reset_settings_button)
        
        advanced_layout.addWidget(data_group)
        advanced_layout.addStretch(1)
        
        # Add all tabs
        self.tabs.addTab(general_tab, "General")
        self.tabs.addTab(spotify_tab, "Spotify")
        self.tabs.addTab(advanced_tab, "Advanced")
        
        main_layout.addWidget(self.tabs)
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)
        
        # Connect signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect signals to slots."""
        # Browse buttons
        self.output_dir_button.clicked.connect(self._on_output_dir_browse)
        self.credentials_browse_button.clicked.connect(self._on_credentials_browse)
        
        # Save buttons
        self.save_credentials_button.clicked.connect(self._on_save_credentials)
        
        # Data management
        self.import_settings_button.clicked.connect(self._on_import_settings)
        self.export_settings_button.clicked.connect(self._on_export_settings)
        self.reset_settings_button.clicked.connect(self._on_reset_settings)
    
    def _load_settings(self):
        """Load settings from config service."""
        # Output settings
        output_dir = self.config_service.get_setting("output/directory")
        self.output_dir_input.setText(output_dir)
        
        create_folders = self.config_service.get_setting("playlist/create_subfolders", True)
        self.create_folders_checkbox.setChecked(create_folders)
        
        include_artist = self.config_service.get_setting("playlist/include_artist", False)
        self.include_artist_checkbox.setChecked(include_artist)
        
        # Appearance
        theme = self.config_service.get_setting("appearance/theme", "light")
        theme_index = self.theme_combo.findData(theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        
        # Spotify settings
        credentials_path = self.config_service.get_setting("spotify/credentials_path", ".env")
        self.credentials_path_input.setText(credentials_path)
        
        client_id = self.config_service.get_setting("spotify/client_id", "")
        self.client_id_input.setText(client_id)
        
        client_secret = self.config_service.get_setting("spotify/client_secret", "")
        self.client_secret_input.setText(client_secret)
        
        # Hidden gems defaults
        min_pop = self.config_service.get_setting("hidden_gems/min_popularity", 5)
        max_pop = self.config_service.get_setting("hidden_gems/max_popularity", 40)
        min_score = self.config_service.get_setting("hidden_gems/min_score", 20)
        
        min_pop_index = self.default_min_pop.findData(min_pop)
        if min_pop_index >= 0:
            self.default_min_pop.setCurrentIndex(min_pop_index)
        else:
            self.default_min_pop.setCurrentIndex(1)  # Default to 5
        
        max_pop_index = self.default_max_pop.findData(max_pop)
        if max_pop_index >= 0:
            self.default_max_pop.setCurrentIndex(max_pop_index)
        else:
            self.default_max_pop.setCurrentIndex(4)  # Default to 40
        
        min_score_index = self.default_min_score.findData(min_score)
        if min_score_index >= 0:
            self.default_min_score.setCurrentIndex(min_score_index)
        else:
            self.default_min_score.setCurrentIndex(4)  # Default to 20
        
        # Logging
        enable_logging = self.config_service.get_setting("logging/enabled", True)
        self.enable_logging_checkbox.setChecked(enable_logging)
        
        log_level = self.config_service.get_setting("logging/level", "info")
        log_level_index = self.log_level_combo.findData(log_level)
        if log_level_index >= 0:
            self.log_level_combo.setCurrentIndex(log_level_index)
    
    def _save_settings(self):
        """Save settings to config service."""
        # Output settings
        self.config_service.set_setting("output/directory", self.output_dir_input.text())
        self.config_service.set_setting("playlist/create_subfolders", self.create_folders_checkbox.isChecked())
        self.config_service.set_setting("playlist/include_artist", self.include_artist_checkbox.isChecked())
        
        # Appearance
        self.config_service.set_setting("appearance/theme", self.theme_combo.currentData())
        
        # Spotify settings
        self.config_service.set_setting("spotify/credentials_path", self.credentials_path_input.text())
        
        # Only save if not empty
        if self.client_id_input.text():
            self.config_service.set_setting("spotify/client_id", self.client_id_input.text())
        
        if self.client_secret_input.text():
            self.config_service.set_setting("spotify/client_secret", self.client_secret_input.text())
        
        # Hidden gems defaults
        self.config_service.set_setting("hidden_gems/min_popularity", self.default_min_pop.currentData())
        self.config_service.set_setting("hidden_gems/max_popularity", self.default_max_pop.currentData())
        self.config_service.set_setting("hidden_gems/min_score", self.default_min_score.currentData())
        
        # Logging
        self.config_service.set_setting("logging/enabled", self.enable_logging_checkbox.isChecked())
        self.config_service.set_setting("logging/level", self.log_level_combo.currentData())
        
        logger.info("Settings saved")
    
    @Slot()
    def _on_output_dir_browse(self):
        """Handle output directory browse button click."""
        current_dir = self.output_dir_input.text()
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            current_dir
        )
        
        if dir_path:
            self.output_dir_input.setText(dir_path)
    
    @Slot()
    def _on_credentials_browse(self):
        """Handle credentials file browse button click."""
        current_path = self.credentials_path_input.text()
        current_dir = os.path.dirname(current_path) if os.path.dirname(current_path) else ""
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Credentials File",
            current_dir,
            "Environment Files (*.env);;All Files (*)"
        )
        
        if file_path:
            self.credentials_path_input.setText(file_path)
    
    @Slot()
    def _on_save_credentials(self):
        """Handle save credentials button click."""
        # Check for required values
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()
        
        if not client_id or not client_secret:
            QMessageBox.warning(
                self,
                "Missing Credentials",
                "Client ID and Client Secret are required."
            )
            return
        
        # Save to config service
        self.config_service.set_setting("spotify/client_id", client_id)
        self.config_service.set_setting("spotify/client_secret", client_secret)
        
        # Try to save to .env file as well if specified
        try:
            env_path = self.credentials_path_input.text()
            if env_path and os.path.isfile(env_path):
                # Read existing file
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                
                # Update ID and secret
                id_found = False
                secret_found = False
                for i, line in enumerate(lines):
                    if line.startswith('SPOTIFY_CLIENT_ID='):
                        lines[i] = f'SPOTIFY_CLIENT_ID={client_id}\n'
                        id_found = True
                    elif line.startswith('SPOTIFY_CLIENT_SECRET='):
                        lines[i] = f'SPOTIFY_CLIENT_SECRET={client_secret}\n'
                        secret_found = True
                
                # Add if not found
                if not id_found:
                    lines.append(f'SPOTIFY_CLIENT_ID={client_id}\n')
                if not secret_found:
                    lines.append(f'SPOTIFY_CLIENT_SECRET={client_secret}\n')
                
                # Write back
                with open(env_path, 'w') as f:
                    f.writelines(lines)
                
                QMessageBox.information(
                    self,
                    "Credentials Saved",
                    f"Spotify API credentials saved successfully to:\n{env_path}"
                )
            else:
                QMessageBox.information(
                    self,
                    "Credentials Saved",
                    "Spotify API credentials saved to application settings."
                )
        except Exception as e:
            self.error_service.handle_error(e, self)
    
    @Slot()
    def _on_import_settings(self):
        """Handle import settings button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Settings",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                if self.config_service.import_settings(file_path):
                    QMessageBox.information(
                        self,
                        "Import Successful",
                        "Settings imported successfully. Restart the application for all changes to take effect."
                    )
                    self._load_settings()  # Reload settings in dialog
                else:
                    QMessageBox.warning(
                        self,
                        "Import Failed",
                        "Failed to import settings. The file may be invalid or corrupted."
                    )
            except Exception as e:
                self.error_service.handle_error(e, self)
    
    @Slot()
    def _on_export_settings(self):
        """Handle export settings button click."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                if self.config_service.export_settings(file_path):
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Settings exported successfully to:\n{file_path}"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Export Failed",
                        "Failed to export settings."
                    )
            except Exception as e:
                self.error_service.handle_error(e, self)
    
    @Slot()
    def _on_reset_settings(self):
        """Handle reset settings button click."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config_service.reset_to_defaults()
            self._load_settings()
            QMessageBox.information(
                self,
                "Reset Complete",
                "Settings have been reset to defaults."
            )
    
    def accept(self):
        """Handle dialog accept."""
        self._save_settings()
        super().accept()
        
    def reject(self):
        """Handle dialog reject."""
        super().reject() 