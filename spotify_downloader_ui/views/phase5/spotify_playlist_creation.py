"""
Spotify Playlist Creation component for creating and managing Spotify playlists.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QProgressBar,
    QListWidget, QListWidgetItem, QScrollArea, QFrame, QFileDialog,
    QTabWidget, QSplitter, QGroupBox, QGridLayout, QCompleter
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QPixmap

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService

logger = logging.getLogger(__name__)

class PlaylistMetadataEditor(QWidget):
    """Editor for playlist metadata (title, description, cover, privacy)."""
    
    metadata_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title field
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter playlist title")
        self.title_edit.textChanged.connect(self._emit_metadata_changed)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # Description field
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter playlist description")
        self.description_edit.setMaximumHeight(80)
        self.description_edit.textChanged.connect(self._emit_metadata_changed)
        layout.addWidget(self.description_edit)
        
        # Cover image
        cover_layout = QHBoxLayout()
        self.cover_frame = QFrame()
        self.cover_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.cover_frame.setFixedSize(100, 100)
        self.cover_label = QLabel("No Image")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("background-color: #f0f0f0;")
        
        cover_frame_layout = QVBoxLayout(self.cover_frame)
        cover_frame_layout.setContentsMargins(0, 0, 0, 0)
        cover_frame_layout.addWidget(self.cover_label)
        cover_layout.addWidget(self.cover_frame)
        
        cover_buttons_layout = QVBoxLayout()
        self.upload_button = QPushButton("Upload Image")
        self.upload_button.clicked.connect(self._on_upload_image)
        self.remove_button = QPushButton("Remove Image")
        self.remove_button.clicked.connect(self._on_remove_image)
        self.remove_button.setEnabled(False)
        
        cover_buttons_layout.addWidget(self.upload_button)
        cover_buttons_layout.addWidget(self.remove_button)
        cover_buttons_layout.addStretch()
        
        cover_layout.addLayout(cover_buttons_layout)
        cover_layout.addStretch()
        layout.addLayout(cover_layout)
        
        # Privacy settings
        privacy_layout = QHBoxLayout()
        privacy_layout.addWidget(QLabel("Privacy:"))
        self.privacy_combo = QComboBox()
        self.privacy_combo.addItems(["Public", "Private", "Unlisted"])
        self.privacy_combo.setCurrentIndex(1)  # Default to Private
        self.privacy_combo.currentIndexChanged.connect(self._emit_metadata_changed)
        privacy_layout.addWidget(self.privacy_combo)
        privacy_layout.addStretch()
        layout.addLayout(privacy_layout)
        
        # Collaborative option
        self.collaborative_checkbox = QCheckBox("Collaborative (allow others to modify)")
        self.collaborative_checkbox.stateChanged.connect(self._emit_metadata_changed)
        layout.addWidget(self.collaborative_checkbox)
        
        layout.addStretch()
    
    def get_metadata(self):
        return {
            "title": self.title_edit.text(),
            "description": self.description_edit.toPlainText(),
            "privacy": self.privacy_combo.currentText().lower(),
            "collaborative": self.collaborative_checkbox.isChecked(),
            "has_cover_image": self.remove_button.isEnabled()
        }
    
    def set_metadata(self, metadata):
        self.title_edit.setText(metadata.get("title", ""))
        self.description_edit.setText(metadata.get("description", ""))
        
        privacy = metadata.get("privacy", "private").lower()
        if privacy == "public":
            self.privacy_combo.setCurrentIndex(0)
        elif privacy == "private":
            self.privacy_combo.setCurrentIndex(1)
        else:  # unlisted
            self.privacy_combo.setCurrentIndex(2)
        
        self.collaborative_checkbox.setChecked(metadata.get("collaborative", False))
        
        # Cover image would be handled separately
    
    def set_cover_image(self, pixmap):
        if pixmap:
            scaled_pixmap = pixmap.scaled(
                self.cover_frame.size(), 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.cover_label.setPixmap(scaled_pixmap)
            self.remove_button.setEnabled(True)
            self._emit_metadata_changed()
    
    def _on_upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Cover Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.set_cover_image(pixmap)
            else:
                logger.error(f"Failed to load image: {file_path}")
    
    def _on_remove_image(self):
        self.cover_label.setText("No Image")
        self.cover_label.setPixmap(QPixmap())
        self.remove_button.setEnabled(False)
        self._emit_metadata_changed()
    
    def _emit_metadata_changed(self):
        self.metadata_changed.emit(self.get_metadata())

class TrackSelectionList(QWidget):
    """Widget for selecting tracks to include in a playlist."""
    
    selection_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_tracks = []
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Search and filter controls
        filter_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search tracks...")
        self.search_edit.textChanged.connect(self._on_search_changed)
        filter_layout.addWidget(self.search_edit)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Tracks", "Selected Only", "Not Selected"])
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        
        layout.addLayout(filter_layout)
        
        # Track list
        self.track_list = QListWidget()
        self.track_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.track_list.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.track_list)
        
        # Selection controls
        selection_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self._on_select_all)
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self._on_deselect_all)
        self.invert_selection_button = QPushButton("Invert Selection")
        self.invert_selection_button.clicked.connect(self._on_invert_selection)
        
        selection_layout.addWidget(self.select_all_button)
        selection_layout.addWidget(self.deselect_all_button)
        selection_layout.addWidget(self.invert_selection_button)
        
        layout.addLayout(selection_layout)
        
        # Selection info
        self.selection_info = QLabel("0 tracks selected")
        layout.addWidget(self.selection_info)
    
    def set_tracks(self, tracks):
        self.track_list.clear()
        self._selected_tracks = []
        
        for track in tracks:
            item = QListWidgetItem()
            item.setText(f"{track.get('name', 'Unknown')} - {track.get('artist', 'Unknown')}")
            item.setData(Qt.ItemDataRole.UserRole, track)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.track_list.addItem(item)
        
        self._update_selection_info()
    
    def get_selected_tracks(self):
        return self._selected_tracks
    
    def _on_item_changed(self, item):
        track = item.data(Qt.ItemDataRole.UserRole)
        if item.checkState() == Qt.CheckState.Checked:
            if track not in self._selected_tracks:
                self._selected_tracks.append(track)
        else:
            if track in self._selected_tracks:
                self._selected_tracks.remove(track)
        
        self._update_selection_info()
        self.selection_changed.emit(self._selected_tracks)
    
    def _on_select_all(self):
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
    
    def _on_deselect_all(self):
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
    
    def _on_invert_selection(self):
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                item.setCheckState(Qt.CheckState.Checked)
    
    def _on_search_changed(self, text):
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def _on_filter_changed(self, index):
        filter_type = self.filter_combo.currentText()
        
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            track = item.data(Qt.ItemDataRole.UserRole)
            
            if filter_type == "All Tracks":
                item.setHidden(False)
            elif filter_type == "Selected Only":
                item.setHidden(track not in self._selected_tracks)
            elif filter_type == "Not Selected":
                item.setHidden(track in self._selected_tracks)
    
    def _update_selection_info(self):
        count = len(self._selected_tracks)
        self.selection_info.setText(f"{count} tracks selected")

class PlaylistTemplateManager(QWidget):
    """Widget for managing playlist creation templates."""
    
    template_selected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._templates = []
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Template list
        layout.addWidget(QLabel("Available Templates:"))
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        layout.addWidget(self.template_list)
        
        # Template controls
        template_controls = QHBoxLayout()
        self.save_template_button = QPushButton("Save Current as Template")
        self.save_template_button.clicked.connect(self._on_save_template)
        self.delete_template_button = QPushButton("Delete Template")
        self.delete_template_button.clicked.connect(self._on_delete_template)
        self.delete_template_button.setEnabled(False)
        
        template_controls.addWidget(self.save_template_button)
        template_controls.addWidget(self.delete_template_button)
        
        layout.addLayout(template_controls)
    
    def set_templates(self, templates):
        self._templates = templates
        self.template_list.clear()
        
        for template in templates:
            item = QListWidgetItem()
            item.setText(template.get("name", "Unnamed Template"))
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)
    
    def add_template(self, template):
        self._templates.append(template)
        
        item = QListWidgetItem()
        item.setText(template.get("name", "Unnamed Template"))
        item.setData(Qt.ItemDataRole.UserRole, template)
        self.template_list.addItem(item)
    
    def _on_template_selected(self, current, previous):
        self.delete_template_button.setEnabled(current is not None)
        if current:
            template = current.data(Qt.ItemDataRole.UserRole)
            self.template_selected.emit(template)
    
    def _on_save_template(self):
        # Signal to parent to save current settings as template
        # In a real implementation, this would show a dialog to name the template
        logger.info("Save as template requested")
    
    def _on_delete_template(self):
        current_item = self.template_list.currentItem()
        if current_item:
            template = current_item.data(Qt.ItemDataRole.UserRole)
            row = self.template_list.row(current_item)
            self.template_list.takeItem(row)
            self._templates.remove(template)
            self.delete_template_button.setEnabled(False)

class SpotifyPlaylistCreation:
    """Component for creating and managing Spotify playlists."""
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the component.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        self._config_service = config_service
        self._error_service = error_service
        self._widget = self._create_widget()
        
        # Sample templates - in real implementation, these would come from config/storage
        self._sample_templates = [
            {
                "name": "Hidden Gems",
                "description": "A collection of hidden gems discovered by Spotify Downloader",
                "privacy": "private",
                "collaborative": False
            },
            {
                "name": "Weekly Discoveries",
                "description": "New music discovered this week",
                "privacy": "private",
                "collaborative": False
            },
            {
                "name": "Artist Spotlight",
                "description": "Featuring music from a specific artist and related acts",
                "privacy": "public",
                "collaborative": False
            }
        ]
        
        self._init_component()
        
        logger.info("Spotify Playlist Creation component initialized")
    
    def _create_widget(self):
        """Create the main widget for this component."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Create Spotify Playlist")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        # Action buttons
        self.create_button = QPushButton("Create Playlist")
        self.create_button.clicked.connect(self._on_create_playlist)
        header_layout.addWidget(self.create_button)
        
        main_layout.addLayout(header_layout)
        
        # Main content area with tabs
        self.tabs = QTabWidget()
        
        # Metadata tab
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout(metadata_tab)
        self.metadata_editor = PlaylistMetadataEditor()
        metadata_layout.addWidget(self.metadata_editor)
        self.tabs.addTab(metadata_tab, "Playlist Info")
        
        # Track selection tab
        tracks_tab = QWidget()
        tracks_layout = QVBoxLayout(tracks_tab)
        self.track_selection = TrackSelectionList()
        tracks_layout.addWidget(self.track_selection)
        self.tabs.addTab(tracks_tab, "Select Tracks")
        
        # Templates tab
        templates_tab = QWidget()
        templates_layout = QVBoxLayout(templates_tab)
        self.template_manager = PlaylistTemplateManager()
        templates_layout.addWidget(self.template_manager)
        self.tabs.addTab(templates_tab, "Templates")
        
        # History tab (placeholder for now)
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.addWidget(QLabel("Playlist creation history will appear here."))
        self.tabs.addTab(history_tab, "History")
        
        main_layout.addWidget(self.tabs)
        
        # Progress section
        self.progress_group = QGroupBox("Creation Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to create playlist")
        progress_layout.addWidget(self.status_label)
        
        self.progress_group.setLayout(progress_layout)
        self.progress_group.setVisible(False)  # Hide until creation starts
        
        main_layout.addWidget(self.progress_group)
        
        return container
    
    def _init_component(self):
        """Initialize the component with data and set up connections."""
        # Connect signals
        self.metadata_editor.metadata_changed.connect(self._on_metadata_changed)
        self.track_selection.selection_changed.connect(self._on_selection_changed)
        self.template_manager.template_selected.connect(self._on_template_selected)
        
        # Set sample templates
        self.template_manager.set_templates(self._sample_templates)
        
        # Set sample track data - in real implementation, this would come from elsewhere
        sample_tracks = []
        for i in range(1, 21):
            track = {
                "id": f"track{i}",
                "name": f"Sample Track {i}",
                "artist": f"Artist {(i % 5) + 1}",
                "album": f"Album {(i % 3) + 1}",
                "duration_ms": 180000 + (i * 10000),
                "popularity": 30 + (i % 50)
            }
            sample_tracks.append(track)
        
        self.track_selection.set_tracks(sample_tracks)
    
    @property
    def widget(self):
        """Get the widget for this component."""
        return self._widget
    
    def set_creation_data(self, data):
        """Set the playlist creation data.
        
        Args:
            data: Dictionary with playlist creation data
        """
        # Set metadata
        metadata = {
            "title": data.get("name", ""),
            "description": data.get("description", ""),
            "privacy": data.get("is_public", False) and "public" or "private",
            "collaborative": data.get("collaborative", False)
        }
        self.metadata_editor.set_metadata(metadata)
        
        # Set tracks if available
        if "tracks" in data and isinstance(data["tracks"], list):
            self.track_selection.set_tracks(data["tracks"])
        
        # Set templates if available
        if "templates" in data and isinstance(data["templates"], list):
            self.template_manager.set_templates(data["templates"])
    
    def _on_metadata_changed(self, metadata):
        """Handle metadata changes."""
        logger.debug(f"Playlist metadata changed: {metadata}")
        # In a real implementation, this might update a model or validate
    
    def _on_selection_changed(self, selected_tracks):
        """Handle track selection changes."""
        logger.debug(f"Track selection changed: {len(selected_tracks)} tracks selected")
        # In a real implementation, this might update a model or validate
    
    def _on_template_selected(self, template):
        """Handle template selection."""
        logger.info(f"Template selected: {template.get('name', 'Unnamed')}")
        self.metadata_editor.set_metadata(template)
    
    def _on_create_playlist(self):
        """Handle create playlist button click."""
        metadata = self.metadata_editor.get_metadata()
        selected_tracks = self.track_selection.get_selected_tracks()
        
        if not metadata.get("title"):
            self._error_service.show_error(
                title="Missing Information",
                message="Please enter a title for your playlist."
            )
            return
        
        if not selected_tracks:
            self._error_service.show_error(
                title="No Tracks Selected",
                message="Please select at least one track for your playlist."
            )
            return
        
        # In a real implementation, this would actually create the playlist
        # For now, just show a success message
        logger.info(f"Creating playlist: {metadata.get('title')} with {len(selected_tracks)} tracks")
        
        # Show progress UI
        self.progress_group.setVisible(True)
        self.status_label.setText("Creating playlist...")
        
        # Simulate creation process - in real implementation, this would be async
        for i in range(101):
            self.progress_bar.setValue(i)
            # In a real app, you'd use QTimer or similar for smooth progress
            # Using a small delay would make it smoother
        
        self.status_label.setText(f"Playlist '{metadata.get('title')}' created successfully!")
        
        # After some time, we'd hide the progress again
        # In a real app, you'd use QTimer for this
        # self.progress_group.setVisible(False) 