"""
Main window for the Spotify Downloader UI.
"""

import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QToolBar, QStatusBar, QLabel, QPushButton, QMenu
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QAction, QAction, QAction

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService
from spotify_downloader_ui.services.playlist_service import PlaylistService
from spotify_downloader_ui.services.spotify_service import SpotifyService
from spotify_downloader_ui.views.playlist_input_view import PlaylistInputView
from spotify_downloader_ui.views.processing_view import ProcessingView
from spotify_downloader_ui.views.results_view import ResultsView
from spotify_downloader_ui.views.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main window for the Spotify Downloader UI."""
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the main window.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        super().__init__()
        
        # Store services
        self.config_service = config_service
        self.error_service = error_service
        
        # Initialize additional services
        self.playlist_service = PlaylistService()
        self.spotify_service = SpotifyService()
        
        # Set up the UI
        self._init_ui()
        self._setup_connections()
        
        # Initialize state
        self.current_playlist_id = None
        self.current_output_dir = None
        
        logger.info("Main window initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Set window properties
        self.setWindowTitle("Spotify Downloader UI")
        self.setMinimumSize(900, 700)
        
        # Create central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        self._create_toolbar()
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)
        
        # Create views
        self._create_views()
        
        # Add tabs
        self.tabs.addTab(self.playlist_input_view, "Playlist Input")
        self.tabs.addTab(self.processing_view, "Processing")
        self.tabs.addTab(self.results_view, "Results")
        
        # Initially disable processing and results tabs
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        
        main_layout.addWidget(self.tabs)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Initial status message
        self.status_bar.showMessage("Ready")
    
    def _create_toolbar(self):
        """Create the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._on_settings_action)
        toolbar.addAction(settings_action)
        
        toolbar.addSeparator()
        
        # Help menu
        help_menu = QMenu("Help", self)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._on_about_action)
        help_menu.addAction(about_action)
        
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self._on_documentation_action)
        help_menu.addAction(docs_action)
        
        help_btn = QPushButton("Help")
        help_btn.setMenu(help_menu)
        
        help_action = toolbar.addWidget(help_btn)
        
        self.addToolBar(toolbar)
    
    def _create_views(self):
        """Create the view components."""
        # Create playlist input view
        self.playlist_input_view = PlaylistInputView(
            self.playlist_service,
            self.spotify_service,
            self.config_service,
            self.error_service
        )
        
        # Create processing view
        self.processing_view = ProcessingView(
            self.playlist_service,
            self.config_service,
            self.error_service
        )
        
        # Create results view
        self.results_view = ResultsView(
            self.playlist_service,
            self.spotify_service,
            self.config_service,
            self.error_service
        )
    
    def _setup_connections(self):
        """Set up signal/slot connections."""
        # Connect playlist input view signals
        self.playlist_input_view.process_requested.connect(self._on_process_requested)
        
        # Connect service signals
        self.playlist_service.playlist_processing_started.connect(self._on_processing_started)
        self.playlist_service.playlist_processed.connect(self._on_processing_completed)
    
    @Slot(str, dict)
    def _on_process_requested(self, url: str, options: dict):
        """Handle process request from playlist input view.
        
        Args:
            url: The playlist URL to process
            options: Processing options dictionary
        """
        # Enable processing tab and switch to it
        self.tabs.setTabEnabled(1, True)
        self.tabs.setCurrentIndex(1)
        
        # Start processing
        self.playlist_service.process_playlist(url, options)
        
        # Update status
        self.status_bar.showMessage(f"Processing playlist: {url}")
    
    @Slot(str)
    def _on_processing_started(self, playlist_id: str):
        """Handle processing started.
        
        Args:
            playlist_id: The playlist ID being processed
        """
        self.current_playlist_id = playlist_id
        
        # Update status
        self.status_bar.showMessage(f"Processing playlist: {playlist_id}")
    
    @Slot(str, dict, list, str)
    def _on_processing_completed(self, playlist_id: str, metadata: dict, tracks: list, output_dir: str):
        """Handle processing completion.
        
        Args:
            playlist_id: The processed playlist ID
            metadata: Playlist metadata dictionary
            tracks: List of track dictionaries
            output_dir: Directory where output files are saved
        """
        # Store output directory
        self.current_output_dir = output_dir
        
        # Enable results tab and switch to it
        self.tabs.setTabEnabled(2, True)
        self.tabs.setCurrentIndex(2)
        
        # Display results
        self.results_view.display_results(playlist_id, metadata, tracks, output_dir)
        
        # Update status
        self.status_bar.showMessage(f"Completed processing playlist: {metadata.get('name', playlist_id)}")
    
    @Slot()
    def _on_settings_action(self):
        """Handle settings action."""
        settings_dialog = SettingsDialog(
            self.config_service,
            self.error_service,
            self
        )
        
        result = settings_dialog.exec_()
        if result == SettingsDialog.DialogCode.Accepted:
            # Handle settings update
            self.status_bar.showMessage("Settings updated")
    
    @Slot()
    def _on_about_action(self):
        """Handle about action."""
        from PySide6.QtWidgets import QMessageBox
        
        QMessageBox.about(
            self,
            "About Spotify Downloader UI",
            "<h3>Spotify Downloader UI</h3>"
            "<p>Version 0.1.0</p>"
            "<p>A modern, user-friendly graphical interface for extracting and analyzing "
            "track information from Spotify playlists.</p>"
            "<p>Built with PySide6</p>"
            "<p>© 2023-2024 SpotifyDownloader</p>"
        )
    
    @Slot()
    def _on_documentation_action(self):
        """Handle documentation action."""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        
        # Open GitHub repo or documentation site in the default browser
        QDesktopServices.openUrl(QUrl("https://github.com/aljereau/Spotify-Downloader"))
    
    def closeEvent(self, event):
        """Handle window close event.
        
        Args:
            event: Close event
        """
        # Clean up any resources
        logger.info("Application shutting down")
        event.accept() 