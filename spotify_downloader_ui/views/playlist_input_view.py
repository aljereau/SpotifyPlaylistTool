"""
Playlist input view for entering and validating Spotify playlist URLs.
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QCheckBox, QFileDialog, QGridLayout, QComboBox,
    QFormLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService
from spotify_downloader_ui.services.playlist_service import PlaylistService
from spotify_downloader_ui.services.spotify_service import SpotifyService

logger = logging.getLogger(__name__)

class PlaylistInputView(QWidget):
    """Widget for entering and validating Spotify playlist URLs."""
    
    # Signals
    process_requested = Signal(str, dict)  # url, options
    
    def __init__(self, playlist_service: PlaylistService, spotify_service: SpotifyService,
                config_service: ConfigService, error_service: ErrorService):
        """Initialize the playlist input view.
        
        Args:
            playlist_service: Service for playlist operations
            spotify_service: Service for Spotify API operations
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        super().__init__()
        
        self.playlist_service = playlist_service
        self.spotify_service = spotify_service
        self.config_service = config_service
        self.error_service = error_service
        
        self._init_ui()
        self._connect_signals()
        
        logger.info("Playlist input view initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Title and description
        title_label = QLabel("Spotify Playlist Extractor")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        description_label = QLabel(
            "Enter a Spotify playlist URL to extract tracks, analyze, and discover hidden gems."
        )
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)
        
        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)
        main_layout.addSpacing(20)
        
        # Playlist URL input
        url_group = QGroupBox("Playlist URL")
        url_layout = QVBoxLayout(url_group)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://open.spotify.com/playlist/...")
        self.url_input.setFixedHeight(30)
        
        url_buttons_layout = QHBoxLayout()
        self.validate_button = QPushButton("Validate")
        self.process_button = QPushButton("Process Playlist")
        self.process_button.setEnabled(False)
        
        url_buttons_layout.addWidget(self.validate_button)
        url_buttons_layout.addWidget(self.process_button)
        
        url_layout.addWidget(self.url_input)
        url_layout.addLayout(url_buttons_layout)
        
        # Or load from file
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Or load from file:"))
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select a file with playlist URLs...")
        self.file_path_input.setReadOnly(True)
        
        self.browse_button = QPushButton("Browse")
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(self.browse_button)
        
        url_layout.addLayout(file_layout)
        
        main_layout.addWidget(url_group)
        
        # Playlist metadata preview
        self.preview_group = QGroupBox("Playlist Preview")
        self.preview_group.setVisible(False)
        preview_layout = QFormLayout(self.preview_group)
        
        self.preview_name = QLabel("")
        self.preview_owner = QLabel("")
        self.preview_tracks = QLabel("")
        self.preview_followers = QLabel("")
        
        preview_layout.addRow("Name:", self.preview_name)
        preview_layout.addRow("Owner:", self.preview_owner)
        preview_layout.addRow("Tracks:", self.preview_tracks)
        preview_layout.addRow("Followers:", self.preview_followers)
        
        main_layout.addWidget(self.preview_group)
        
        # Options
        options_group = QGroupBox("Processing Options")
        options_layout = QGridLayout(options_group)
        
        self.include_artist_checkbox = QCheckBox("Include artist name in filenames")
        self.create_folders_checkbox = QCheckBox("Create separate folder for each playlist")
        self.create_folders_checkbox.setChecked(True)
        
        # Add hidden gems options
        self.hidden_gems_checkbox = QCheckBox("Analyze for hidden gems")
        self.hidden_gems_checkbox.setChecked(True)
        
        min_pop_layout = QHBoxLayout()
        min_pop_layout.addWidget(QLabel("Min popularity:"))
        self.min_pop_input = QComboBox()
        for i in range(0, 45, 5):
            self.min_pop_input.addItem(str(i), i)
        self.min_pop_input.setCurrentIndex(1)  # Default to 5
        min_pop_layout.addWidget(self.min_pop_input)
        
        max_pop_layout = QHBoxLayout()
        max_pop_layout.addWidget(QLabel("Max popularity:"))
        self.max_pop_input = QComboBox()
        for i in range(20, 65, 5):
            self.max_pop_input.addItem(str(i), i)
        self.max_pop_input.setCurrentIndex(4)  # Default to 40
        max_pop_layout.addWidget(self.max_pop_input)
        
        options_layout.addWidget(self.include_artist_checkbox, 0, 0)
        options_layout.addWidget(self.create_folders_checkbox, 0, 1)
        options_layout.addWidget(self.hidden_gems_checkbox, 1, 0, 1, 2)
        options_layout.addLayout(min_pop_layout, 2, 0)
        options_layout.addLayout(max_pop_layout, 2, 1)
        
        main_layout.addWidget(options_group)
        
        # Output directory
        output_group = QGroupBox("Output Settings")
        output_layout = QHBoxLayout(output_group)
        
        output_layout.addWidget(QLabel("Output directory:"))
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setReadOnly(True)
        
        # Load from config
        output_dir = self.config_service.get_setting("output/directory")
        self.output_dir_input.setText(output_dir)
        
        self.output_dir_button = QPushButton("Change")
        output_layout.addWidget(self.output_dir_input)
        output_layout.addWidget(self.output_dir_button)
        
        main_layout.addWidget(output_group)
        
        # Add spacer
        main_layout.addStretch(1)
        
        # Status
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_layout = QHBoxLayout(status_frame)
        
        self.status_label = QLabel("Ready to process Spotify playlists")
        status_layout.addWidget(self.status_label)
        
        main_layout.addWidget(status_frame)
    
    def _connect_signals(self):
        """Connect signals to slots."""
        # Button signals
        self.validate_button.clicked.connect(self._on_validate_clicked)
        self.process_button.clicked.connect(self._on_process_clicked)
        self.browse_button.clicked.connect(self._on_browse_clicked)
        self.output_dir_button.clicked.connect(self._on_output_dir_clicked)
        
        # Service signals
        self.playlist_service.playlist_validation_completed.connect(self._on_validation_completed)
        self.playlist_service.playlist_metadata_loaded.connect(self._on_metadata_loaded)
        
        # Option changes
        self.hidden_gems_checkbox.toggled.connect(self._on_hidden_gems_toggled)
        
        # URL input enter key
        self.url_input.returnPressed.connect(self._on_validate_clicked)
    
    @Slot()
    def _on_validate_clicked(self):
        """Handle validate button click."""
        url = self.url_input.text().strip()
        if not url:
            self.status_label.setText("Please enter a valid Spotify playlist URL")
            return
        
        self.status_label.setText("Validating playlist URL...")
        playlist_id = self.playlist_service.validate_playlist_url(url)
        
        if playlist_id:
            # Now get metadata
            self.playlist_service.get_playlist_metadata(url)
    
    @Slot(str)
    def _on_validation_completed(self, playlist_id: str):
        """Handle playlist URL validation completion.
        
        Args:
            playlist_id: The validated playlist ID
        """
        self.status_label.setText(f"Valid playlist ID: {playlist_id}")
    
    @Slot(dict)
    def _on_metadata_loaded(self, metadata: dict):
        """Handle playlist metadata loading.
        
        Args:
            metadata: The playlist metadata
        """
        # Update preview
        self.preview_name.setText(metadata.get('name', 'Unknown'))
        self.preview_owner.setText(metadata.get('owner', 'Unknown'))
        self.preview_tracks.setText(str(metadata.get('total_tracks', 0)))
        self.preview_followers.setText(str(metadata.get('followers', 0)))
        
        # Show preview and enable process button
        self.preview_group.setVisible(True)
        self.process_button.setEnabled(True)
        
        self.status_label.setText(f"Playlist loaded: {metadata.get('name', 'Unknown')}")
    
    @Slot()
    def _on_process_clicked(self):
        """Handle process button click."""
        url = self.url_input.text().strip()
        
        # Collect options
        options = {
            "include_artist": self.include_artist_checkbox.isChecked(),
            "create_playlist_folders": self.create_folders_checkbox.isChecked(),
            "analyze_hidden_gems": self.hidden_gems_checkbox.isChecked(),
            "min_popularity": self.min_pop_input.currentData(),
            "max_popularity": self.max_pop_input.currentData()
        }
        
        # Emit signal with URL and options
        self.process_requested.emit(url, options)
        
        self.status_label.setText("Processing playlist...")
    
    @Slot()
    def _on_browse_clicked(self):
        """Handle browse button click for playlist file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Playlist File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            self.file_path_input.setText(file_path)
            
            try:
                # Read playlist URLs from file
                urls = self.playlist_service.read_playlist_urls_from_file(file_path)
                if urls:
                    # Set the first URL in the input field
                    self.url_input.setText(urls[0])
                    self.status_label.setText(f"Loaded {len(urls)} playlist URLs from file")
                    
                    # Validate the first URL
                    self._on_validate_clicked()
            except Exception as e:
                self.error_service.handle_error(e, self)
    
    @Slot()
    def _on_output_dir_clicked(self):
        """Handle output directory button click."""
        current_dir = self.output_dir_input.text()
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            current_dir
        )
        
        if dir_path:
            self.output_dir_input.setText(dir_path)
            self.config_service.set_setting("output/directory", dir_path)
            self.status_label.setText(f"Output directory set to: {dir_path}")
    
    @Slot(bool)
    def _on_hidden_gems_toggled(self, checked: bool):
        """Handle hidden gems checkbox toggle.
        
        Args:
            checked: Whether the checkbox is checked
        """
        # Enable/disable popularity controls based on checkbox
        self.min_pop_input.setEnabled(checked)
        self.max_pop_input.setEnabled(checked) 