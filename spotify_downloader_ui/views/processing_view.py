"""
Processing view for displaying playlist processing progress.
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, Slot, QSize

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService
from spotify_downloader_ui.services.playlist_service import PlaylistService
from spotify_downloader_ui.views.components import (
    ProcessVisualization, ProcessStage, ProgressLevel, ProgressState
)

logger = logging.getLogger(__name__)

class ProcessingView(QWidget):
    """Widget for displaying playlist processing progress."""
    
    def __init__(self, playlist_service: PlaylistService, config_service: ConfigService,
                error_service: ErrorService):
        """Initialize the processing view.
        
        Args:
            playlist_service: Service for playlist operations
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        super().__init__()
        
        self.playlist_service = playlist_service
        self.config_service = config_service
        self.error_service = error_service
        
        self._init_ui()
        self._connect_signals()
        
        logger.info("Processing view initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Process visualization widget
        self.process_vis = ProcessVisualization()
        main_layout.addWidget(self.process_vis)
    
    def _connect_signals(self):
        """Connect signals to slots."""
        # Button signals
        self.process_vis.cancel_requested.connect(self._on_cancel_clicked)
        self.process_vis.pause_requested.connect(self._on_pause_requested)
        self.process_vis.resume_requested.connect(self._on_resume_requested)
        
        # Service signals
        self.playlist_service.playlist_processing_progress.connect(self._on_processing_progress)
        self.playlist_service.playlist_processed.connect(self._on_processing_completed)
        self.playlist_service.processing_error.connect(self._on_processing_error)
    
    @Slot()
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.playlist_service.cancel_processing()
        self.process_vis.add_detail("Processing cancelled by user")
        
        # Update the UI
        self.process_vis.set_status("Processing cancelled")
        self.process_vis.set_processing_complete(success=False, error_message="Cancelled by user")
    
    @Slot()
    def _on_pause_requested(self):
        """Handle pause request."""
        # In this version we don't actually pause the backend processing
        # as it's not supported by the backend, but we update the UI to show paused state
        self.process_vis.add_detail("Processing paused (UI only, backend continues)")
    
    @Slot()
    def _on_resume_requested(self):
        """Handle resume request."""
        self.process_vis.add_detail("Processing resumed")
    
    @Slot(int, int)
    def _on_processing_progress(self, current: int, total: int):
        """Handle processing progress update.
        
        Args:
            current: Current progress value
            total: Total items to process
        """
        # Calculate percentage
        if total > 0:
            percentage = int((current / total) * 100)
        else:
            percentage = 0
        
        # Update progress
        self.process_vis.update_progress(
            ProgressLevel.PLAYLIST, 
            current, 
            total,
            f"Processing track {current} of {total}"
        )
        
        # Update overall progress (simplified - just use the same progress for now)
        self.process_vis.update_progress(
            ProgressLevel.OVERALL,
            current,
            total
        )
        
        # Update operation progress (just pulse)
        if current > 0 and current < total:
            operation_progress = (current % 10) * 10  # Cycle through 0-100% for operation level
            self.process_vis.update_progress(
                ProgressLevel.OPERATION,
                operation_progress,
                100
            )
        
        # Set appropriate stage based on progress
        if current == 0:
            self.process_vis.set_stage(ProcessStage.INITIALIZATION)
            self.process_vis.add_detail(f"Starting processing of {total} tracks")
        elif current == 1:
            self.process_vis.set_stage(ProcessStage.METADATA)
            self.process_vis.add_detail("Retrieving playlist metadata")
        elif current < total // 3:
            # First third of processing - tracks stage
            if current == total // 10:
                self.process_vis.set_stage(ProcessStage.TRACKS)
                self.process_vis.add_detail("Processing track information")
        elif current < total * 2 // 3:
            # Second third - audio features
            if current == total // 3:
                self.process_vis.set_stage(ProcessStage.AUDIO_FEATURES)
                self.process_vis.add_detail("Analyzing audio features")
        elif current < total:
            # Last third - finalizing
            if current == total * 2 // 3:
                self.process_vis.set_stage(ProcessStage.FINALIZING)
                self.process_vis.add_detail("Finalizing playlist processing")
        elif current == total:
            self.process_vis.add_detail(f"Completed processing {total} tracks")
            
        # Log periodically
        if current % 10 == 0 or current == 1:
            self.process_vis.add_detail(f"Processed {current} of {total} tracks")
    
    @Slot(str, dict, list, str)
    def _on_processing_completed(self, playlist_id: str, metadata: dict, tracks: list, output_dir: str):
        """Handle processing completion.
        
        Args:
            playlist_id: Playlist ID
            metadata: Playlist metadata
            tracks: List of tracks
            output_dir: Output directory
        """
        # Update UI to show completion
        self.process_vis.set_processing_complete(success=True)
        
        # Update phase
        for i in range(5):  # Mark all phases as completed
            self.process_vis.set_phase(ProgressLevel.OVERALL, i)
        
        # Add completion details
        self.process_vis.add_detail(f"Playlist processing completed: {metadata.get('name', playlist_id)}")
        self.process_vis.add_detail(f"Output saved to: {output_dir}")
        self.process_vis.add_detail(f"Total tracks processed: {len(tracks)}")
        
        # Add playlist details
        details = []
        details.append(f"Playlist: {metadata.get('name', 'Unknown')}")
        details.append(f"Owner: {metadata.get('owner', 'Unknown')}")
        details.append(f"Tracks: {len(tracks)}")
        details.append(f"Followers: {metadata.get('followers', 0)}")
        details.append(f"Output Directory: {output_dir}")
        
        # Add track genres statistics if available
        genre_counts = {}
        for track in tracks:
            if 'genres' in track:
                for genre in track['genres']:
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        if genre_counts:
            details.append("Top Genres:")
            
            # Sort genres by count and display top 5
            top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for genre, count in top_genres:
                details.append(f"- {genre}: {count} tracks")
        
        # Add all details
        for detail in details:
            self.process_vis.add_detail(detail)
    
    @Slot(Exception)
    def _on_processing_error(self, error: Exception):
        """Handle processing error.
        
        Args:
            error: Error exception
        """
        error_message = str(error)
        self.process_vis.add_detail(f"Error: {error_message}")
        self.process_vis.set_processing_complete(success=False, error_message=error_message)
        
        # Show error dialog - use handle_error method instead of show_error
        self.error_service.handle_error(error, self)
    
    def reset_ui(self):
        """Reset the UI to its initial state."""
        self.process_vis.reset() 