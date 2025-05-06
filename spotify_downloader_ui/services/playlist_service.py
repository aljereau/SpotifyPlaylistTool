"""
Playlist service for interacting with the backend playlist functionality.
"""

import logging
import os
import sys
import traceback
from typing import Dict, List, Optional, Tuple, Callable, Any
from PySide6.QtCore import QObject, Signal, Slot, QThread

# Import the backend functionality
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.spotify_playlist_extractor import (
        validate_spotify_url,
        initialize_spotify,
        get_playlist_metadata,
        get_all_tracks,
        process_playlist,
        display_playlist_preview,
        read_playlist_urls,
        SpotifyExtractorError
    )
except ImportError as e:
    logging.error(f"Failed to import backend functionality: {str(e)}")
    # Create placeholder functions for type checking
    def validate_spotify_url(url: str) -> str: return ""
    def initialize_spotify(): return None
    def get_playlist_metadata(sp, playlist_id: str) -> Dict: return {}
    def get_all_tracks(sp, playlist_id: str) -> List[Dict]: return []
    def process_playlist(sp, url: str, output_dir: str, 
                      include_artist: bool = False, no_playlist_folders: bool = False) -> Tuple[str, str, str]: 
        return ("", "", "")
    def display_playlist_preview(metadata: Dict, tracks: List[Dict]) -> None: pass
    def read_playlist_urls(file_path: str) -> List[str]: return []
    class SpotifyExtractorError(Exception): pass

logger = logging.getLogger(__name__)

class PlaylistWorker(QObject):
    """Worker class for processing playlists in a separate thread."""
    
    # Signals
    finished = Signal()
    progress = Signal(int, int)  # current, total
    error = Signal(Exception)
    playlist_processed = Signal(str, object, object, str)  # playlist_id, metadata, tracks, output_dir
    
    def __init__(self, url: str, output_dir: str, include_artist: bool = False, 
                 create_playlist_folders: bool = True):
        """Initialize the worker.
        
        Args:
            url: Spotify playlist URL to process
            output_dir: Directory to save output files
            include_artist: Whether to include artist name in filenames
            create_playlist_folders: Whether to create separate folders for each playlist
        """
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.include_artist = include_artist
        self.create_playlist_folders = create_playlist_folders
        self.sp = None
    
    @Slot()
    def process(self):
        """Process the playlist."""
        try:
            logger.info(f"Processing playlist: {self.url}")
            logger.info(f"Using output directory: {self.output_dir} (type: {type(self.output_dir)})")
            
            # Validate URL and extract playlist ID
            playlist_id = validate_spotify_url(self.url)
            
            # Initialize Spotify client
            self.sp = initialize_spotify()
            
            # Get playlist metadata
            metadata = get_playlist_metadata(self.sp, playlist_id)
            
            # Get tracks with progress updates
            tracks = []
            total_tracks = metadata['total_tracks']
            
            # Signal initial progress
            self.progress.emit(0, total_tracks)
            
            batch_size = 100
            for offset in range(0, total_tracks, batch_size):
                batch = self.sp.playlist_tracks(playlist_id, limit=batch_size, offset=offset)
                for i, item in enumerate(batch['items']):
                    if 'track' in item and item['track']:
                        track = {
                            'name': item['track']['name'],
                            'artists': [artist['name'] for artist in item['track']['artists']],
                            'album': item['track']['album']['name'],
                            'duration_ms': item['track']['duration_ms'],
                            'popularity': item['track'].get('popularity', 0),
                            'explicit': item['track']['explicit'],
                            'id': item['track']['id'],
                            'uri': item['track']['uri'],
                            'preview_url': item['track'].get('preview_url'),
                            'external_urls': item['track']['external_urls']
                        }
                        tracks.append(track)
                
                # Update progress
                self.progress.emit(min(offset + batch_size, total_tracks), total_tracks)
            
            # Process the playlist using the backend function - ensure output_dir is a string
            logger.info(f"Calling backend process_playlist with output_dir: {self.output_dir}")
            folder_path, tracks_file, links_file = process_playlist(
                self.sp,
                self.url,
                self.output_dir,  # This must be a string
                self.include_artist,
                not self.create_playlist_folders
            )
            
            # Emit success signal with results
            self.playlist_processed.emit(playlist_id, metadata, tracks, folder_path)
            
            # Signal completion
            self.finished.emit()
            
        except Exception as e:
            logger.error(f"Error processing playlist: {str(e)}")
            logger.error(traceback.format_exc())
            self.error.emit(e)
            self.finished.emit()


class PlaylistService(QObject):
    """Service for interacting with the backend playlist functionality."""
    
    # Signals
    playlist_validation_completed = Signal(str)  # playlist_id
    playlist_metadata_loaded = Signal(object)  # metadata
    playlist_processing_started = Signal(str)  # playlist_id
    playlist_processing_progress = Signal(int, int)  # current, total
    playlist_processed = Signal(str, object, object, str)  # playlist_id, metadata, tracks, output_dir
    processing_error = Signal(Exception)
    
    def __init__(self):
        """Initialize the playlist service."""
        super().__init__()
        self.thread = None
        self.worker = None
        logger.info("Playlist service initialized")
    
    def validate_playlist_url(self, url: str) -> Optional[str]:
        """Validate a Spotify playlist URL.
        
        Args:
            url: The URL to validate
            
        Returns:
            Playlist ID if valid, None if not
        """
        try:
            playlist_id = validate_spotify_url(url)
            self.playlist_validation_completed.emit(playlist_id)
            return playlist_id
        except SpotifyExtractorError as e:
            self.processing_error.emit(e)
            return None
    
    def get_playlist_metadata(self, url: str) -> Optional[Dict]:
        """Get playlist metadata.
        
        Args:
            url: Spotify playlist URL
            
        Returns:
            Playlist metadata dict if successful, None if not
        """
        try:
            playlist_id = validate_spotify_url(url)
            sp = initialize_spotify()
            metadata = get_playlist_metadata(sp, playlist_id)
            self.playlist_metadata_loaded.emit(metadata)
            return metadata
        except Exception as e:
            self.processing_error.emit(e)
            return None
    
    def process_playlist(self, url: str, output_dir: str, include_artist: bool = False,
                        create_playlist_folders: bool = True):
        """Process a playlist asynchronously.
        
        Args:
            url: Spotify playlist URL
            output_dir: Directory to save output files
            include_artist: Whether to include artist name in filenames
            create_playlist_folders: Whether to create separate folders for each playlist
        """
        # Clean up previous worker/thread if exists
        if self.thread is not None and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        
        # CRITICAL FIX: Ensure output_dir is a string before passing it to worker
        # Extract values from dictionary if needed
        options = None
        if isinstance(output_dir, dict):
            options = output_dir
            # Default values
            actual_output_dir = "output"
            actual_include_artist = include_artist
            actual_create_playlist_folders = create_playlist_folders
            
            # Extract options if available
            if "output_dir" in options and isinstance(options["output_dir"], str):
                actual_output_dir = options["output_dir"]
            if "include_artist" in options:
                actual_include_artist = options["include_artist"]
            if "create_playlist_folders" in options:
                actual_create_playlist_folders = options["create_playlist_folders"]
            
            # Use the variables directly from here
            logger.info(f"Fixed process_playlist params - output_dir: {actual_output_dir}, "
                      f"include_artist: {actual_include_artist}, "
                      f"create_playlist_folders: {actual_create_playlist_folders}")
        else:
            # Use the parameters directly
            actual_output_dir = output_dir if isinstance(output_dir, str) else "output"
            actual_include_artist = include_artist
            actual_create_playlist_folders = create_playlist_folders
            
        # Create worker and thread - pass fixed parameters
        self.thread = QThread()
        self.worker = PlaylistWorker(url, actual_output_dir, actual_include_artist, actual_create_playlist_folders)
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.thread.started.connect(self.worker.process)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.worker.progress.connect(self.playlist_processing_progress)
        self.worker.error.connect(self.processing_error)
        self.worker.playlist_processed.connect(self.playlist_processed)
        
        # Start processing
        self.thread.start()
    
    def cancel_processing(self):
        """Cancel the current playlist processing operation."""
        if self.thread is not None and self.thread.isRunning():
            logger.info("Cancelling playlist processing")
            self.thread.quit()
            self.thread.wait()
            
    def read_playlist_urls_from_file(self, file_path: str) -> List[str]:
        """Read playlist URLs from a file.
        
        Args:
            file_path: Path to the file containing URLs
            
        Returns:
            List of playlist URLs
        """
        try:
            return read_playlist_urls(file_path)
        except Exception as e:
            self.processing_error.emit(e)
            return [] 