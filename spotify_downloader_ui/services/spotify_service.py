"""
Spotify service for handling Spotify API integration.
"""

import os
import logging
import sys
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, Signal

# Import the backend functionality
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.spotify_playlist_extractor import (
        initialize_spotify,
        SpotifyExtractorError
    )
    import spotipy
except ImportError as e:
    logging.error(f"Failed to import backend functionality: {str(e)}")
    # Create placeholders for type checking
    def initialize_spotify(): return None
    class SpotifyExtractorError(Exception): pass
    class spotipy:
        class Spotify: pass

logger = logging.getLogger(__name__)

class SpotifyService(QObject):
    """Service for interacting with the Spotify API."""
    
    # Signals
    connection_status_changed = Signal(bool, str)  # connected, message
    error_occurred = Signal(Exception)
    
    def __init__(self):
        """Initialize the Spotify service."""
        super().__init__()
        self._spotify_client = None
        self._connected = False
        self._connection_message = "Not connected"
        logger.info("Spotify service initialized")
    
    def initialize(self) -> bool:
        """Initialize the Spotify client.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Initializing Spotify client")
            self._spotify_client = initialize_spotify()
            
            # Test the connection
            if self._spotify_client:
                # Make a simple API call to validate credentials
                self._spotify_client.current_user_saved_tracks(limit=1)
                self._connected = True
                self._connection_message = "Connected to Spotify API"
                self.connection_status_changed.emit(True, self._connection_message)
                logger.info("Successfully connected to Spotify API")
                return True
            else:
                self._connected = False
                self._connection_message = "Failed to initialize Spotify client"
                self.connection_status_changed.emit(False, self._connection_message)
                logger.error("Failed to initialize Spotify client")
                return False
                
        except SpotifyExtractorError as e:
            self._connected = False
            self._connection_message = f"Authentication error: {str(e)}"
            self.connection_status_changed.emit(False, self._connection_message)
            self.error_occurred.emit(e)
            logger.error(f"Spotify authentication error: {str(e)}")
            return False
        except Exception as e:
            self._connected = False
            self._connection_message = f"Connection error: {str(e)}"
            self.connection_status_changed.emit(False, self._connection_message)
            self.error_occurred.emit(e)
            logger.error(f"Spotify connection error: {str(e)}")
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Spotify API.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected
    
    @property
    def connection_message(self) -> str:
        """Get the current connection status message.
        
        Returns:
            Status message
        """
        return self._connection_message
    
    @property
    def spotify_client(self) -> Optional[Any]:
        """Get the Spotify client instance.
        
        Returns:
            Spotify client instance or None if not initialized
        """
        return self._spotify_client
    
    def search_tracks(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for tracks on Spotify.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of track data dictionaries
        """
        if not self._connected or not self._spotify_client:
            error = SpotifyExtractorError("Not connected to Spotify API", "connection_error")
            self.error_occurred.emit(error)
            return []
        
        try:
            results = self._spotify_client.search(q=query, type='track', limit=limit)
            tracks = []
            
            if 'tracks' in results and 'items' in results['tracks']:
                for item in results['tracks']['items']:
                    track = {
                        'name': item['name'],
                        'artists': [artist['name'] for artist in item['artists']],
                        'album': item['album']['name'],
                        'duration_ms': item['duration_ms'],
                        'popularity': item.get('popularity', 0),
                        'explicit': item['explicit'],
                        'id': item['id'],
                        'uri': item['uri'],
                        'preview_url': item.get('preview_url'),
                        'external_urls': item['external_urls']
                    }
                    tracks.append(track)
            
            return tracks
            
        except Exception as e:
            self.error_occurred.emit(e)
            logger.error(f"Error searching tracks: {str(e)}")
            return []
    
    def get_current_user_profile(self) -> Optional[Dict]:
        """Get the current user's Spotify profile.
        
        Returns:
            User profile data or None if not available
        """
        if not self._connected or not self._spotify_client:
            error = SpotifyExtractorError("Not connected to Spotify API", "connection_error")
            self.error_occurred.emit(error)
            return None
        
        try:
            return self._spotify_client.current_user()
        except Exception as e:
            self.error_occurred.emit(e)
            logger.error(f"Error getting user profile: {str(e)}")
            return None
    
    def create_playlist(self, name: str, description: str = "", public: bool = False) -> Optional[Dict]:
        """Create a new playlist for the current user.
        
        Args:
            name: Playlist name
            description: Playlist description
            public: Whether the playlist should be public
            
        Returns:
            Playlist data or None if creation failed
        """
        if not self._connected or not self._spotify_client:
            error = SpotifyExtractorError("Not connected to Spotify API", "connection_error")
            self.error_occurred.emit(error)
            return None
        
        try:
            user_profile = self.get_current_user_profile()
            if not user_profile:
                raise SpotifyExtractorError("Could not get user profile", "api_error")
            
            user_id = user_profile['id']
            playlist = self._spotify_client.user_playlist_create(
                user=user_id,
                name=name,
                public=public,
                description=description
            )
            return playlist
        except Exception as e:
            self.error_occurred.emit(e)
            logger.error(f"Error creating playlist: {str(e)}")
            return None
    
    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> bool:
        """Add tracks to a playlist.
        
        Args:
            playlist_id: Playlist ID
            track_uris: List of track URIs to add
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected or not self._spotify_client:
            error = SpotifyExtractorError("Not connected to Spotify API", "connection_error")
            self.error_occurred.emit(error)
            return False
        
        try:
            # Add tracks in batches of 100 (Spotify API limit)
            batch_size = 100
            for i in range(0, len(track_uris), batch_size):
                batch = track_uris[i:i + batch_size]
                self._spotify_client.playlist_add_items(playlist_id, batch)
            
            return True
        except Exception as e:
            self.error_occurred.emit(e)
            logger.error(f"Error adding tracks to playlist: {str(e)}")
            return False 