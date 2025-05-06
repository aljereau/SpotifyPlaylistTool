"""
Playlist Results View component for displaying playlist data and analysis results.
"""

import logging
from typing import List, Dict, Optional, Any
from functools import partial

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QTabWidget, QToolBar, QToolButton,
    QSplitter, QMenu, QFileDialog, QDialog,
    QGroupBox, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QPixmap, QImage, QAction, QAction, QAction

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService

logger = logging.getLogger(__name__)

class PlaylistMetadataView(QWidget):
    """Widget for displaying playlist metadata and cover art."""
    
    def __init__(self, parent=None):
        """Initialize the playlist metadata view.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # UI state
        self.playlist_data = {}
        self.cover_image = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Cover art frame
        self.cover_frame = QFrame()
        self.cover_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.cover_frame.setFixedSize(200, 200)
        
        # Cover art label
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("background-color: #f0f0f0;")
        
        cover_layout = QVBoxLayout(self.cover_frame)
        cover_layout.setContentsMargins(0, 0, 0, 0)
        cover_layout.addWidget(self.cover_label)
        
        main_layout.addWidget(self.cover_frame)
        
        # Metadata section
        metadata_layout = QVBoxLayout()
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("<b>Title:</b>"))
        self.title_label = QLabel("No playlist loaded")
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        metadata_layout.addLayout(title_layout)
        
        # Owner
        owner_layout = QHBoxLayout()
        owner_layout.addWidget(QLabel("<b>Owner:</b>"))
        self.owner_label = QLabel("")
        self.owner_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        owner_layout.addWidget(self.owner_label)
        owner_layout.addStretch()
        metadata_layout.addLayout(owner_layout)
        
        # Description
        metadata_layout.addWidget(QLabel("<b>Description:</b>"))
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        metadata_layout.addWidget(self.description_label)
        
        # Statistics group
        stats_group = QGroupBox("Statistics")
        stats_layout = QGridLayout()
        
        # Track count
        stats_layout.addWidget(QLabel("Tracks:"), 0, 0)
        self.tracks_label = QLabel("0")
        stats_layout.addWidget(self.tracks_label, 0, 1)
        
        # Duration
        stats_layout.addWidget(QLabel("Duration:"), 0, 2)
        self.duration_label = QLabel("00:00:00")
        stats_layout.addWidget(self.duration_label, 0, 3)
        
        # Followers
        stats_layout.addWidget(QLabel("Followers:"), 1, 0)
        self.followers_label = QLabel("0")
        stats_layout.addWidget(self.followers_label, 1, 1)
        
        # Average popularity
        stats_layout.addWidget(QLabel("Avg. Popularity:"), 1, 2)
        self.popularity_label = QLabel("0")
        stats_layout.addWidget(self.popularity_label, 1, 3)
        
        # Hidden gems count
        stats_layout.addWidget(QLabel("Hidden Gems:"), 2, 0)
        self.gems_label = QLabel("0")
        stats_layout.addWidget(self.gems_label, 2, 1)
        
        # Analysis date
        stats_layout.addWidget(QLabel("Analyzed:"), 2, 2)
        self.analysis_date_label = QLabel("Never")
        stats_layout.addWidget(self.analysis_date_label, 2, 3)
        
        stats_group.setLayout(stats_layout)
        metadata_layout.addWidget(stats_group)
        
        # Add stretch to push everything to the top
        metadata_layout.addStretch()
        
        main_layout.addLayout(metadata_layout, 1)  # Give metadata section more space
    
    def set_playlist_data(self, data: Dict[str, Any]):
        """Set the playlist data to display.
        
        Args:
            data: Dictionary containing playlist metadata
        """
        self.playlist_data = data
        
        # Update UI with playlist data
        self.title_label.setText(data.get('name', 'Unnamed Playlist'))
        self.owner_label.setText(data.get('owner', {}).get('display_name', 'Unknown'))
        self.description_label.setText(data.get('description', ''))
        
        # Statistics
        tracks = data.get('tracks', {}).get('items', [])
        self.tracks_label.setText(str(len(tracks)))
        
        # Calculate total duration
        total_ms = sum(track.get('track', {}).get('duration_ms', 0) for track in tracks)
        total_seconds = total_ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        self.duration_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Other stats
        self.followers_label.setText(str(data.get('followers', {}).get('total', 0)))
        
        # Calculate average popularity
        popularities = [
            track.get('track', {}).get('popularity', 0) 
            for track in tracks 
            if 'track' in track and track['track'] is not None
        ]
        avg_popularity = sum(popularities) / len(popularities) if popularities else 0
        self.popularity_label.setText(f"{avg_popularity:.1f}")
        
        # Hidden gems count - this will be set separately
        
        # Analysis date
        self.analysis_date_label.setText(data.get('analysis_date', 'Never'))
        
        # Load cover image if available
        if 'images' in data and data['images'] and len(data['images']) > 0:
            image_url = data['images'][0]['url']
            # In a real implementation, you would download the image
            # For now, just log that we would load it
            logger.info(f"Would load cover image from: {image_url}")
    
    def set_cover_image(self, pixmap: QPixmap):
        """Set the cover art image.
        
        Args:
            pixmap: Image pixmap to display
        """
        self.cover_image = pixmap
        scaled_pixmap = pixmap.scaled(
            self.cover_frame.size(), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.cover_label.setPixmap(scaled_pixmap)
    
    def set_hidden_gems_count(self, count: int):
        """Set the count of hidden gems.
        
        Args:
            count: Number of hidden gems found
        """
        self.gems_label.setText(str(count))

class PlaylistResultsContainer(QTabWidget):
    """Container widget for multiple playlist results."""
    
    playlist_selected = Signal(str)  # Emits playlist ID when selected
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the playlist results container.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        super().__init__()
        
        self.config_service = config_service
        self.error_service = error_service
        
        # Playlist data storage
        self.playlists = {}  # Dictionary of playlist ID -> data
        
        self._init_ui()
        
        logger.info("Playlist results container initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Configure tab widget
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.currentChanged.connect(self._on_tab_changed)
        
        # Add "+" tab for adding new playlists
        self.addTab(QWidget(), "+")
        self.tabBar().setTabButton(0, self.tabBar().ButtonPosition.RightSide, None)
    
    def add_playlist(self, playlist_id: str, playlist_data: Dict[str, Any]):
        """Add a new playlist tab.
        
        Args:
            playlist_id: Unique identifier for the playlist
            playlist_data: Dictionary containing playlist metadata and tracks
        """
        if playlist_id in self.playlists:
            # Playlist already exists, just select its tab
            for i in range(self.count()):
                if self.tabText(i) == playlist_data.get('name', 'Unnamed'):
                    self.setCurrentIndex(i)
                    return
        
        # Store playlist data
        self.playlists[playlist_id] = playlist_data
        
        # Create results view
        results_view = PlaylistResultsView(self.config_service, self.error_service, playlist_id)
        results_view.set_playlist_data(playlist_data)
        
        # Add new tab before the "+" tab
        tab_index = self.count() - 1
        self.insertTab(tab_index, results_view, playlist_data.get('name', 'Unnamed'))
        self.setCurrentIndex(tab_index)
        
        # Emit signal
        self.playlist_selected.emit(playlist_id)
        
        logger.info(f"Added playlist results tab: {playlist_data.get('name', 'Unnamed')}")
    
    def get_current_playlist_id(self) -> Optional[str]:
        """Get the ID of the currently selected playlist.
        
        Returns:
            Current playlist ID or None if no playlist is selected
        """
        current_widget = self.currentWidget()
        if isinstance(current_widget, PlaylistResultsView):
            return current_widget.playlist_id
        return None
    
    def save_current_snapshot(self) -> bool:
        """Save a snapshot of the current playlist.
        
        Returns:
            True if successful, False otherwise
        """
        current_widget = self.currentWidget()
        if isinstance(current_widget, PlaylistResultsView):
            return current_widget.save_snapshot()
        return False
    
    @Slot(int)
    def _on_tab_close_requested(self, index: int):
        """Handle tab close button click.
        
        Args:
            index: Tab index to close
        """
        # Don't close the "+" tab
        if index == self.count() - 1:
            return
        
        # Get playlist ID
        widget = self.widget(index)
        if isinstance(widget, PlaylistResultsView):
            playlist_id = widget.playlist_id
            if playlist_id in self.playlists:
                del self.playlists[playlist_id]
        
        # Remove tab
        self.removeTab(index)
        
        # Select another tab if available
        if self.count() > 1:
            self.setCurrentIndex(max(0, index - 1))
            
            # Emit signal for newly selected tab
            current_widget = self.currentWidget()
            if isinstance(current_widget, PlaylistResultsView):
                self.playlist_selected.emit(current_widget.playlist_id)
    
    @Slot(int)
    def _on_tab_changed(self, index: int):
        """Handle tab change.
        
        Args:
            index: New tab index
        """
        # Check if the "+" tab was selected
        if index == self.count() - 1:
            # Create a new empty tab
            # In a real implementation, this would show a dialog to select a playlist
            logger.info("New playlist tab requested")
            
            # Go back to the previous tab
            self.setCurrentIndex(max(0, index - 1))
        else:
            # Emit signal for selected playlist
            current_widget = self.currentWidget()
            if isinstance(current_widget, PlaylistResultsView):
                self.playlist_selected.emit(current_widget.playlist_id)

class PlaylistResultsView(QWidget):
    """Widget for displaying detailed playlist results."""
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService, playlist_id: str):
        """Initialize the playlist results view.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
            playlist_id: ID of the playlist being displayed
        """
        super().__init__()
        
        self.config_service = config_service
        self.error_service = error_service
        self.playlist_id = playlist_id
        
        # Data
        self.playlist_data = {}
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # Snapshot action
        self.snapshot_action = QAction("Save Snapshot", self)
        self.snapshot_action.triggered.connect(self._on_snapshot)
        toolbar.addAction(self.snapshot_action)
        
        # Share action
        self.share_action = QAction("Share", self)
        self.share_action.triggered.connect(self._on_share)
        toolbar.addAction(self.share_action)
        
        # Compare action
        self.compare_action = QAction("Compare", self)
        self.compare_action.triggered.connect(self._on_compare)
        toolbar.addAction(self.compare_action)
        
        # Refresh action
        self.refresh_action = QAction("Refresh", self)
        self.refresh_action.triggered.connect(self._on_refresh)
        toolbar.addAction(self.refresh_action)
        
        # Add to toolbar
        main_layout.addWidget(toolbar)
        
        # Metadata widget
        self.metadata_view = PlaylistMetadataView()
        main_layout.addWidget(self.metadata_view)
        
        # Content splitter (will hold track listing and details)
        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Placeholder widgets - these will be replaced with actual components
        # when they are implemented
        track_list_placeholder = QLabel("Track listing will appear here")
        track_list_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        track_list_placeholder.setStyleSheet("background-color: #f5f5f5;")
        track_list_placeholder.setMinimumHeight(200)
        
        details_placeholder = QLabel("Track details will appear here")
        details_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_placeholder.setStyleSheet("background-color: #e9e9e9;")
        details_placeholder.setMinimumHeight(150)
        
        self.content_splitter.addWidget(track_list_placeholder)
        self.content_splitter.addWidget(details_placeholder)
        
        main_layout.addWidget(self.content_splitter, 1)  # Give it stretch
    
    def set_playlist_data(self, data: Dict[str, Any]):
        """Set the playlist data to display.
        
        Args:
            data: Dictionary containing playlist metadata and tracks
        """
        self.playlist_data = data
        
        # Update metadata view
        self.metadata_view.set_playlist_data(data)
        
        # In a real implementation, we would load the playlist cover image
        # For now, use a placeholder image
        # pixmap = QPixmap(200, 200)
        # pixmap.fill(Qt.GlobalColor.gray)
        # self.metadata_view.set_cover_image(pixmap)
        
        # Calculate and set hidden gems count
        hidden_gems_count = data.get('hidden_gems_count', 0)
        self.metadata_view.set_hidden_gems_count(hidden_gems_count)
        
        logger.info(f"Loaded playlist data: {data.get('name', 'Unnamed')}")
    
    def save_snapshot(self) -> bool:
        """Save a snapshot of the current playlist state.
        
        Returns:
            True if successful, False otherwise
        """
        # In a real implementation, this would save the current state to a file
        # For now, just simulate success
        logger.info(f"Saving snapshot of playlist: {self.playlist_data.get('name', 'Unnamed')}")
        return True
    
    @Slot()
    def _on_snapshot(self):
        """Handle snapshot button click."""
        success = self.save_snapshot()
        if success:
            self.error_service.show_info(
                title="Snapshot Saved",
                message=f"Playlist snapshot saved successfully."
            )
        else:
            self.error_service.show_error(
                title="Snapshot Error",
                message="Failed to save playlist snapshot."
            )
    
    @Slot()
    def _on_share(self):
        """Handle share button click."""
        # In a real implementation, this would show share options
        self.error_service.show_info(
            title="Share Playlist",
            message="Sharing functionality will be implemented in a future update."
        )
    
    @Slot()
    def _on_compare(self):
        """Handle compare button click."""
        # In a real implementation, this would show comparison options
        self.error_service.show_info(
            title="Compare Playlists",
            message="Playlist comparison will be implemented in a future update."
        )
    
    @Slot()
    def _on_refresh(self):
        """Handle refresh button click."""
        # In a real implementation, this would reload the playlist data
        self.error_service.show_info(
            title="Refresh Playlist",
            message="Playlist refresh functionality will be implemented in a future update."
        )

class PlaylistResultsView:
    """Main component for displaying playlist results and analysis."""
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the playlist results view.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        self.config_service = config_service
        self.error_service = error_service
        self.container = PlaylistResultsContainer(config_service, error_service)
        
        logger.info("Playlist results view initialized")
    
    @property
    def widget(self) -> QWidget:
        """Get the main widget.
        
        Returns:
            The playlist results container widget
        """
        return self.container
    
    def load_playlist(self, playlist_id: str, playlist_data: Dict[str, Any]):
        """Load a playlist into the results view.
        
        Args:
            playlist_id: Unique identifier for the playlist
            playlist_data: Dictionary containing playlist metadata and tracks
        """
        self.container.add_playlist(playlist_id, playlist_data)
    
    def get_current_playlist_id(self) -> Optional[str]:
        """Get the ID of the currently displayed playlist.
        
        Returns:
            Current playlist ID or None if no playlist is displayed
        """
        return self.container.get_current_playlist_id() 