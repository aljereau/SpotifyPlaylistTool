"""
Model for storing playlist data.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PlaylistModel:
    """Model for storing playlist data."""
    
    def __init__(self, playlist_id: str = "", metadata: Dict = None, tracks: List[Dict] = None):
        """Initialize the playlist model.
        
        Args:
            playlist_id: Spotify playlist ID
            metadata: Playlist metadata
            tracks: List of tracks
        """
        self.playlist_id = playlist_id
        self.metadata = metadata or {}
        self.tracks = tracks or []
        
        logger.debug(f"Playlist model created for {playlist_id}")
    
    @property
    def name(self) -> str:
        """Get the playlist name.
        
        Returns:
            Playlist name
        """
        return self.metadata.get("name", f"Playlist {self.playlist_id[:8]}")
    
    @property
    def owner(self) -> str:
        """Get the playlist owner.
        
        Returns:
            Playlist owner
        """
        return self.metadata.get("owner", "Unknown")
    
    @property
    def description(self) -> str:
        """Get the playlist description.
        
        Returns:
            Playlist description
        """
        return self.metadata.get("description", "")
    
    @property
    def followers(self) -> int:
        """Get the number of playlist followers.
        
        Returns:
            Number of followers
        """
        return self.metadata.get("followers", 0)
    
    @property
    def track_count(self) -> int:
        """Get the number of tracks in the playlist.
        
        Returns:
            Number of tracks
        """
        return len(self.tracks)
    
    @property
    def image_url(self) -> str:
        """Get the playlist image URL.
        
        Returns:
            Image URL
        """
        return self.metadata.get("image_url", "")
    
    @property
    def spotify_url(self) -> str:
        """Get the Spotify URL for the playlist.
        
        Returns:
            Spotify URL
        """
        return f"https://open.spotify.com/playlist/{self.playlist_id}"
    
    def get_track(self, index: int) -> Optional[Dict]:
        """Get a track by index.
        
        Args:
            index: Track index
            
        Returns:
            Track data or None if index out of range
        """
        if 0 <= index < len(self.tracks):
            return self.tracks[index]
        return None
    
    def get_track_by_id(self, track_id: str) -> Optional[Dict]:
        """Get a track by ID.
        
        Args:
            track_id: Track ID
            
        Returns:
            Track data or None if not found
        """
        for track in self.tracks:
            if track.get("id") == track_id:
                return track
        return None
    
    def filter_tracks(self, **criteria) -> List[Dict]:
        """Filter tracks based on criteria.
        
        Args:
            **criteria: Filtering criteria
            
        Returns:
            Filtered list of tracks
        """
        filtered_tracks = self.tracks.copy()
        
        # Filter by min/max popularity
        if "min_popularity" in criteria:
            min_pop = criteria["min_popularity"]
            filtered_tracks = [t for t in filtered_tracks if t.get("popularity", 0) >= min_pop]
        
        if "max_popularity" in criteria:
            max_pop = criteria["max_popularity"]
            filtered_tracks = [t for t in filtered_tracks if t.get("popularity", 0) <= max_pop]
        
        # Filter by explicit
        if "explicit" in criteria:
            explicit = criteria["explicit"]
            filtered_tracks = [t for t in filtered_tracks if t.get("explicit", False) == explicit]
        
        # Filter by artist
        if "artist" in criteria:
            artist = criteria["artist"].lower()
            filtered_tracks = [
                t for t in filtered_tracks 
                if any(artist in a.lower() for a in t.get("artists", []))
            ]
        
        # Filter by album
        if "album" in criteria:
            album = criteria["album"].lower()
            filtered_tracks = [
                t for t in filtered_tracks 
                if album in t.get("album", "").lower()
            ]
        
        # Filter by name
        if "name" in criteria:
            name = criteria["name"].lower()
            filtered_tracks = [
                t for t in filtered_tracks 
                if name in t.get("name", "").lower()
            ]
        
        return filtered_tracks
    
    def get_hidden_gems(self, min_popularity: int = 5, max_popularity: int = 40, min_score: int = 20) -> List[Dict]:
        """Get hidden gems based on criteria.
        
        Args:
            min_popularity: Minimum popularity (0-100)
            max_popularity: Maximum popularity (0-100)
            min_score: Minimum hidden gems score
            
        Returns:
            List of hidden gems
        """
        # Filter tracks by popularity
        filtered_tracks = self.filter_tracks(
            min_popularity=min_popularity,
            max_popularity=max_popularity
        )
        
        # Calculate hidden gems score for each track
        for track in filtered_tracks:
            score = self._calculate_hidden_gems_score(track)
            track["hidden_gems_score"] = score
        
        # Filter by minimum score
        gems = [t for t in filtered_tracks if t.get("hidden_gems_score", 0) >= min_score]
        
        # Sort by score (highest first)
        gems.sort(key=lambda x: x.get("hidden_gems_score", 0), reverse=True)
        
        return gems
    
    def _calculate_hidden_gems_score(self, track: Dict) -> int:
        """Calculate hidden gems score for a track.
        
        Args:
            track: Track data
            
        Returns:
            Score from 0-50
        """
        score = 0
        
        # Popularity score (0-20 points)
        # Lower popularity = higher score
        popularity = track.get("popularity", 50)
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
        artists_count = len(track.get("artists", []))
        if artists_count >= 3:
            score += 10
        elif artists_count == 2:
            score += 5
        
        # Track duration (0-10 points)
        # Longer tracks get higher scores
        duration_ms = track.get("duration_ms", 0)
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
    
    def get_analytics(self) -> Dict:
        """Generate analytics for the playlist.
        
        Returns:
            Analytics data
        """
        if not self.tracks:
            return {
                "track_count": 0,
                "explicit_count": 0,
                "explicit_percentage": 0,
                "avg_popularity": 0,
                "avg_duration_ms": 0,
                "total_duration_ms": 0,
                "artists": {},
                "albums": {}
            }
        
        # Basic counts
        track_count = len(self.tracks)
        explicit_count = sum(1 for t in self.tracks if t.get("explicit", False))
        explicit_percentage = (explicit_count / track_count) * 100 if track_count > 0 else 0
        
        # Popularity
        total_popularity = sum(t.get("popularity", 0) for t in self.tracks)
        avg_popularity = total_popularity / track_count if track_count > 0 else 0
        
        # Duration
        total_duration_ms = sum(t.get("duration_ms", 0) for t in self.tracks)
        avg_duration_ms = total_duration_ms / track_count if track_count > 0 else 0
        
        # Artists
        artists = {}
        for track in self.tracks:
            for artist in track.get("artists", []):
                artists[artist] = artists.get(artist, 0) + 1
        
        # Albums
        albums = {}
        for track in self.tracks:
            album = track.get("album", "Unknown")
            albums[album] = albums.get(album, 0) + 1
        
        return {
            "track_count": track_count,
            "explicit_count": explicit_count,
            "explicit_percentage": explicit_percentage,
            "avg_popularity": avg_popularity,
            "avg_duration_ms": avg_duration_ms,
            "total_duration_ms": total_duration_ms,
            "artists": artists,
            "albums": albums
        } 