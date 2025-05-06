"""
Download view for downloading tracks from processed playlists.
"""

import os
import logging
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QProgressBar, QTableWidget, QTableWidgetItem, QComboBox,
    QSpinBox, QCheckBox, QGroupBox, QFormLayout, QAbstractItemView,
    QHeaderView, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject

# Import the downloader functionality
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.spotify_downloader import (
        download_playlist, download_tracks, check_dependencies, DownloaderError
    )
except ImportError as e:
    logging.error(f"Failed to import downloader functionality: {str(e)}")

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService
from spotify_downloader_ui.services.playlist_service import PlaylistService

logger = logging.getLogger(__name__)

class DownloadWorker(QObject):
    """Worker class for downloading tracks in a separate thread."""
    
    # Signals
    started = Signal()
    progress = Signal(int, int)  # current, total
    track_completed = Signal(object)  # track result
    finished = Signal(list)  # download results
    error = Signal(str)  # error message
    
    def __init__(self, playlist_id: str, metadata: Dict, tracks: List[Dict], 
                 output_dir: str, format_str: str = "mp3", max_workers: int = 4,
                 skip_existing: bool = True):
        """Initialize the worker.
        
        Args:
            playlist_id: Spotify playlist ID
            metadata: Playlist metadata
            tracks: List of track dictionaries
            output_dir: Directory to save tracks
            format_str: Audio format (mp3, m4a, etc.)
            max_workers: Maximum concurrent downloads
            skip_existing: Whether to skip existing files
        """
        super().__init__()
        self.playlist_id = playlist_id
        self.metadata = metadata
        self.tracks = tracks
        self.output_dir = output_dir
        self.format_str = format_str
        self.max_workers = max_workers
        self.skip_existing = skip_existing
        self.results = []
    
    @Slot()
    def process(self):
        """Download the tracks."""
        try:
            self.started.emit()
            
            # Create download directory
            playlist_dir = os.path.join(self.output_dir, self.metadata.get('name', self.playlist_id))
            os.makedirs(playlist_dir, exist_ok=True)
            
            downloads_dir = os.path.join(playlist_dir, "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Custom callback for track completion
            def track_callback(result):
                self.track_completed.emit(result)
                self.results.append(result)
                # Update progress
                completed = len(self.results)
                total = len(self.tracks)
                self.progress.emit(completed, total)
            
            # Download tracks (alternative implementation that reports progress)
            from concurrent.futures import ThreadPoolExecutor
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all download tasks
                futures = []
                for track in self.tracks:
                    from src.spotify_downloader import download_track
                    future = executor.submit(
                        download_track, 
                        track, 
                        downloads_dir, 
                        self.format_str,
                        3,  # retry_count
                        self.skip_existing
                    )
                    futures.append(future)
                
                # Process results as they complete
                from concurrent.futures import as_completed
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        track_callback(result)
                    except Exception as e:
                        # Handle individual track errors without stopping all downloads
                        logger.error(f"Error downloading track: {str(e)}")
                        error_result = {
                            "track": {"name": "Unknown"},
                            "success": False,
                            "error": str(e)
                        }
                        track_callback(error_result)
            
            # Signal completion with results
            self.finished.emit(self.results)
            
        except Exception as e:
            logger.error(f"Error in download worker: {str(e)}")
            self.error.emit(str(e))
            self.finished.emit([])


class DownloadView(QWidget):
    """View for downloading tracks from processed playlists."""
    
    # Signals
    download_started = Signal()
    download_completed = Signal(list)  # download results
    
    def __init__(self, playlist_service: PlaylistService, 
                 config_service: ConfigService, 
                 error_service: ErrorService):
        """Initialize the download view.
        
        Args:
            playlist_service: Service for playlist operations
            config_service: Service for configuration
            error_service: Service for error handling
        """
        super().__init__()
        
        # Store services
        self.playlist_service = playlist_service
        self.config_service = config_service
        self.error_service = error_service
        
        # Initialize state
        self.current_playlist_id = None
        self.current_metadata = None
        self.current_tracks = None
        self.current_output_dir = None
        self.download_thread = None
        self.download_worker = None
        self.download_results = []
        
        # Set up UI
        self._init_ui()
        
        # Check dependencies
        self._check_dependencies()
    
    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        
        # Downloads settings section
        settings_group = QGroupBox("Download Settings")
        settings_layout = QFormLayout(settings_group)
        
        # Format selection
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "m4a", "opus", "wav"])
        settings_layout.addRow("Format:", self.format_combo)
        
        # Concurrent downloads
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 8)
        self.workers_spin.setValue(4)
        settings_layout.addRow("Concurrent downloads:", self.workers_spin)
        
        # Skip existing files
        self.skip_existing_check = QCheckBox("Skip existing files")
        self.skip_existing_check.setChecked(True)
        settings_layout.addRow("", self.skip_existing_check)
        
        # Output directory
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Using default output directory")
        output_layout.addWidget(self.output_label)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._on_browse_clicked)
        output_layout.addWidget(self.browse_button)
        
        settings_layout.addRow("Output:", output_layout)
        
        main_layout.addWidget(settings_group)
        
        # Status and buttons section
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready to download")
        status_layout.addWidget(self.status_label, 1)
        
        self.download_button = QPushButton("Download All Tracks")
        self.download_button.clicked.connect(self._on_download_clicked)
        status_layout.addWidget(self.download_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.cancel_button.setEnabled(False)
        status_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(status_layout)
        
        # Progress section
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        # "Currently downloading" label
        self.current_track_label = QLabel("No download in progress")
        progress_layout.addWidget(self.current_track_label)
        
        main_layout.addLayout(progress_layout)
        
        # Results table
        self.results_table = QTableWidget(0, 4)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setHorizontalHeaderLabels(["Track", "Artist", "Status", "Details"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.results_table.verticalHeader().setVisible(False)
        
        main_layout.addWidget(self.results_table)
        
        # Open folder button
        self.open_folder_button = QPushButton("Open Download Folder")
        self.open_folder_button.clicked.connect(self._on_open_folder_clicked)
        self.open_folder_button.setEnabled(False)
        main_layout.addWidget(self.open_folder_button)
    
    def _check_dependencies(self):
        """Check if required dependencies are installed."""
        try:
            if not check_dependencies():
                self.error_service.show_error(
                    "Missing Dependencies",
                    "Required dependencies (yt-dlp, ffmpeg) are not installed. "
                    "Please install these dependencies to use the download functionality."
                )
                self.download_button.setEnabled(False)
                self.status_label.setText("Dependencies missing - downloads disabled")
        except Exception as e:
            logger.error(f"Error checking dependencies: {str(e)}")
    
    def setup_playlist(self, playlist_id: str, metadata: object, tracks: list, output_dir: str):
        """Set up the view with playlist information.
        
        Args:
            playlist_id: Spotify playlist ID
            metadata: Playlist metadata
            tracks: List of track dictionaries
            output_dir: Directory for processed playlist
        """
        self.current_playlist_id = playlist_id
        self.current_metadata = metadata
        self.current_tracks = tracks
        self.current_output_dir = output_dir
        
        # Update UI
        self.status_label.setText(f"Ready to download {len(tracks)} tracks from \"{metadata.get('name', 'Unknown')}\"")
        self.output_label.setText(f"Output directory: {output_dir}")
        self.progress_bar.setRange(0, len(tracks))
        self.progress_bar.setValue(0)
        
        # Clear previous results
        self.results_table.setRowCount(0)
        self.download_results = []
        
        # Populate table with tracks (status will be updated during download)
        self._populate_table()
        
        # Enable buttons
        self.download_button.setEnabled(True)
        self.open_folder_button.setEnabled(True)
    
    def _populate_table(self):
        """Populate the results table with tracks."""
        if not self.current_tracks:
            return
        
        self.results_table.setRowCount(len(self.current_tracks))
        
        for i, track in enumerate(self.current_tracks):
            # Track name
            name_item = QTableWidgetItem(track.get('name', 'Unknown'))
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.results_table.setItem(i, 0, name_item)
            
            # Artist
            artists = ", ".join(track.get('artist_names', []))
            artist_item = QTableWidgetItem(artists)
            artist_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.results_table.setItem(i, 1, artist_item)
            
            # Status (initially "Pending")
            status_item = QTableWidgetItem("Pending")
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.results_table.setItem(i, 2, status_item)
            
            # Details (initially empty)
            details_item = QTableWidgetItem("")
            details_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.results_table.setItem(i, 3, details_item)
    
    def _update_track_status(self, track_result: object):
        """Update the status of a track in the table.
        
        Args:
            track_result: Dictionary with download result information
        """
        track = track_result.get('track', {})
        track_name = track.get('name', 'Unknown')
        
        # Find the row for this track
        for i in range(self.results_table.rowCount()):
            name_item = self.results_table.item(i, 0)
            if name_item and name_item.text() == track_name:
                # Update status
                status_text = "Success" if track_result.get('success', False) else "Failed"
                status_item = QTableWidgetItem(status_text)
                status_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                
                # Set color based on status
                if track_result.get('success', False):
                    status_item.setBackground(Qt.GlobalColor.green)
                else:
                    status_item.setBackground(Qt.GlobalColor.red)
                    
                self.results_table.setItem(i, 2, status_item)
                
                # Update details
                details = track_result.get('error', '') if not track_result.get('success', False) else "Downloaded"
                details_item = QTableWidgetItem(details)
                details_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.results_table.setItem(i, 3, details_item)
                
                # Ensure this row is visible
                self.results_table.scrollToItem(name_item)
                break
    
    @Slot()
    def _on_browse_clicked(self):
        """Handle browse button click for output directory selection."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.current_output_dir or os.path.expanduser("~")
        )
        
        if directory:
            self.current_output_dir = directory
            self.output_label.setText(f"Output directory: {directory}")
    
    @Slot()
    def _on_download_clicked(self):
        """Handle download button click."""
        if not self.current_tracks:
            return
        
        # Update UI state
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.format_combo.setEnabled(False)
        self.workers_spin.setEnabled(False)
        self.skip_existing_check.setEnabled(False)
        self.browse_button.setEnabled(False)
        
        # Reset progress
        self.progress_bar.setValue(0)
        
        # Get settings
        format_str = self.format_combo.currentText()
        max_workers = self.workers_spin.value()
        skip_existing = self.skip_existing_check.isChecked()
        
        # Start download in a separate thread
        self.download_thread = QThread()
        self.download_worker = DownloadWorker(
            playlist_id=self.current_playlist_id,
            metadata=self.current_metadata,
            tracks=self.current_tracks,
            output_dir=self.current_output_dir,
            format_str=format_str,
            max_workers=max_workers,
            skip_existing=skip_existing
        )
        
        self.download_worker.moveToThread(self.download_thread)
        
        # Connect signals
        self.download_thread.started.connect(self.download_worker.process)
        self.download_worker.started.connect(self._on_download_started)
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.track_completed.connect(self._on_track_completed)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.error.connect(self._on_download_error)
        
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        
        # Start thread
        self.download_thread.start()
    
    @Slot()
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        if self.download_thread and self.download_thread.isRunning():
            # Signal thread to stop
            self.download_thread.requestInterruption()
            # Abort thread if it doesn't stop quickly
            if not self.download_thread.wait(1000):
                self.download_thread.terminate()
                self.download_thread.wait()
            
            # Update UI state
            self.status_label.setText("Download cancelled")
            self._reset_ui_state()
    
    @Slot()
    def _on_open_folder_clicked(self):
        """Handle open folder button click."""
        if self.current_output_dir and os.path.exists(self.current_output_dir):
            playlist_dir = os.path.join(
                self.current_output_dir, 
                self.current_metadata.get('name', self.current_playlist_id)
            )
            downloads_dir = os.path.join(playlist_dir, "Downloads")
            
            # Use either downloads directory or playlist directory, whichever exists
            target_dir = downloads_dir if os.path.exists(downloads_dir) else playlist_dir
            
            # Open folder in file explorer
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(target_dir))
    
    @Slot()
    def _on_download_started(self):
        """Handle download started signal."""
        self.status_label.setText("Download started...")
        self.download_started.emit()
    
    @Slot(int, int)
    def _on_download_progress(self, current: int, total: int):
        """Handle download progress signal.
        
        Args:
            current: Number of completed tracks
            total: Total number of tracks
        """
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Downloading... {current}/{total} tracks completed")
    
    @Slot(dict)
    def _on_track_completed(self, result: object):
        """Handle track completed signal.
        
        Args:
            result: Dictionary with download result information
        """
        # Update track information in table
        self._update_track_status(result)
        
        # Update current track label
        track_name = result.get('track', {}).get('name', 'Unknown')
        status = "Successfully downloaded" if result.get('success', False) else "Failed to download"
        self.current_track_label.setText(f"{status}: {track_name}")
    
    @Slot(list)
    def _on_download_finished(self, results: list):
        """Handle download finished signal.
        
        Args:
            results: List of download result dictionaries
        """
        self.download_results = results
        
        # Count successes
        successful = sum(1 for r in results if r.get('success', False))
        
        # Update status
        self.status_label.setText(f"Download complete. {successful}/{len(results)} tracks downloaded successfully.")
        
        # Reset UI state
        self._reset_ui_state()
        
        # Enable open folder button
        self.open_folder_button.setEnabled(True)
        
        # Emit completion signal
        self.download_completed.emit(results)
    
    @Slot(str)
    def _on_download_error(self, error_message: str):
        """Handle download error signal.
        
        Args:
            error_message: Error message
        """
        self.error_service.show_error(
            "Download Error", 
            f"An error occurred during download: {error_message}"
        )
        
        # Update status
        self.status_label.setText("Download failed. See error message.")
        
        # Reset UI state
        self._reset_ui_state()
    
    def _reset_ui_state(self):
        """Reset the UI state after download completes or cancels."""
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.format_combo.setEnabled(True)
        self.workers_spin.setEnabled(True)
        self.skip_existing_check.setEnabled(True)
        self.browse_button.setEnabled(True) 