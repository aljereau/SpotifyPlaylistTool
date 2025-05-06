"""
Results view for displaying playlist processing results.
"""

import logging
import os
import subprocess
from typing import Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QSplitter,
    QCheckBox, QComboBox, QFormLayout, QFileDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Slot, QUrl
from PySide6.QtGui import QDesktopServices, QColor

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService
from spotify_downloader_ui.services.playlist_service import PlaylistService
from spotify_downloader_ui.services.spotify_service import SpotifyService
from spotify_downloader_ui.views.download_view import DownloadView

logger = logging.getLogger(__name__)

class ResultsView(QWidget):
    """Widget for displaying playlist processing results."""
    
    def __init__(self, playlist_service: PlaylistService, spotify_service: SpotifyService,
                config_service: ConfigService, error_service: ErrorService):
        """Initialize the results view.
        
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
        
        # Store current results
        self.playlist_id = ""
        self.metadata = {}
        self.tracks = []
        self.output_dir = ""
        
        self._init_ui()
        self._connect_signals()
        
        logger.info("Results view initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header section
        header_layout = QVBoxLayout()
        
        # Title
        self.title_label = QLabel("Processing Results")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("title_label")
        header_layout.addWidget(self.title_label)
        
        # Playlist info
        self.playlist_info_label = QLabel("No playlist loaded")
        self.playlist_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.playlist_info_label)
        
        main_layout.addLayout(header_layout)
        
        # Tabs container
        self.tabs = QTabWidget()
        
        # 1. All Tracks tab
        self.all_tracks_tab = QWidget()
        all_tracks_layout = QVBoxLayout(self.all_tracks_tab)
        
        # Table for tracks
        self.tracks_table = QTableWidget()
        self.tracks_table.setColumnCount(7)
        self.tracks_table.setHorizontalHeaderLabels([
            "Track Name", "Artists", "Album", "Duration", "Popularity", "Explicit", "Link"
        ])
        
        # Set column widths
        header = self.tracks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Track name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Artists
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Album
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Duration
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Popularity
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Explicit
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Link
        
        all_tracks_layout.addWidget(self.tracks_table)
        
        # 2. Hidden Gems tab
        self.hidden_gems_tab = QWidget()
        hidden_gems_layout = QVBoxLayout(self.hidden_gems_tab)
        
        # Gems filter controls
        filter_group = QGroupBox("Hidden Gems Filter")
        filter_layout = QHBoxLayout(filter_group)
        
        form_layout = QFormLayout()
        self.min_popularity = QComboBox()
        for i in range(0, 45, 5):
            self.min_popularity.addItem(str(i), i)
        self.min_popularity.setCurrentIndex(1)  # Default to 5
        
        self.max_popularity = QComboBox()
        for i in range(20, 65, 5):
            self.max_popularity.addItem(str(i), i)
        self.max_popularity.setCurrentIndex(4)  # Default to 40
        
        self.min_score = QComboBox()
        for i in range(0, 55, 5):
            self.min_score.addItem(str(i), i)
        self.min_score.setCurrentIndex(4)  # Default to 20
        
        form_layout.addRow("Min Popularity:", self.min_popularity)
        form_layout.addRow("Max Popularity:", self.max_popularity)
        form_layout.addRow("Min Score:", self.min_score)
        
        filter_layout.addLayout(form_layout)
        
        # Add apply button
        self.apply_filter_button = QPushButton("Apply Filter")
        filter_layout.addWidget(self.apply_filter_button)
        
        hidden_gems_layout.addWidget(filter_group)
        
        # Hidden gems table
        self.gems_table = QTableWidget()
        self.gems_table.setColumnCount(8)
        self.gems_table.setHorizontalHeaderLabels([
            "Track Name", "Artists", "Album", "Popularity", "Score", "Duration", "Explicit", "Link"
        ])
        
        # Set column widths
        header = self.gems_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Track name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Artists
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Album
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Popularity
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Score
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Duration
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Explicit
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Link
        
        hidden_gems_layout.addWidget(self.gems_table)
        
        # 3. Analytics tab
        self.analytics_tab = QWidget()
        analytics_layout = QVBoxLayout(self.analytics_tab)
        
        # Summary statistics
        summary_group = QGroupBox("Playlist Summary")
        summary_layout = QFormLayout(summary_group)
        
        self.track_count_label = QLabel("0")
        self.avg_popularity_label = QLabel("0")
        self.explicit_count_label = QLabel("0")
        self.total_duration_label = QLabel("0:00")
        
        summary_layout.addRow("Total Tracks:", self.track_count_label)
        summary_layout.addRow("Average Popularity:", self.avg_popularity_label)
        summary_layout.addRow("Explicit Tracks:", self.explicit_count_label)
        summary_layout.addRow("Total Duration:", self.total_duration_label)
        
        analytics_layout.addWidget(summary_group)
        
        # Genre/Artist distribution could be added here
        # This would be expanded in a future enhancement
        
        analytics_layout.addWidget(QLabel("More detailed analytics to be added in future versions"))
        analytics_layout.addStretch(1)

        # 4. Download tab (new)
        self.download_tab = DownloadView(
            self.playlist_service,
            self.config_service,
            self.error_service
        )
        
        # Add all tabs
        self.tabs.addTab(self.all_tracks_tab, "All Tracks")
        self.tabs.addTab(self.hidden_gems_tab, "Hidden Gems")
        self.tabs.addTab(self.analytics_tab, "Analytics")
        self.tabs.addTab(self.download_tab, "Download Tracks")
        
        main_layout.addWidget(self.tabs)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.open_output_button = QPushButton("Open Output Folder")
        self.create_playlist_button = QPushButton("Create Spotify Playlist")
        self.export_button = QPushButton("Export Results")
        
        actions_layout.addWidget(self.open_output_button)
        actions_layout.addWidget(self.create_playlist_button)
        actions_layout.addWidget(self.export_button)
        
        main_layout.addLayout(actions_layout)
    
    def _connect_signals(self):
        """Connect signals to slots."""
        # Button signals
        self.open_output_button.clicked.connect(self._on_open_output_clicked)
        self.create_playlist_button.clicked.connect(self._on_create_playlist_clicked)
        self.export_button.clicked.connect(self._on_export_clicked)
        self.apply_filter_button.clicked.connect(self._on_apply_filter_clicked)
        
        # Table signals
        self.tracks_table.cellDoubleClicked.connect(self._on_track_link_clicked)
        self.gems_table.cellDoubleClicked.connect(self._on_gem_link_clicked)
        
        # Download tab signals
        self.download_tab.download_completed.connect(self._on_download_completed)
    
    def display_results(self, playlist_id: str, metadata: Dict, tracks: List[Dict], output_dir: str):
        """Display the results of playlist processing.
        
        Args:
            playlist_id: The Spotify playlist ID
            metadata: Playlist metadata dictionary
            tracks: List of track dictionaries
            output_dir: Directory where output files are saved
        """
        # Store the data
        self.playlist_id = playlist_id
        self.metadata = metadata
        self.tracks = tracks
        self.output_dir = output_dir
        
        # Update the header
        self.title_label.setText(f"Results: {metadata.get('name', 'Unknown Playlist')}")
        self.playlist_info_label.setText(
            f"{len(tracks)} tracks | Owner: {metadata.get('owner', 'Unknown')} | "
            f"Followers: {metadata.get('followers', 0)}"
        )
        
        # Update tables
        self._populate_tracks_table()
        self._populate_gems_table()
        self._update_analytics()
        
        # Set up download tab
        self.download_tab.setup_playlist(playlist_id, metadata, tracks, output_dir)
        
        logger.info(f"Displayed results for playlist {playlist_id} with {len(tracks)} tracks")
    
    def _populate_tracks_table(self):
        """Populate the all tracks table with track information."""
        # Clear the table
        self.tracks_table.setRowCount(0)
        
        # Add each track
        for row, track in enumerate(self.tracks):
            self.tracks_table.insertRow(row)
            
            # Track name
            self.tracks_table.setItem(row, 0, QTableWidgetItem(track.get('name', 'Unknown')))
            
            # Artists
            artists = ", ".join(track.get('artists', ['Unknown']))
            self.tracks_table.setItem(row, 1, QTableWidgetItem(artists))
            
            # Album
            self.tracks_table.setItem(row, 2, QTableWidgetItem(track.get('album', 'Unknown')))
            
            # Duration (formatted)
            duration_ms = track.get('duration_ms', 0)
            minutes = int(duration_ms / 60000)
            seconds = int((duration_ms % 60000) / 1000)
            duration_str = f"{minutes}:{seconds:02d}"
            self.tracks_table.setItem(row, 3, QTableWidgetItem(duration_str))
            
            # Popularity
            popularity = track.get('popularity', 0)
            popularity_item = QTableWidgetItem(str(popularity))
            self.tracks_table.setItem(row, 4, popularity_item)
            
            # Color-code popularity
            if popularity < 30:
                popularity_item.setBackground(QColor(255, 200, 200))  # Light red for low popularity
            elif popularity > 70:
                popularity_item.setBackground(QColor(200, 255, 200))  # Light green for high popularity
            
            # Explicit
            explicit = "Yes" if track.get('explicit', False) else "No"
            self.tracks_table.setItem(row, 5, QTableWidgetItem(explicit))
            
            # Link (as a button)
            link_item = QTableWidgetItem("Open")
            link_item.setData(Qt.ItemDataRole.UserRole, track.get('external_urls', {}).get('spotify', ''))
            self.tracks_table.setItem(row, 6, link_item)
    
    def _populate_gems_table(self):
        """Populate the hidden gems table with filtered tracks."""
        # Apply the current filter settings
        self._on_apply_filter_clicked()
    
    def _update_analytics(self):
        """Update the analytics tab with playlist statistics."""
        if not self.tracks:
            return
        
        # Basic statistics
        track_count = len(self.tracks)
        explicit_count = sum(1 for track in self.tracks if track.get('explicit', False))
        
        # Calculate average popularity
        total_popularity = sum(track.get('popularity', 0) for track in self.tracks)
        avg_popularity = total_popularity / track_count if track_count > 0 else 0
        
        # Calculate total duration
        total_duration_ms = sum(track.get('duration_ms', 0) for track in self.tracks)
        total_minutes = int(total_duration_ms / 60000)
        total_hours = total_minutes // 60
        remaining_minutes = total_minutes % 60
        
        # Update labels
        self.track_count_label.setText(str(track_count))
        self.avg_popularity_label.setText(f"{avg_popularity:.1f}")
        self.explicit_count_label.setText(f"{explicit_count} ({explicit_count/track_count*100:.1f}%)")
        self.total_duration_label.setText(f"{total_hours}h {remaining_minutes}m")
    
    def _calculate_hidden_gems_score(self, track: Dict) -> int:
        """Calculate the hidden gems score for a track.
        
        Args:
            track: Track dictionary
            
        Returns:
            Score from 0-50
        """
        score = 0
        
        # Popularity score (0-20 points)
        # Lower popularity = higher score
        popularity = track.get('popularity', 50)
        if popularity <= 20:
            score += 20
        elif popularity <= 40:
            score += 15
        elif popularity <= 60:
            score += 10
        elif popularity <= 80:
            score += 5
        
        # Artist collaboration (0-10 points)
        # More artists = higher score
        artists_count = len(track.get('artists', []))
        if artists_count >= 3:
            score += 10
        elif artists_count == 2:
            score += 5
        
        # Track duration (0-10 points)
        # Longer tracks get higher scores
        duration_ms = track.get('duration_ms', 0)
        duration_min = duration_ms / 60000
        
        if duration_min >= 7:
            score += 10
        elif duration_min >= 5:
            score += 7
        elif duration_min >= 4:
            score += 5
        elif duration_min >= 3:
            score += 3
        
        # Release type bonus (0-10 points) - not implemented here
        # Would need album type information
        
        return score
    
    @Slot()
    def _on_apply_filter_clicked(self):
        """Apply hidden gems filter and update the gems table."""
        if not self.tracks:
            return
            
        # Get filter values
        min_pop = self.min_popularity.currentData()
        max_pop = self.max_popularity.currentData()
        min_score = self.min_score.currentData()
        
        # Clear the table
        self.gems_table.setRowCount(0)
        
        # Filter tracks and add to table
        row = 0
        for track in self.tracks:
            popularity = track.get('popularity', 0)
            
            # Skip if not within popularity range
            if popularity < min_pop or popularity > max_pop:
                continue
                
            # Calculate score
            score = self._calculate_hidden_gems_score(track)
            
            # Skip if below minimum score
            if score < min_score:
                continue
                
            # Add to table
            self.gems_table.insertRow(row)
            
            # Track name
            self.gems_table.setItem(row, 0, QTableWidgetItem(track.get('name', 'Unknown')))
            
            # Artists
            artists = ", ".join(track.get('artists', ['Unknown']))
            self.gems_table.setItem(row, 1, QTableWidgetItem(artists))
            
            # Album
            self.gems_table.setItem(row, 2, QTableWidgetItem(track.get('album', 'Unknown')))
            
            # Popularity
            popularity_item = QTableWidgetItem(str(popularity))
            self.gems_table.setItem(row, 3, popularity_item)
            
            # Score
            score_item = QTableWidgetItem(str(score))
            score_item.setBackground(QColor(200, 255, 200))  # Light green
            self.gems_table.setItem(row, 4, score_item)
            
            # Duration (formatted)
            duration_ms = track.get('duration_ms', 0)
            minutes = int(duration_ms / 60000)
            seconds = int((duration_ms % 60000) / 1000)
            duration_str = f"{minutes}:{seconds:02d}"
            self.gems_table.setItem(row, 5, QTableWidgetItem(duration_str))
            
            # Explicit
            explicit = "Yes" if track.get('explicit', False) else "No"
            self.gems_table.setItem(row, 6, QTableWidgetItem(explicit))
            
            # Link (as a button)
            link_item = QTableWidgetItem("Open")
            link_item.setData(Qt.ItemDataRole.UserRole, track.get('external_urls', {}).get('spotify', ''))
            self.gems_table.setItem(row, 7, link_item)
            
            row += 1
        
        # Update the tab name with count
        self.tabs.setTabText(1, f"Hidden Gems ({self.gems_table.rowCount()})")
        logger.info(f"Applied hidden gems filter: found {self.gems_table.rowCount()} tracks")
    
    @Slot(int, int)
    def _on_track_link_clicked(self, row: int, column: int):
        """Handle track link clicked in the tracks table.
        
        Args:
            row: Table row index
            column: Table column index
        """
        if column == 6:  # Link column
            link = self.tracks_table.item(row, column).data(Qt.ItemDataRole.UserRole)
            if link:
                QDesktopServices.openUrl(QUrl(link))
    
    @Slot(int, int)
    def _on_gem_link_clicked(self, row: int, column: int):
        """Handle track link clicked in the gems table.
        
        Args:
            row: Table row index
            column: Table column index
        """
        if column == 7:  # Link column
            link = self.gems_table.item(row, column).data(Qt.ItemDataRole.UserRole)
            if link:
                QDesktopServices.openUrl(QUrl(link))
    
    @Slot()
    def _on_open_output_clicked(self):
        """Handle open output folder button click."""
        if not self.output_dir or not os.path.exists(self.output_dir):
            self.error_service.handle_error(Exception("Output directory not found"), self)
            return
            
        # Open the folder in file explorer
        try:
            # For Windows
            if os.name == 'nt':
                os.startfile(self.output_dir)
            # For macOS
            elif os.name == 'posix' and sys.platform == 'darwin':
                subprocess.call(['open', self.output_dir])
            # For Linux
            else:
                subprocess.call(['xdg-open', self.output_dir])
                
            logger.info(f"Opened output directory: {self.output_dir}")
        except Exception as e:
            self.error_service.handle_error(e, self)
    
    @Slot()
    def _on_create_playlist_clicked(self):
        """Handle create playlist button click."""
        # Check if we're on the hidden gems tab
        if self.tabs.currentIndex() == 1 and self.gems_table.rowCount() > 0:
            # Get tracks from hidden gems table
            tracks = []
            for row in range(self.gems_table.rowCount()):
                track_name = self.gems_table.item(row, 0).text()
                track_artists = self.gems_table.item(row, 1).text()
                track_link = self.gems_table.item(row, 7).data(Qt.ItemDataRole.UserRole)
                track_score = self.gems_table.item(row, 4).text()
                
                tracks.append({
                    'name': track_name,
                    'artists': track_artists.split(', '),
                    'link': track_link,
                    'score': int(track_score)
                })
                
            # TODO: Implement playlist creation dialog
            QMessageBox.information(
                self,
                "Create Playlist",
                "Playlist creation will be implemented in a future version."
            )
        else:
            QMessageBox.information(
                self,
                "Create Playlist",
                "Please switch to the Hidden Gems tab and filter the tracks you want to include."
            )
    
    @Slot()
    def _on_export_clicked(self):
        """Handle export results button click."""
        if not self.tracks:
            return
            
        # Determine which table to export based on current tab
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 0:  # All Tracks
            table = self.tracks_table
            default_name = f"{self.metadata.get('name', 'playlist')}_all_tracks.csv"
        elif current_tab == 1:  # Hidden Gems
            table = self.gems_table
            default_name = f"{self.metadata.get('name', 'playlist')}_hidden_gems.csv"
        else:  # Analytics - not implemented
            QMessageBox.information(
                self,
                "Export Results",
                "Exporting analytics will be implemented in a future version."
            )
            return
            
        # Ask for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            os.path.join(self.output_dir, default_name),
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write header
                headers = []
                for col in range(table.columnCount()):
                    headers.append(table.horizontalHeaderItem(col).text())
                    
                f.write(','.join(f'"{h}"' for h in headers) + '\n')
                
                # Write data
                for row in range(table.rowCount()):
                    row_data = []
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if col == 6 or col == 7:  # Link columns
                            link = item.data(Qt.ItemDataRole.UserRole) if item else ""
                            row_data.append(f'"{link}"')
                        else:
                            text = item.text() if item else ""
                            row_data.append(f'"{text}"')
                    
                    f.write(','.join(row_data) + '\n')
                    
            logger.info(f"Exported results to {file_path}")
            QMessageBox.information(
                self,
                "Export Complete",
                f"Results exported successfully to:\n{file_path}"
            )
        except Exception as e:
            self.error_service.handle_error(e, self)
            
    @Slot(list)
    def _on_download_completed(self, results: List[Dict]):
        """Handle download completion from the download tab.
        
        Args:
            results: List of download result dictionaries
        """
        # Count successes
        successful = sum(1 for r in results if r.get('success', False))
        
        # Show a notification
        QMessageBox.information(
            self,
            "Download Complete",
            f"Download completed with {successful} of {len(results)} tracks successfully downloaded."
        )
        
        logger.info(f"Download completed: {successful}/{len(results)} tracks successful") 