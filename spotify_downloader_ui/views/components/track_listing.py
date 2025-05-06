"""
Track Listing component for displaying and interacting with track data.
"""

import logging
from typing import List, Dict, Optional, Any, Callable
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableView, QAbstractItemView, QHeaderView, QMenu,
    QDialog, QFrame, QSplitter, QToolBar,
    QCheckBox, QComboBox, QSizePolicy, QStyledItemDelegate,
    QStyle, QApplication
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QSize, QAbstractTableModel, 
    QModelIndex, QSortFilterProxyModel, QRect
)
from PySide6.QtGui import (
    QIcon, QPixmap, QImage, QPainter, QColor, QPen, 
    QBrush, QFont, QFontMetrics, QPalette, QAction
)

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService

logger = logging.getLogger(__name__)

class TrackTableModel(QAbstractTableModel):
    """Model for track data in a table view."""
    
    # Column definitions
    COLUMNS = [
        {"name": "#", "key": "index", "width": 40},
        {"name": "Title", "key": "name", "width": 250},
        {"name": "Artist", "key": "artists", "width": 200},
        {"name": "Album", "key": "album", "width": 200},
        {"name": "Duration", "key": "duration_ms", "width": 80},
        {"name": "Popularity", "key": "popularity", "width": 80},
        {"name": "Gem Score", "key": "gem_score", "width": 80},
        {"name": "Added", "key": "added_at", "width": 120},
    ]
    
    def __init__(self, parent=None):
        """Initialize the track table model.
        
        Args:
            parent: Parent object
        """
        super().__init__(parent)
        self.tracks = []
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """Get number of rows.
        
        Args:
            parent: Parent index
            
        Returns:
            Number of rows
        """
        return len(self.tracks)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        """Get number of columns.
        
        Args:
            parent: Parent index
            
        Returns:
            Number of columns
        """
        return len(self.COLUMNS)
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """Get data for a specific index and role.
        
        Args:
            index: Model index
            role: Data role
            
        Returns:
            Data value
        """
        if not index.isValid() or index.row() >= len(self.tracks):
            return None
        
        track = self.tracks[index.row()]
        column = self.COLUMNS[index.column()]
        key = column["key"]
        
        # Display role - the visible text
        if role == Qt.ItemDataRole.DisplayRole:
            if key == "index":
                return index.row() + 1
            elif key == "name":
                return track.get("name", "")
            elif key == "artists":
                artists = track.get("artists", [])
                return ", ".join(artist.get("name", "") for artist in artists)
            elif key == "album":
                album = track.get("album", {})
                return album.get("name", "")
            elif key == "duration_ms":
                duration_ms = track.get("duration_ms", 0)
                minutes = duration_ms // 60000
                seconds = (duration_ms % 60000) // 1000
                return f"{minutes}:{seconds:02d}"
            elif key == "popularity":
                return track.get("popularity", 0)
            elif key == "gem_score":
                return track.get("gem_score", 0)
            elif key == "added_at":
                added_at = track.get("added_at", "")
                # In a real implementation, format the date properly
                return added_at[:10] if added_at else ""
        
        # Text alignment
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if key in ["index", "duration_ms", "popularity", "gem_score"]:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        
        # For editing, sorting, etc.
        elif role == Qt.ItemDataRole.UserRole:
            if key == "index":
                return index.row()
            else:
                # Return raw data for sorting
                return track.get(key, "")
                
        # Background color role
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Alternate row colors
            if index.row() % 2 == 0:
                return QApplication.palette().base()
            else:
                return QApplication.palette().alternateBase()
                
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        """Get header data.
        
        Args:
            section: Header section
            orientation: Header orientation
            role: Data role
            
        Returns:
            Header data
        """
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]["name"]
        elif orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return section + 1
            
        return None
    
    def setTracks(self, tracks: List[Dict[str, Any]]):
        """Set the track data.
        
        Args:
            tracks: List of track data dictionaries
        """
        self.beginResetModel()
        self.tracks = tracks
        self.endResetModel()

class TrackScoreDelegate(QStyledItemDelegate):
    """Delegate for rendering track scores with visual indicators."""
    
    def __init__(self, parent=None):
        """Initialize the track score delegate.
        
        Args:
            parent: Parent object
        """
        super().__init__(parent)
    
    def paint(self, painter: QPainter, option: QStyle.StateFlag, index: QModelIndex):
        """Paint the delegate.
        
        Args:
            painter: Painter
            option: Style options
            index: Model index
        """
        # Get score value
        value = index.data(Qt.ItemDataRole.DisplayRole)
        if not isinstance(value, (int, float)):
            super().paint(painter, option, index)
            return
        
        score = int(value)
        
        # Draw background
        painter.save()
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, index.data(Qt.ItemDataRole.BackgroundRole))
        
        # Draw score bar
        if score > 0:
            bar_width = int((option.rect.width() - 4) * score / 100)
            bar_height = option.rect.height() - 8
            bar_rect = QRect(
                option.rect.position().position().x() + 2,
                option.rect.position().position().y() + 4,
                bar_width,
                bar_height
            )
            
            # Color based on score
            if score >= 80:
                color = QColor(46, 204, 113)  # Green for high scores
            elif score >= 60:
                color = QColor(241, 196, 15)  # Yellow for medium scores
            else:
                color = QColor(231, 76, 60)  # Red for low scores
            
            painter.fillRect(bar_rect, color)
        
        # Draw text
        text_rect = option.rect.adjusted(2, 0, -2, 0)
        text_align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())
        
        painter.drawText(text_rect, text_align, f"{score}")
        
        painter.restore()

class TrackDetailPanel(QWidget):
    """Panel for displaying detailed information about a selected track."""
    
    play_preview = Signal(str)  # Emits preview URL when play button clicked
    
    def __init__(self, parent=None):
        """Initialize the track detail panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Data
        self.current_track = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Track title and artists
        title_layout = QVBoxLayout()
        
        self.title_label = QLabel("No track selected")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(self.title_label)
        
        self.artist_label = QLabel("")
        self.artist_label.setStyleSheet("font-size: 14px;")
        title_layout.addWidget(self.artist_label)
        
        main_layout.addLayout(title_layout)
        
        # Album art and metadata
        content_layout = QHBoxLayout()
        
        # Album art
        self.cover_frame = QFrame()
        self.cover_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.cover_frame.setFixedSize(150, 150)
        
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("background-color: #f0f0f0;")
        
        cover_layout = QVBoxLayout(self.cover_frame)
        cover_layout.setContentsMargins(0, 0, 0, 0)
        cover_layout.addWidget(self.cover_label)
        
        content_layout.addWidget(self.cover_frame)
        
        # Metadata
        metadata_layout = QVBoxLayout()
        
        # Album
        album_layout = QHBoxLayout()
        album_layout.addWidget(QLabel("<b>Album:</b>"))
        self.album_label = QLabel("")
        album_layout.addWidget(self.album_label, 1)
        metadata_layout.addLayout(album_layout)
        
        # Release date
        release_layout = QHBoxLayout()
        release_layout.addWidget(QLabel("<b>Released:</b>"))
        self.release_label = QLabel("")
        release_layout.addWidget(self.release_label, 1)
        metadata_layout.addLayout(release_layout)
        
        # Duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("<b>Duration:</b>"))
        self.duration_label = QLabel("")
        duration_layout.addWidget(self.duration_label, 1)
        metadata_layout.addLayout(duration_layout)
        
        # Popularity
        popularity_layout = QHBoxLayout()
        popularity_layout.addWidget(QLabel("<b>Popularity:</b>"))
        self.popularity_label = QLabel("")
        popularity_layout.addWidget(self.popularity_label, 1)
        metadata_layout.addLayout(popularity_layout)
        
        # Gem score
        gem_layout = QHBoxLayout()
        gem_layout.addWidget(QLabel("<b>Gem Score:</b>"))
        self.gem_label = QLabel("")
        gem_layout.addWidget(self.gem_label, 1)
        metadata_layout.addLayout(gem_layout)
        
        # Preview button
        self.preview_button = QPushButton("Play Preview")
        self.preview_button.clicked.connect(self._on_preview_clicked)
        self.preview_button.setEnabled(False)
        metadata_layout.addWidget(self.preview_button)
        
        # Add stretch to push everything to the top
        metadata_layout.addStretch()
        
        content_layout.addLayout(metadata_layout, 1)
        main_layout.addLayout(content_layout)
        
        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        
        # Audio features section
        features_layout = QHBoxLayout()
        features_layout.addWidget(QLabel("<b>Audio Features:</b>"))
        
        # Features will be displayed as a horizontal bar chart
        # This is a placeholder - will be implemented in a real app
        features_frame = QFrame()
        features_frame.setFrameShape(QFrame.Shape.StyledPanel)
        features_frame.setMinimumHeight(80)
        features_layout.addWidget(features_frame, 1)
        
        main_layout.addLayout(features_layout)
        
        # Spacer at the bottom
        main_layout.addStretch(1)
    
    def set_track(self, track_data: Dict[str, Any]):
        """Set the track to display.
        
        Args:
            track_data: Track data dictionary
        """
        if not track_data:
            self.clear()
            return
            
        self.current_track = track_data
        
        # Update basic info
        self.title_label.setText(track_data.get("name", "Unknown Track"))
        
        # Artists
        artists = track_data.get("artists", [])
        artist_names = [artist.get("name", "") for artist in artists]
        self.artist_label.setText(", ".join(artist_names))
        
        # Album
        album = track_data.get("album", {})
        self.album_label.setText(album.get("name", ""))
        
        # Release date
        self.release_label.setText(album.get("release_date", ""))
        
        # Duration
        duration_ms = track_data.get("duration_ms", 0)
        minutes = duration_ms // 60000
        seconds = (duration_ms % 60000) // 1000
        self.duration_label.setText(f"{minutes}:{seconds:02d}")
        
        # Popularity
        self.popularity_label.setText(str(track_data.get("popularity", 0)))
        
        # Gem score
        self.gem_label.setText(str(track_data.get("gem_score", 0)))
        
        # Preview
        preview_url = track_data.get("preview_url", "")
        self.preview_button.setEnabled(bool(preview_url))
        
        # In a real implementation, load the album artwork
        # For now, just log that we would load it
        if album.get("images") and len(album["images"]) > 0:
            image_url = album["images"][0]["url"]
            logger.info(f"Would load album image from: {image_url}")
        
        logger.info(f"Track details updated: {track_data.get('name', 'Unknown')}")
    
    def clear(self):
        """Clear the track details."""
        self.current_track = None
        
        self.title_label.setText("No track selected")
        self.artist_label.setText("")
        self.album_label.setText("")
        self.release_label.setText("")
        self.duration_label.setText("")
        self.popularity_label.setText("")
        self.gem_label.setText("")
        self.preview_button.setEnabled(False)
        
        # Clear album art
        self.cover_label.clear()
    
    @Slot()
    def _on_preview_clicked(self):
        """Handle preview button click."""
        if self.current_track and "preview_url" in self.current_track:
            preview_url = self.current_track["preview_url"]
            if preview_url:
                self.play_preview.emit(preview_url)
                logger.info(f"Playing preview: {preview_url}")
            else:
                logger.warning("No preview URL available")

class TrackListing:
    """Main component for displaying and interacting with track listings."""
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the track listing component.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        self.config_service = config_service
        self.error_service = error_service
        
        # Create main container widget
        self.container = QSplitter(Qt.Orientation.Vertical)
        
        # Create model and views
        self._init_components()
        
        logger.info("Track listing initialized")
    
    def _init_components(self):
        """Initialize the component parts."""
        # Track table view
        self.table_widget = QWidget()
        table_layout = QVBoxLayout(self.table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # Actions
        self.select_all_action = QAction("Select All", self.table_widget)
        self.select_all_action.triggered.connect(self._on_select_all)
        toolbar.addAction(self.select_all_action)
        
        self.select_none_action = QAction("Select None", self.table_widget)
        self.select_none_action.triggered.connect(self._on_select_none)
        toolbar.addAction(self.select_none_action)
        
        toolbar.addSeparator()
        
        self.group_by_label = QLabel("Group by:")
        toolbar.addWidget(self.group_by_label)
        
        self.group_combo = QComboBox()
        self.group_combo.addItem("None", "")
        self.group_combo.addItem("Artist", "artists")
        self.group_combo.addItem("Album", "album")
        self.group_combo.addItem("Year", "year")
        self.group_combo.addItem("Gem Category", "gem_category")
        self.group_combo.currentIndexChanged.connect(self._on_group_changed)
        toolbar.addWidget(self.group_combo)
        
        table_layout.addWidget(toolbar)
        
        # Table view
        self.track_model = TrackTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.track_model)
        
        self.track_table = QTableView()
        self.track_table.setModel(self.proxy_model)
        self.track_table.setSortingEnabled(True)
        self.track_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.track_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.track_table.setAlternatingRowColors(True)
        self.track_table.verticalHeader().setVisible(False)
        self.track_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.track_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.track_table.customContextMenuRequested.connect(self._on_context_menu)
        self.track_table.clicked.connect(self._on_track_selected)
        
        # Set column widths
        for i, col in enumerate(TrackTableModel.COLUMNS):
            self.track_table.setColumnWidth(i, col["width"])
        
        # Set delegates for custom rendering
        self.track_table.setItemDelegateForColumn(6, TrackScoreDelegate())  # Gem score column
        
        table_layout.addWidget(self.track_table)
        
        # Detail panel
        self.detail_panel = TrackDetailPanel()
        self.detail_panel.play_preview.connect(self._on_play_preview)
        
        # Add to splitter
        self.container.addWidget(self.table_widget)
        self.container.addWidget(self.detail_panel)
        self.container.setStretchFactor(0, 3)  # Give table more space
        self.container.setStretchFactor(1, 1)
    
    @property
    def widget(self) -> QWidget:
        """Get the main widget.
        
        Returns:
            The track listing widget
        """
        return self.container
    
    def set_tracks(self, tracks: List[Dict[str, Any]]):
        """Set track data for display.
        
        Args:
            tracks: List of track dictionaries
        """
        # Add gem scores if they don't exist
        for track in tracks:
            if "gem_score" not in track:
                # In a real implementation, this would be calculated or loaded
                # For now, use a placeholder value
                track["gem_score"] = track.get("popularity", 50)
        
        # Update model
        self.track_model.setTracks(tracks)
        
        # Clear detail panel
        self.detail_panel.clear()
        
        # Resize columns to content
        self.track_table.resizeColumnsToContents()
        
        logger.info(f"Track listing updated with {len(tracks)} tracks")
    
    def get_selected_tracks(self) -> List[Dict[str, Any]]:
        """Get the currently selected tracks.
        
        Returns:
            List of selected track dictionaries
        """
        selected_rows = self.track_table.selectionModel().selectedRows()
        selected_tracks = []
        
        for index in selected_rows:
            source_index = self.proxy_model.mapToSource(index)
            row = source_index.row()
            if 0 <= row < len(self.track_model.tracks):
                selected_tracks.append(self.track_model.tracks[row])
        
        return selected_tracks
    
    @Slot(QModelIndex)
    def _on_track_selected(self, index: QModelIndex):
        """Handle track selection.
        
        Args:
            index: Selected model index
        """
        source_index = self.proxy_model.mapToSource(index)
        row = source_index.row()
        
        if 0 <= row < len(self.track_model.tracks):
            track = self.track_model.tracks[row]
            self.detail_panel.set_track(track)
    
    @Slot(QModelIndex)
    def _on_context_menu(self, position):
        """Show context menu for track.
        
        Args:
            position: Menu position
        """
        # Get selected tracks
        selected = self.get_selected_tracks()
        if not selected:
            return
        
        # Create context menu
        menu = QMenu()
        
        # Add actions
        play_action = menu.addAction("Play")
        add_to_playlist_action = menu.addAction("Add to Playlist")
        export_action = menu.addAction("Export Selected")
        
        # Show menu and get selected action
        action = menu.exec(self.track_table.viewport().mapToGlobal(position))
        
        # Handle action
        if action == play_action:
            # In a real implementation, this would play the tracks
            logger.info(f"Play requested for {len(selected)} tracks")
        elif action == add_to_playlist_action:
            # In a real implementation, this would show a dialog to choose a playlist
            logger.info(f"Add to playlist requested for {len(selected)} tracks")
        elif action == export_action:
            # In a real implementation, this would export the selected tracks
            logger.info(f"Export requested for {len(selected)} tracks")
    
    @Slot()
    def _on_select_all(self):
        """Select all tracks."""
        self.track_table.selectAll()
    
    @Slot()
    def _on_select_none(self):
        """Deselect all tracks."""
        self.track_table.clearSelection()
    
    @Slot(int)
    def _on_group_changed(self, index: int):
        """Handle grouping option change.
        
        Args:
            index: Selected index
        """
        group_by = self.group_combo.currentData()
        
        # In a real implementation, this would update the view to group tracks
        logger.info(f"Group by changed to: {group_by}")
    
    @Slot(str)
    def _on_play_preview(self, preview_url: str):
        """Handle preview playback request.
        
        Args:
            preview_url: URL to preview audio
        """
        # In a real implementation, this would play the audio
        # For now, just log it
        logger.info(f"Play preview requested: {preview_url}")