"""
Multi-Playlist Management component for comparing and managing multiple Spotify playlists.
"""

import logging
from typing import Dict, List, Any, Optional
from functools import partial

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QListWidget, QListWidgetItem, 
    QTabWidget, QSplitter, QTreeWidget, QTreeWidgetItem, 
    QGroupBox, QGridLayout, QMenu, QCheckBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QPixmap

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService

logger = logging.getLogger(__name__)

class PlaylistCategoryManager(QWidget):
    """Widget for managing and categorizing playlists."""
    
    category_changed = Signal(str, str)  # playlist_id, category
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._categories = ["All", "Favorites", "Hidden Gems", "Mood", "Genre", "Custom"]
        self._playlists_by_category = {category: [] for category in self._categories}
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Category tree
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabel("Categories")
        self.category_tree.itemClicked.connect(self._on_category_selected)
        layout.addWidget(self.category_tree)
        
        # Populate categories
        self._populate_categories()
        
        # Category controls
        controls_layout = QHBoxLayout()
        self.add_category_button = QPushButton("Add Category")
        self.add_category_button.clicked.connect(self._on_add_category)
        self.rename_category_button = QPushButton("Rename")
        self.rename_category_button.clicked.connect(self._on_rename_category)
        self.remove_category_button = QPushButton("Remove")
        self.remove_category_button.clicked.connect(self._on_remove_category)
        
        controls_layout.addWidget(self.add_category_button)
        controls_layout.addWidget(self.rename_category_button)
        controls_layout.addWidget(self.remove_category_button)
        
        layout.addLayout(controls_layout)
    
    def _populate_categories(self):
        """Populate the category tree with initial categories."""
        self.category_tree.clear()
        
        for category in self._categories:
            item = QTreeWidgetItem([category])
            item.setData(0, Qt.ItemDataRole.UserRole, category)
            self.category_tree.addTopLevelItem(item)
            
            # Add child items for playlists in this category
            for playlist in self._playlists_by_category[category]:
                child = QTreeWidgetItem([playlist.get("name", "Unnamed")])
                child.setData(0, Qt.ItemDataRole.UserRole, playlist)
                item.addChild(child)
        
        # Expand the "All" category by default
        self.category_tree.topLevelItem(0).setExpanded(True)
    
    def add_playlist_to_category(self, playlist, category):
        """Add a playlist to a category."""
        if category in self._playlists_by_category:
            if playlist not in self._playlists_by_category[category]:
                self._playlists_by_category[category].append(playlist)
                
                # Always add to "All" category
                if category != "All" and playlist not in self._playlists_by_category["All"]:
                    self._playlists_by_category["All"].append(playlist)
                
                self._populate_categories()
    
    def remove_playlist_from_category(self, playlist, category):
        """Remove a playlist from a category."""
        if category in self._playlists_by_category and playlist in self._playlists_by_category[category]:
            self._playlists_by_category[category].remove(playlist)
            self._populate_categories()
    
    def set_playlists(self, playlists):
        """Set all playlists and categorize them."""
        # Reset categories
        self._playlists_by_category = {category: [] for category in self._categories}
        
        # Add all playlists to "All" category
        self._playlists_by_category["All"] = list(playlists)
        
        # Auto-categorize playlists based on their metadata
        for playlist in playlists:
            # Example: categorize by a "category" field if present
            category = playlist.get("category")
            if category and category in self._categories:
                self._playlists_by_category[category].append(playlist)
        
        self._populate_categories()
    
    def _on_category_selected(self, item, column):
        """Handle category or playlist selection."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, str):  # It's a category
            logger.debug(f"Category selected: {data}")
        else:  # It's a playlist
            logger.debug(f"Playlist selected: {data.get('name', 'Unnamed')}")
    
    def _on_add_category(self):
        """Add a new category."""
        # In a real implementation, this would show a dialog to enter a category name
        new_category = "New Category"
        if new_category not in self._categories:
            self._categories.append(new_category)
            self._playlists_by_category[new_category] = []
            self._populate_categories()
    
    def _on_rename_category(self):
        """Rename the selected category."""
        # In a real implementation, this would show a dialog
        item = self.category_tree.currentItem()
        if item and item.parent() is None:  # It's a top-level category
            category = item.data(0, Qt.ItemDataRole.UserRole)
            if category != "All":  # Don't allow renaming the "All" category
                # For now, just log that we would rename it
                logger.info(f"Would rename category: {category}")
    
    def _on_remove_category(self):
        """Remove the selected category."""
        item = self.category_tree.currentItem()
        if item and item.parent() is None:  # It's a top-level category
            category = item.data(0, Qt.ItemDataRole.UserRole)
            if category != "All":  # Don't allow removing the "All" category
                # Move playlists to "All" if not already there
                for playlist in self._playlists_by_category[category]:
                    if playlist not in self._playlists_by_category["All"]:
                        self._playlists_by_category["All"].append(playlist)
                
                # Remove the category
                self._categories.remove(category)
                del self._playlists_by_category[category]
                self._populate_categories()

class PlaylistComparisonView(QWidget):
    """Widget for comparing multiple playlists."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._playlists = []
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Comparison header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Playlist Comparison"))
        self.add_playlist_button = QPushButton("Add Playlist")
        self.add_playlist_button.clicked.connect(self._on_add_playlist)
        header_layout.addStretch()
        header_layout.addWidget(self.add_playlist_button)
        layout.addLayout(header_layout)
        
        # Comparison tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.South)
        
        # Overview tab
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        overview_layout.addWidget(QLabel("Playlists selected for comparison: 0"))
        self.comparison_label = QLabel("Select playlists to compare")
        overview_layout.addWidget(self.comparison_label)
        self.tabs.addTab(overview_tab, "Overview")
        
        # Tracks tab
        tracks_tab = QWidget()
        tracks_layout = QVBoxLayout(tracks_tab)
        tracks_layout.addWidget(QLabel("Track Comparison"))
        self.track_comparison = QTreeWidget()
        self.track_comparison.setHeaderLabels(["Track", "In Playlist 1", "In Playlist 2"])
        tracks_layout.addWidget(self.track_comparison)
        self.tabs.addTab(tracks_tab, "Tracks")
        
        # Artists tab
        artists_tab = QWidget()
        artists_layout = QVBoxLayout(artists_tab)
        artists_layout.addWidget(QLabel("Artist Comparison"))
        self.artist_comparison = QTreeWidget()
        self.artist_comparison.setHeaderLabels(["Artist", "In Playlist 1", "In Playlist 2"])
        artists_layout.addWidget(self.artist_comparison)
        self.tabs.addTab(artists_tab, "Artists")
        
        # Metrics tab
        metrics_tab = QWidget()
        metrics_layout = QGridLayout(metrics_tab)
        metrics_layout.addWidget(QLabel("Playlist 1 Size:"), 0, 0)
        metrics_layout.addWidget(QLabel("0 tracks"), 0, 1)
        metrics_layout.addWidget(QLabel("Playlist 2 Size:"), 1, 0)
        metrics_layout.addWidget(QLabel("0 tracks"), 1, 1)
        metrics_layout.addWidget(QLabel("Common Tracks:"), 2, 0)
        metrics_layout.addWidget(QLabel("0 tracks (0%)"), 2, 1)
        metrics_layout.addWidget(QLabel("Unique to Playlist 1:"), 3, 0)
        metrics_layout.addWidget(QLabel("0 tracks (0%)"), 3, 1)
        metrics_layout.addWidget(QLabel("Unique to Playlist 2:"), 4, 0)
        metrics_layout.addWidget(QLabel("0 tracks (0%)"), 4, 1)
        metrics_layout.addWidget(QLabel("Jaccard Similarity:"), 5, 0)
        metrics_layout.addWidget(QLabel("0.0"), 5, 1)
        metrics_layout.setRowStretch(6, 1)
        self.tabs.addTab(metrics_tab, "Metrics")
        
        layout.addWidget(self.tabs)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.merge_button = QPushButton("Merge Playlists")
        self.merge_button.clicked.connect(self._on_merge)
        self.export_button = QPushButton("Export Comparison")
        self.export_button.clicked.connect(self._on_export)
        
        action_layout.addWidget(self.merge_button)
        action_layout.addWidget(self.export_button)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
    
    def set_playlists(self, playlists):
        """Set playlists for comparison."""
        self._playlists = playlists
        if len(playlists) >= 2:
            self._update_comparison(playlists[0], playlists[1])
        elif len(playlists) == 1:
            self.comparison_label.setText(f"Selected: {playlists[0].get('name', 'Unnamed')}\nSelect one more playlist to compare.")
        else:
            self.comparison_label.setText("Select playlists to compare")
    
    def _update_comparison(self, playlist1, playlist2):
        """Update the comparison view with two playlists."""
        self.comparison_label.setText(f"Comparing:\n1. {playlist1.get('name', 'Unnamed')}\n2. {playlist2.get('name', 'Unnamed')}")
        
        # In a real implementation, we would perform the actual comparison
        # and update the track and artist lists, as well as the metrics
        
        # For now, just clear the lists
        self.track_comparison.clear()
        self.artist_comparison.clear()
    
    def _on_add_playlist(self):
        """Handle add playlist button click."""
        # In a real implementation, this would show a dialog to select a playlist
        logger.info("Add playlist for comparison requested")
    
    def _on_merge(self):
        """Handle merge button click."""
        # In a real implementation, this would merge the selected playlists
        logger.info("Merge playlists requested")
    
    def _on_export(self):
        """Handle export button click."""
        # In a real implementation, this would export the comparison
        logger.info("Export comparison requested")

class DuplicateTrackFinder(QWidget):
    """Widget for finding duplicate tracks across playlists."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._playlists = []
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Exact Match", "Similar Title", "Same Artist"])
        controls_layout.addWidget(QLabel("Search Type:"))
        controls_layout.addWidget(self.search_type_combo)
        
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["All Playlists", "Selected Playlists"])
        controls_layout.addWidget(QLabel("Scope:"))
        controls_layout.addWidget(self.scope_combo)
        
        self.find_button = QPushButton("Find Duplicates")
        self.find_button.clicked.connect(self._on_find_duplicates)
        controls_layout.addWidget(self.find_button)
        
        layout.addLayout(controls_layout)
        
        # Results
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Track", "Artist", "Playlists", "Action"])
        layout.addWidget(self.results_tree)
        
        # Actions
        actions_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self._on_select_all)
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self._on_deselect_all)
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self._on_remove_selected)
        self.keep_newest_button = QPushButton("Keep Newest")
        self.keep_newest_button.clicked.connect(self._on_keep_newest)
        
        actions_layout.addWidget(self.select_all_button)
        actions_layout.addWidget(self.deselect_all_button)
        actions_layout.addWidget(self.remove_button)
        actions_layout.addWidget(self.keep_newest_button)
        
        layout.addLayout(actions_layout)
    
    def set_playlists(self, playlists):
        """Set playlists to search for duplicates."""
        self._playlists = playlists
    
    def _on_find_duplicates(self):
        """Handle find duplicates button click."""
        search_type = self.search_type_combo.currentText()
        scope = self.scope_combo.currentText()
        
        # In a real implementation, this would actually find duplicates
        logger.info(f"Finding duplicates with type: {search_type}, scope: {scope}")
        
        # For now, just populate with some example data
        self.results_tree.clear()
        
        examples = [
            ["Track 1", "Artist A", "Playlist 1, Playlist 3"],
            ["Track 2", "Artist B", "Playlist 2, Playlist 4"],
            ["Track 3", "Artist C", "Playlist 1, Playlist 2, Playlist 3"]
        ]
        
        for example in examples:
            item = QTreeWidgetItem(example)
            checkbox = QCheckBox()
            self.results_tree.addTopLevelItem(item)
            self.results_tree.setItemWidget(item, 3, checkbox)
    
    def _on_select_all(self):
        """Select all duplicates."""
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            widget = self.results_tree.itemWidget(item, 3)
            if isinstance(widget, QCheckBox):
                widget.setChecked(True)
    
    def _on_deselect_all(self):
        """Deselect all duplicates."""
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            widget = self.results_tree.itemWidget(item, 3)
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)
    
    def _on_remove_selected(self):
        """Remove selected duplicates."""
        # In a real implementation, this would remove the selected duplicates
        count = 0
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            widget = self.results_tree.itemWidget(item, 3)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                count += 1
        
        logger.info(f"Would remove {count} duplicate tracks")
    
    def _on_keep_newest(self):
        """Keep only the newest version of each duplicate."""
        # In a real implementation, this would keep only the newest version
        logger.info("Would keep only the newest version of each duplicate")

class MultiPlaylistStatistics(QWidget):
    """Widget for displaying statistics across multiple playlists."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._playlists = []
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Overview statistics
        overview_group = QGroupBox("Collection Overview")
        overview_layout = QGridLayout()
        
        overview_layout.addWidget(QLabel("Total Playlists:"), 0, 0)
        self.total_playlists_label = QLabel("0")
        overview_layout.addWidget(self.total_playlists_label, 0, 1)
        
        overview_layout.addWidget(QLabel("Total Tracks:"), 0, 2)
        self.total_tracks_label = QLabel("0")
        overview_layout.addWidget(self.total_tracks_label, 0, 3)
        
        overview_layout.addWidget(QLabel("Unique Tracks:"), 1, 0)
        self.unique_tracks_label = QLabel("0")
        overview_layout.addWidget(self.unique_tracks_label, 1, 1)
        
        overview_layout.addWidget(QLabel("Unique Artists:"), 1, 2)
        self.unique_artists_label = QLabel("0")
        overview_layout.addWidget(self.unique_artists_label, 1, 3)
        
        overview_layout.addWidget(QLabel("Total Duration:"), 2, 0)
        self.duration_label = QLabel("0h 0m")
        overview_layout.addWidget(self.duration_label, 2, 1)
        
        overview_layout.addWidget(QLabel("Avg. Playlist Size:"), 2, 2)
        self.avg_size_label = QLabel("0 tracks")
        overview_layout.addWidget(self.avg_size_label, 2, 3)
        
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        # Top artists and tracks
        tops_layout = QHBoxLayout()
        
        # Top artists
        artists_group = QGroupBox("Top Artists")
        artists_layout = QVBoxLayout()
        self.artists_list = QListWidget()
        artists_layout.addWidget(self.artists_list)
        artists_group.setLayout(artists_layout)
        tops_layout.addWidget(artists_group)
        
        # Top tracks
        tracks_group = QGroupBox("Top Tracks")
        tracks_layout = QVBoxLayout()
        self.tracks_list = QListWidget()
        tracks_layout.addWidget(self.tracks_list)
        tracks_group.setLayout(tracks_layout)
        tops_layout.addWidget(tracks_group)
        
        layout.addLayout(tops_layout)
        
        # Distribution chart placeholder
        chart_group = QGroupBox("Distribution")
        chart_layout = QVBoxLayout()
        
        chart_type_layout = QHBoxLayout()
        chart_type_layout.addWidget(QLabel("Chart Type:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Genre", "Decade", "Popularity", "Energy/Danceability"])
        self.chart_type_combo.currentIndexChanged.connect(self._on_chart_type_changed)
        chart_type_layout.addWidget(self.chart_type_combo)
        chart_type_layout.addStretch()
        
        chart_layout.addLayout(chart_type_layout)
        
        # Chart placeholder
        self.chart_placeholder = QLabel("Chart will be displayed here")
        self.chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_placeholder.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd;")
        self.chart_placeholder.setMinimumHeight(200)
        chart_layout.addWidget(self.chart_placeholder)
        
        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)
    
    def set_playlists(self, playlists):
        """Set playlists for statistics."""
        self._playlists = playlists
        self._update_statistics()
    
    def _update_statistics(self):
        """Update statistics based on playlists."""
        # Update overview statistics
        self.total_playlists_label.setText(str(len(self._playlists)))
        
        total_tracks = sum(playlist.get("tracks_count", 0) for playlist in self._playlists)
        self.total_tracks_label.setText(str(total_tracks))
        
        # In a real implementation, we would calculate unique tracks and artists
        # For now, use placeholder values
        self.unique_tracks_label.setText(str(int(total_tracks * 0.8)))  # Estimate 80% unique
        self.unique_artists_label.setText(str(int(total_tracks * 0.3)))  # Estimate 30% unique artists
        
        # Calculate total duration (in a real implementation, we'd use actual track durations)
        # For now, use a placeholder
        hours = total_tracks * 3.5 // 60  # Assuming 3.5 minutes per track
        minutes = total_tracks * 3.5 % 60
        self.duration_label.setText(f"{hours:.0f}h {minutes:.0f}m")
        
        # Calculate average playlist size
        avg_size = total_tracks / len(self._playlists) if self._playlists else 0
        self.avg_size_label.setText(f"{avg_size:.1f} tracks")
        
        # Update top artists and tracks (in a real implementation, we'd calculate these)
        self.artists_list.clear()
        self.tracks_list.clear()
        
        # Example data
        artists = ["Artist A (10 tracks)", "Artist B (8 tracks)", "Artist C (5 tracks)"]
        for artist in artists:
            self.artists_list.addItem(artist)
        
        tracks = ["Track 1 - Artist A (4 playlists)", "Track 2 - Artist B (3 playlists)", "Track 3 - Artist C (2 playlists)"]
        for track in tracks:
            self.tracks_list.addItem(track)
    
    def _on_chart_type_changed(self, index):
        """Handle chart type change."""
        chart_type = self.chart_type_combo.currentText()
        # In a real implementation, this would update the chart
        logger.info(f"Chart type changed to: {chart_type}")

class MultiPlaylistManagement:
    """Component for managing and comparing multiple playlists."""
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the component.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        self._config_service = config_service
        self._error_service = error_service
        self._widget = self._create_widget()
        
        self._init_component()
        
        logger.info("Multi-Playlist Management component initialized")
    
    def _create_widget(self):
        """Create the main widget for this component."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Multi-Playlist Management")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        # Action buttons
        self.import_button = QPushButton("Import Playlists")
        self.import_button.clicked.connect(self._on_import_playlists)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._on_refresh)
        
        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # Main content with splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: playlist categories
        self.category_manager = PlaylistCategoryManager()
        self.splitter.addWidget(self.category_manager)
        
        # Right side: tabs for different views
        self.tabs = QTabWidget()
        
        # Comparison tab
        self.comparison_view = PlaylistComparisonView()
        self.tabs.addTab(self.comparison_view, "Compare")
        
        # Duplicates tab
        self.duplicate_finder = DuplicateTrackFinder()
        self.tabs.addTab(self.duplicate_finder, "Find Duplicates")
        
        # Statistics tab
        self.statistics_view = MultiPlaylistStatistics()
        self.tabs.addTab(self.statistics_view, "Statistics")
        
        # Version control tab (placeholder)
        version_tab = QWidget()
        version_layout = QVBoxLayout(version_tab)
        version_layout.addWidget(QLabel("Playlist version history will be shown here."))
        self.tabs.addTab(version_tab, "Version History")
        
        self.splitter.addWidget(self.tabs)
        
        # Set initial sizes
        self.splitter.setSizes([300, 700])
        
        main_layout.addWidget(self.splitter)
        
        return container
    
    def _init_component(self):
        """Initialize the component with data and set up connections."""
        # Set sample playlist data - in real implementation, this would come from elsewhere
        sample_playlists = []
        for i in range(1, 6):
            playlist = {
                "id": f"playlist{i}",
                "name": f"Sample Playlist {i}",
                "description": f"Description for playlist {i}",
                "is_public": i % 2 == 0,
                "owner": "User123",
                "followers": 10 * i,
                "tracks_count": 20 + i * 5,
                "category": ["Favorites", "Hidden Gems", "Mood", "Genre", "Custom"][i % 5],
                "date_created": "2023-01-01",
                "date_modified": "2023-05-01"
            }
            sample_playlists.append(playlist)
        
        self.set_playlists(sample_playlists)
    
    @property
    def widget(self):
        """Get the widget for this component."""
        return self._widget
    
    def set_playlists(self, playlists):
        """Set playlist data for management.
        
        Args:
            playlists: List of playlist dictionaries
        """
        # Set playlists for each sub-component
        self.category_manager.set_playlists(playlists)
        self.comparison_view.set_playlists(playlists[:2] if len(playlists) >= 2 else playlists)
        self.duplicate_finder.set_playlists(playlists)
        self.statistics_view.set_playlists(playlists)
    
    def _on_import_playlists(self):
        """Handle import playlists button click."""
        # In a real implementation, this would show a dialog to import playlists
        logger.info("Import playlists requested")
    
    def _on_refresh(self):
        """Handle refresh button click."""
        # In a real implementation, this would refresh playlist data
        logger.info("Refresh playlists requested") 