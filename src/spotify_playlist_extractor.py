#!/usr/bin/env python3
"""
Spotify Playlist Link Extractor
A tool to extract track information and links from Spotify playlists.
"""

import argparse
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import sys
import os
import re
import json
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
from tqdm import tqdm
import time
import logging
from typing import Dict, List, Optional, Union, Tuple
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/spotify_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SpotifyExtractorError(Exception):
    """Custom exception class for Spotify Playlist Extractor errors."""
    def __init__(self, message: str, error_type: str = "general", original_error: Optional[Exception] = None):
        self.message = message
        self.error_type = error_type
        self.original_error = original_error
        super().__init__(self.message)

# Load environment variables from .env file
try:
    load_dotenv()
except Exception as e:
    raise SpotifyExtractorError(
        "Failed to load environment variables", 
        "env_error", 
        e
    )

def validate_spotify_url(url: str) -> str:
    """Validate and extract playlist ID from Spotify URL."""
    try:
        if not url:
            raise SpotifyExtractorError(
                "Playlist URL cannot be empty",
                "validation_error"
            )
        
        # Check if it's a valid Spotify URL
        parsed = urlparse(url)
        if parsed.netloc not in ['open.spotify.com', 'spotify.com']:
            raise SpotifyExtractorError(
                "Not a valid Spotify URL. URL must be from open.spotify.com or spotify.com",
                "validation_error"
            )
        
        # Extract playlist ID using regex
        pattern = r'playlist/([a-zA-Z0-9]+)'
        match = re.search(pattern, url)
        if not match:
            raise SpotifyExtractorError(
                "Could not find playlist ID in URL. Make sure it's a valid Spotify playlist URL",
                "validation_error"
            )
        
        playlist_id = match.group(1)
        
        # Check if this is a Spotify-created playlist (typically starts with 37i9dQ)
        if playlist_id.startswith('37i9dQ'):
            logger.info(f"Detected Spotify-created playlist: {playlist_id}")
        
        return playlist_id
    except SpotifyExtractorError:
        raise
    except Exception as e:
        raise SpotifyExtractorError(
            f"Error validating Spotify URL: {str(e)}",
            "validation_error",
            e
        )

def initialize_spotify() -> spotipy.Spotify:
    """Initialize Spotify client with credentials."""
    try:
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise SpotifyExtractorError(
                "Missing Spotify credentials. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file",
                "auth_error"
            )
        
        logger.info(f"Using Client ID: {client_id[:5]}...")
            
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        return spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    except SpotifyExtractorError:
        raise
    except spotipy.oauth2.SpotifyOauthError as e:
        raise SpotifyExtractorError(
            "Failed to authenticate with Spotify. Please check your credentials",
            "auth_error",
            e
        )
    except Exception as e:
        raise SpotifyExtractorError(
            f"Error initializing Spotify client: {str(e)}",
            "initialization_error",
            e
        )

def get_playlist_metadata(sp: spotipy.Spotify, playlist_id: str) -> Dict:
    """Get playlist metadata including name, description, and owner."""
    try:
        # For Spotify-created playlists, try with different markets
        is_spotify_playlist = playlist_id.startswith('37i9dQ')
        
        if is_spotify_playlist:
            # Try with specific markets that might work better with Spotify's playlists
            markets = ['US', 'GB', 'DE', 'FR', None]
            
            for market in markets:
                try:
                    logger.info(f"Trying to fetch Spotify playlist with market: {market or 'default'}")
                    playlist = sp.playlist(playlist_id, 
                                         fields='name,description,owner.display_name,tracks.total,followers.total,public',
                                         market=market)
                    return {
                        'name': playlist['name'],
                        'description': playlist.get('description', ''),
                        'owner': playlist['owner']['display_name'],
                        'total_tracks': playlist['tracks']['total'],
                        'followers': playlist.get('followers', {}).get('total', 0),
                        'public': playlist.get('public', True)
                    }
                except spotipy.exceptions.SpotifyException as e:
                    if e.http_status == 404 and market != markets[-1]:
                        # Try next market
                        logger.info(f"Market {market} failed, trying next market")
                        continue
                    # On last market attempt, let the error propagate
                    raise
        else:
            # Regular user playlist - standard approach
            playlist = sp.playlist(playlist_id, fields='name,description,owner.display_name,tracks.total,followers.total,public')
            return {
                'name': playlist['name'],
                'description': playlist.get('description', ''),
                'owner': playlist['owner']['display_name'],
                'total_tracks': playlist['tracks']['total'],
                'followers': playlist.get('followers', {}).get('total', 0),
                'public': playlist.get('public', True)
            }
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            raise SpotifyExtractorError(
                f"Playlist not found: {playlist_id}",
                "not_found_error",
                e
            )
        elif e.http_status == 403:
            raise SpotifyExtractorError(
                "Access denied. The playlist might be private",
                "access_error",
                e
            )
        else:
            raise SpotifyExtractorError(
                f"Error fetching playlist metadata: {str(e)}",
                "api_error",
                e
            )
    except Exception as e:
        raise SpotifyExtractorError(
            f"Unexpected error fetching playlist metadata: {str(e)}",
            "metadata_error",
            e
        )

def format_duration_ms(duration_ms: int) -> str:
    """Convert duration from milliseconds to mm:ss format."""
    try:
        seconds = int(duration_ms / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    except Exception as e:
        logger.warning(f"Error formatting duration: {str(e)}")
        return "0:00"  # Return default duration on error

def get_all_tracks(sp: spotipy.Spotify, playlist_id: str) -> List[Dict]:
    """Get all tracks from a playlist, handling pagination."""
    tracks = []
    offset = 0
    limit = 100  # Maximum allowed by Spotify API
    
    try:
        # Check if this is a Spotify-created playlist
        is_spotify_playlist = playlist_id.startswith('37i9dQ')
        
        # Determine which markets to try
        markets = ['US', 'GB', 'DE', 'FR', None] if is_spotify_playlist else [None]
        market_index = 0
        current_market = markets[market_index]
        
        if is_spotify_playlist:
            logger.info(f"Using market {current_market or 'default'} for Spotify playlist")
        
        # Get total tracks first for progress bar
        try:
            total = sp.playlist_tracks(playlist_id, fields='total', market=current_market)['total']
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 404 and is_spotify_playlist:
                # Try with a different market
                for test_market in markets:
                    try:
                        total = sp.playlist_tracks(playlist_id, fields='total', market=test_market)['total']
                        current_market = test_market
                        logger.info(f"Successfully found playlist with market: {current_market or 'default'}")
                        break
                    except spotipy.exceptions.SpotifyException:
                        continue
                else:
                    # No market worked
                    raise SpotifyExtractorError(
                        f"Could not access playlist {playlist_id} with any market setting",
                        "not_found_error"
                    )
            else:
                raise
        
        with tqdm(total=total, desc="Fetching tracks", unit="track") as pbar:
            while True:
                try:
                    results = sp.playlist_tracks(
                        playlist_id,
                        offset=offset,
                        limit=limit,
                        market=current_market,
                        fields='items(added_at,track(id,name,external_urls.spotify,artists(name,id),album(name,release_date,total_tracks),duration_ms,preview_url,popularity,explicit,track_number,disc_number,is_local)),total'
                    )
                    
                    if not results['items']:
                        break
                        
                    for item in results['items']:
                        track = item['track']
                        if track and not track.get('is_local', False):  # Skip local files and None tracks
                            try:
                                # Generate share URL with si parameter
                                share_url = f"{track['external_urls']['spotify']}?si={track['id']}"
                                
                                track_data = {
                                    'name': track['name'],
                                    'artists': [{'name': artist['name'], 'id': artist['id']} for artist in track['artists']],
                                    'artist_names': [artist['name'] for artist in track['artists']],
                                    'album': {
                                        'name': track['album']['name'],
                                        'release_date': track['album'].get('release_date', 'Unknown'),
                                        'total_tracks': track['album'].get('total_tracks', 0)
                                    },
                                    'duration': format_duration_ms(track['duration_ms']),
                                    'duration_ms': track['duration_ms'],
                                    'url': share_url,
                                    'preview_url': track.get('preview_url'),
                                    'popularity': track.get('popularity', 0),
                                    'explicit': track.get('explicit', False),
                                    'track_number': track.get('track_number', 0),
                                    'disc_number': track.get('disc_number', 1),
                                    'added_at': item.get('added_at', None)
                                }
                                tracks.append(track_data)
                                pbar.update(1)
                            except KeyError as ke:
                                logger.warning(f"\nWarning: Missing data for track '{track.get('name', 'Unknown')}': {ke}")
                                continue  # Skip tracks with missing critical data
                            except Exception as e:
                                logger.warning(f"\nWarning: Error processing track '{track.get('name', 'Unknown')}': {str(e)}")
                                continue
                    
                    if len(tracks) >= results['total']:
                        break
                        
                    offset += limit
                    
                except spotipy.exceptions.SpotifyException as e:
                    if e.http_status == 429:  # Rate limiting
                        retry_after = int(e.headers.get('Retry-After', 1))
                        logger.info(f"\nRate limited. Waiting {retry_after} seconds...")
                        time.sleep(retry_after)
                        continue
                    elif e.http_status == 404 and is_spotify_playlist and market_index < len(markets) - 1:
                        # Try with a different market
                        market_index += 1
                        current_market = markets[market_index]
                        logger.info(f"\nSwitching to market: {current_market or 'default'}")
                        continue
                    raise SpotifyExtractorError(
                        f"Error fetching tracks: {str(e)}",
                        "api_error",
                        e
                    )
                
        if not tracks:
            raise SpotifyExtractorError(
                "No valid tracks found in playlist",
                "empty_playlist_error"
            )
            
        # Sort tracks by their position in the playlist
        tracks.sort(key=lambda x: (x.get('disc_number', 1), x.get('track_number', 0)))
        return tracks
        
    except SpotifyExtractorError:
        raise
    except Exception as e:
        raise SpotifyExtractorError(
            f"Error fetching tracks: {str(e)}",
            "track_error",
            e
        )

def save_json_data(data: Dict, output_file: str) -> None:
    """Save data to a JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise SpotifyExtractorError(
            f"Failed to save JSON data to {output_file}: {str(e)}",
            "file_error",
            e
        )

def save_track_list(tracks: List[Dict], output_file: str) -> None:
    """Save detailed track information to a text file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for track in tracks:
                f.write(f"Track: {track['name']}\n")
                f.write(f"Artist(s): {', '.join(track['artist_names'])}\n")
                f.write(f"Album: {track['album']['name']} ({track['album']['release_date']})\n")
                f.write(f"Duration: {track['duration']} | Popularity: {track['popularity']}/100\n")
                f.write(f"Track {track['track_number']} of {track['album']['total_tracks']}\n")
                f.write(f"Added to playlist: {track['added_at']}\n")
                f.write(f"URL: {track['url']}\n\n")
    except Exception as e:
        raise SpotifyExtractorError(
            f"Failed to save track list to {output_file}: {str(e)}",
            "file_error",
            e
        )

def save_track_links(tracks: List[Dict], output_file: str) -> None:
    """Save track URLs to a text file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(' '.join(track['url'] for track in tracks))
    except Exception as e:
        raise SpotifyExtractorError(
            f"Failed to save track links to {output_file}: {str(e)}",
            "file_error",
            e
        )

def save_track_analytics(tracks: List[Dict], output_file: str) -> None:
    """Save analytics about the tracks to a file."""
    try:
        # Calculate analytics
        total_tracks = len(tracks)
        total_duration_ms = sum(track['duration_ms'] for track in tracks)
        total_duration_min = total_duration_ms / (1000 * 60)
        
        # Popularity analysis
        popularity_scores = [track['popularity'] for track in tracks]
        avg_popularity = sum(popularity_scores) / total_tracks if total_tracks > 0 else 0
        
        underground_tracks = [t for t in tracks if t['popularity'] <= 20]
        rising_tracks = [t for t in tracks if 20 < t['popularity'] <= 40]
        
        # Timeline analysis
        years = [int(track['album']['release_date'][:4]) for track in tracks if track['album']['release_date']]
        year_distribution = {}
        if years:
            for year in years:
                year_distribution[year] = year_distribution.get(year, 0) + 1
        
        # Write analytics
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Playlist Analytics\n")
            f.write("=================\n\n")
            
            f.write(f"Total Tracks: {total_tracks}\n")
            f.write(f"Total Duration: {total_duration_min:.1f} minutes\n")
            f.write(f"Average Popularity: {avg_popularity:.1f}/100\n\n")
            
            # Add sorted track list by popularity
            f.write("All Tracks Sorted by Popularity:\n")
            f.write("-------------------------------\n")
            sorted_tracks = sorted(tracks, key=lambda x: x['popularity'])
            for track in sorted_tracks:
                artists = ', '.join(track['artist_names'])
                f.write(f"[{track['popularity']:>3}/100] {track['name']} by {artists}\n")
                f.write(f"         Added: {track['added_at']}\n")
                f.write(f"         Album: {track['album']['name']} ({track['album']['release_date']})\n")
                f.write(f"         URL: {track['url']}\n\n")
            f.write("\n")
            
            f.write("Underground Tracks (Popularity ≤ 20):\n")
            for track in underground_tracks:
                f.write(f"- {track['name']} by {', '.join(track['artist_names'])} ({track['popularity']}/100)\n")
            f.write(f"Total: {len(underground_tracks)} tracks\n\n")
            
            f.write("Rising Tracks (Popularity 21-40):\n")
            for track in rising_tracks:
                f.write(f"- {track['name']} by {', '.join(track['artist_names'])} ({track['popularity']}/100)\n")
            f.write(f"Total: {len(rising_tracks)} tracks\n\n")
            
            if year_distribution:
                f.write("Timeline Analysis:\n")
                for year in sorted(year_distribution.keys()):
                    f.write(f"{year}: {year_distribution[year]} tracks\n")
    except Exception as e:
        raise SpotifyExtractorError(
            f"Failed to save analytics to {output_file}: {str(e)}",
            "file_error",
            e
        )

def check_directory_writable(directory: str) -> None:
    """Check if the directory exists and is writable."""
    try:
        # Check if path is a valid Windows path
        if sys.platform == 'win32':
            import win32file
            import win32api
            try:
                # Try to get the drive type
                drive = os.path.splitdrive(directory)[0] + '\\'
                drive_type = win32file.GetDriveType(drive)
                if drive_type == win32file.DRIVE_NO_ROOT_DIR:
                    raise SpotifyExtractorError(
                        f"Drive {drive} does not exist",
                        "path_error"
                    )
            except Exception as e:
                if not isinstance(e, SpotifyExtractorError):
                    raise SpotifyExtractorError(
                        f"Invalid drive or path: {str(e)}",
                        "path_error",
                        e
                    )
                raise
        
        # Check if directory exists
        if not os.path.exists(directory):
            raise SpotifyExtractorError(
                f"Directory {directory} does not exist",
                "path_error"
            )
        
        # Check if it's actually a directory
        if not os.path.isdir(directory):
            raise SpotifyExtractorError(
                f"{directory} exists but is not a directory",
                "path_error"
            )
        
        # Try to create a temporary file to verify write permissions
        test_file = os.path.join(directory, '.write_test')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except (IOError, OSError) as e:
            raise SpotifyExtractorError(
                f"Directory {directory} is not writable: {str(e)}",
                "permission_error",
                e
            )
            
    except SpotifyExtractorError:
        raise
    except Exception as e:
        raise SpotifyExtractorError(
            f"Failed to verify write permissions for {directory}: {str(e)}",
            "permission_error",
            e
        )

def normalize_path(path: str) -> str:
    """Normalize a file path for the current operating system."""
    try:
        # Convert to absolute path first
        abs_path = os.path.abspath(path)
        
        # On Windows, check for invalid characters and convert slashes
        if sys.platform == 'win32':
            # Convert forward slashes to backslashes
            abs_path = abs_path.replace('/', '\\')
            
            # Check path length (Windows MAX_PATH is 260 by default)
            if len(abs_path) > 260:
                raise SpotifyExtractorError(
                    f"Path exceeds maximum length of 260 characters: {abs_path}",
                    "path_error"
                )
            
            # Check for invalid characters in the path part (after drive letter)
            drive, path_part = os.path.splitdrive(abs_path)
            invalid_chars = '<>"|?*'
            if any(char in path_part for char in invalid_chars):
                raise SpotifyExtractorError(
                    f"Path contains invalid characters: {invalid_chars}",
                    "path_error"
                )
        
        return abs_path
        
    except SpotifyExtractorError:
        raise
    except Exception as e:
        raise SpotifyExtractorError(
            f"Failed to normalize path {path}: {str(e)}",
            "path_error",
            e
        )

def create_output_dir(output_dir: str) -> None:
    """Create output directory if it doesn't exist and verify it's writable."""
    try:
        # Normalize the path
        output_dir = normalize_path(output_dir)
        
        # First try to create the directory
        try:
            os.makedirs(output_dir, exist_ok=True)
        except (IOError, OSError) as e:
            raise SpotifyExtractorError(
                f"Failed to create directory {output_dir}: {str(e)}",
                "file_error",
                e
            )
        
        # Then verify we can write to it
        check_directory_writable(output_dir)
        
    except SpotifyExtractorError:
        raise
    except Exception as e:
        raise SpotifyExtractorError(
            f"Failed to create or verify output directory {output_dir}: {str(e)}",
            "file_error",
            e
        )

def get_safe_filename(metadata: Dict, include_artist: bool = False) -> str:
    """Generate a safe filename from playlist metadata."""
    try:
        # Remove invalid characters and trim
        safe_name = re.sub(r'[^\w\s-]', '', metadata['name']).strip().replace(' ', '_')
        
        if include_artist:
            # Add owner name to filename
            safe_owner = re.sub(r'[^\w\s-]', '', metadata['owner']).strip().replace(' ', '_')
            return f"{safe_name}_by_{safe_owner}"
        
        return safe_name
    except Exception as e:
        logger.warning(f"Error generating safe filename: {str(e)}")
        return "playlist"  # Fallback name

def process_playlist(sp: spotipy.Spotify, url: str, output_dir: str, 
                    include_artist: bool = False, no_playlist_folders: bool = False) -> Tuple[str, str, str]:
    """Process a single playlist.
    
    Args:
        sp: Spotify client instance
        url: URL of the playlist to process
        output_dir: Base output directory
        include_artist: Whether to include the artist name in filenames
        no_playlist_folders: Whether to disable playlist-specific folders
        
    Returns:
        Tuple containing (playlist_output_dir, safe_name, playlist_id)
        
    Raises:
        SpotifyExtractorError: If processing fails
    """
    try:
        # Normalize the output directory path
        output_dir = normalize_path(output_dir)
        
        # Extract playlist ID
        playlist_id = validate_spotify_url(url)
        
        # Get playlist metadata
        metadata = get_playlist_metadata(sp, playlist_id)
        logger.info(f"\nProcessing playlist: {metadata['name']}")
        logger.info(f"Created by: {metadata['owner']}")
        logger.info(f"Total tracks: {metadata['total_tracks']}")
        
        # Get all tracks
        tracks = get_all_tracks(sp, playlist_id)
        
        # Generate safe filename base
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = get_safe_filename(metadata, include_artist)
        base_filename = f"{safe_name}_{timestamp}" if not include_artist else safe_name
        
        # Determine output directory
        playlist_output_dir = output_dir
        if not no_playlist_folders:
            # Create a playlist-specific output directory
            playlist_output_dir = os.path.join(output_dir, safe_name)
            try:
                os.makedirs(playlist_output_dir, exist_ok=True)
                # Verify we can write to it
                check_directory_writable(playlist_output_dir)
            except Exception as e:
                logger.warning(f"Could not create playlist-specific directory: {str(e)}")
                logger.warning(f"Using main output directory instead")
                playlist_output_dir = output_dir
        
        try:
            # Verify output directory is still writable
            check_directory_writable(playlist_output_dir)
            
            # Create Downloads folder inside the playlist directory
            downloads_dir = os.path.join(playlist_output_dir, "Downloads")
            try:
                os.makedirs(downloads_dir, exist_ok=True)
                logger.info(f"Created Downloads directory: {downloads_dir}")
            except Exception as e:
                logger.warning(f"Could not create Downloads directory: {str(e)}")
            
            # Save data to files
            json_file = os.path.join(playlist_output_dir, f"{base_filename}.json")
            save_json_data({'metadata': metadata, 'tracks': tracks}, json_file)
            logger.info(f"\nPlaylist data saved to: {json_file}")
            
            tracks_file = os.path.join(playlist_output_dir, f"{safe_name}_tracks.txt")
            save_track_list(tracks, tracks_file)
            logger.info(f"Track list saved to: {tracks_file}")
            
            links_file = os.path.join(playlist_output_dir, f"{safe_name}_links.txt")
            save_track_links(tracks, links_file)
            logger.info(f"Track links saved to: {links_file}")
            
            analytics_file = os.path.join(playlist_output_dir, f"{safe_name}_analytics.txt")
            save_track_analytics(tracks, analytics_file)
            logger.info(f"Analytics saved to: {analytics_file}")
            
            # Save metadata reference in main output directory for later access
            metadata_ref = {
                'id': playlist_id,
                'name': metadata['name'],
                'owner': metadata['owner'],
                'folder': safe_name,
                'processed_at': timestamp,
                'files': {
                    'json': json_file,
                    'tracks': tracks_file,
                    'links': links_file,
                    'analytics': analytics_file,
                    'downloads_dir': downloads_dir
                }
            }
            metadata_ref_file = os.path.join(output_dir, f"{safe_name}_ref.json")
            save_json_data(metadata_ref, metadata_ref_file)
            
            # Display preview
            display_playlist_preview(metadata, tracks)
            
            # Generate individual hidden gems report if requested
            if hasattr(args, 'hidden_gems') and args.hidden_gems and not args.combined_analysis:
                gems_file, playlist_urls_file = generate_hidden_gems_report(playlist_output_dir, tracks, 
                                                                          getattr(args, 'min_pop', 0),
                                                                          getattr(args, 'max_pop', 40),
                                                                          getattr(args, 'min_score', 20),
                                                                          getattr(args, 'top_gems', 30),
                                                                          playlist_name=metadata['name'])
                logger.info(f"Hidden gems report saved to: {gems_file}")
            
            return playlist_output_dir, safe_name, playlist_id
            
        except SpotifyExtractorError as e:
            logger.error(f"Failed to save files for playlist {metadata['name']}")
            logger.error(f"Error Type: {e.error_type}")
            logger.error(f"Error Message: {str(e)}")
            raise
            
    except SpotifyExtractorError as e:
        logger.error(f"Error processing playlist {url}")
        logger.error(f"Error Type: {e.error_type}")
        logger.error(f"Error Message: {str(e)}")
        raise

def display_playlist_preview(metadata: Dict, tracks: List[Dict]) -> None:
    """Display a preview of the playlist information."""
    try:
        logger.info("\nPlaylist Information:")
        logger.info(f"Name: {metadata['name']}")
        logger.info(f"Owner: {metadata['owner']}")
        logger.info(f"Total tracks: {len(tracks)}")
        logger.info(f"Followers: {metadata.get('followers', 0)}")
        logger.info(f"Visibility: {'Public' if metadata.get('public', True) else 'Private'}")
        
        logger.info("\nFirst 5 tracks:")
        for i, track in enumerate(tracks[:5], 1):
            logger.info(f"{i}. {track['name']}")
            logger.info(f"   by {', '.join(track['artist_names'])}")
            logger.info(f"   Album: {track['album']['name']} ({track['album']['release_date']})")
            logger.info(f"   Duration: {track['duration']} | Popularity: {track['popularity']}/100")
            logger.info(f"   Track {track['track_number']} of {track['album']['total_tracks']}")
            logger.info(f"   Added to playlist: {track['added_at']}")
            logger.info(f"   URL: {track['url']}\n")
    except Exception as e:
        logger.error(f"Error displaying playlist preview: {str(e)}")
        # Don't raise an error here as this is just a display function

def setup_logging(output_dir: str) -> None:
    """Configure logging with both file and console handlers."""
    try:
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Console handler with UTF-8 encoding
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = os.path.join(output_dir, 'spotify_extractor.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        
    except Exception as e:
        raise SpotifyExtractorError(
            f"Failed to setup logging: {str(e)}",
            "logging_error",
            e
        )

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Extract track information from Spotify playlists and find hidden gems.')
    
    # Input options
    input_group = parser.add_argument_group('Input Options')
    input_group.add_argument('urls', nargs='*', help='One or more Spotify playlist URLs')
    input_group.add_argument('-f', '--file', help='Text file containing Spotify playlist URLs (one per line)')
    input_group.add_argument('--batch-size', type=int, default=5,
                          help='Number of playlists to process simultaneously (default: 5)')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('-o', '--output-dir', default='output',
                          help='Output directory for generated files (default: output)')
    output_group.add_argument('-a', '--include-artist', action='store_true',
                          help='Include playlist owner name in output filenames')
    output_group.add_argument('--combined-analysis', action='store_true',
                          help='Generate a combined analysis file for all processed playlists')
    output_group.add_argument('--no-playlist-folders', action='store_true',
                          help='Do not create separate folders for each playlist')
    
    # Processing options
    process_group = parser.add_argument_group('Processing Options')
    process_group.add_argument('--retry-failed', action='store_true',
                           help='Retry failed playlist downloads')
    process_group.add_argument('--retry-limit', type=int, default=3,
                           help='Maximum number of retries for failed playlists (default: 3)')
    process_group.add_argument('--skip-existing', action='store_true',
                           help='Skip playlists that have already been processed')
    
    # Hidden Gems options
    gems_group = parser.add_argument_group('Hidden Gems Options')
    gems_group.add_argument('--hidden-gems', action='store_true',
                        help='Generate a hidden gems report (automatically enabled with --combined-analysis)')
    gems_group.add_argument('--min-pop', type=int, default=0,
                        help='Minimum popularity score for hidden gems consideration (default: 0)')
    gems_group.add_argument('--max-pop', type=int, default=40,
                        help='Maximum popularity score for hidden gems consideration (default: 40)')
    gems_group.add_argument('--min-score', type=int, default=20,
                        help='Minimum gem score to include in the report (default: 20)')
    gems_group.add_argument('--top-gems', type=int, default=30,
                        help='Number of top gems to include in the playlist creation section (default: 30)')
    
    # Spotify Integration options
    spotify_group = parser.add_argument_group('Spotify Integration')
    spotify_group.add_argument('--create-playlist', action='store_true',
                            help='Create a new Spotify playlist from hidden gems (requires user authorization)')
    spotify_group.add_argument('--playlist-name', type=str, default="Hidden Gems",
                            help='Name for the created Spotify playlist (default: "Hidden Gems")')
    spotify_group.add_argument('--playlist-description', type=str,
                            default="Discovered gems from playlists analyzed by Spotify Playlist Extractor",
                            help='Description for the created Spotify playlist')
    spotify_group.add_argument('--playlist-public', action='store_true',
                            help='Make the created playlist public (default is private)')
    spotify_group.add_argument('--urls-file', type=str,
                            help='Use a specific URLs file to create a playlist instead of generating a new one')
    
    return parser.parse_args()

def read_playlist_urls(file_path: str) -> List[str]:
    """Read playlist URLs from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read lines and clean them
            urls = [line.strip() for line in f if line.strip()]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            if not unique_urls:
                raise SpotifyExtractorError(
                    f"No valid URLs found in {file_path}",
                    "validation_error"
                )
            
            return unique_urls
    except FileNotFoundError:
        raise SpotifyExtractorError(
            f"Playlist URL file not found: {file_path}",
            "file_error"
        )
    except Exception as e:
        raise SpotifyExtractorError(
            f"Error reading playlist URLs from {file_path}: {str(e)}",
            "file_error",
            e
        )

def get_playlist_cache_path(output_dir: str, playlist_id: str) -> str:
    """Get the path to the most recent cache file for a playlist."""
    try:
        # First check for reference file
        ref_pattern = os.path.join(output_dir, "*_ref.json")
        for ref_file in glob.glob(ref_pattern):
            try:
                with open(ref_file, 'r', encoding='utf-8') as f:
                    ref_data = json.load(f)
                    if ref_data.get('id') == playlist_id:
                        json_file = ref_data.get('files', {}).get('json', '')
                        if json_file and os.path.exists(json_file):
                            return json_file
            except Exception:
                continue
        
        # Fall back to direct search
        pattern = os.path.join(output_dir, "**", f"*{playlist_id}*.json")
        files = glob.glob(pattern, recursive=True)
        if files:
            return max(files, key=os.path.getctime)
            
        # Final fallback - search in all subdirectories
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.json') and playlist_id in file:
                    return os.path.join(root, file)
                    
    except Exception as e:
        logger.warning(f"Error finding cache for playlist {playlist_id}: {str(e)}")
    return ""

def is_playlist_cached(output_dir: str, playlist_id: str) -> bool:
    """Check if a playlist has been processed before."""
    cache_path = get_playlist_cache_path(output_dir, playlist_id)
    return os.path.exists(cache_path)

def save_playlist_to_cache(output_dir: str, playlist_id: str, metadata: Dict, tracks: List[Dict]) -> None:
    """Save playlist data to cache."""
    try:
        cache_path = get_playlist_cache_path(output_dir, playlist_id)
        cache_data = {
            'metadata': metadata,
            'tracks': tracks,
            'processed_at': datetime.now().isoformat()
        }
        save_json_data(cache_data, cache_path)
    except Exception as e:
        logger.warning(f"Failed to cache playlist {playlist_id}: {str(e)}")
        # Don't raise error as this is non-critical

def process_playlists(sp: spotipy.Spotify, urls: List[str], args: argparse.Namespace) -> None:
    """Process multiple playlists with advanced handling.
    
    Args:
        sp: Spotify client instance
        urls: List of playlist URLs to process
        args: Command-line arguments
    """
    total_playlists = len(urls)
    failed_playlists = []
    processed_playlists = []
    skipped_playlists = []
    playlist_folders = {}  # Map playlist IDs to their folder names
    playlist_urls_files = {}  # Store generated playlist URL files for later use
    
    logger.info(f"\nProcessing {total_playlists} playlist{'s' if total_playlists > 1 else ''}")
    
    for i, url in enumerate(urls, 1):
        try:
            # Extract playlist ID for cache checking
            playlist_id = validate_spotify_url(url)
            
            # Check cache if skip_existing is enabled
            if args.skip_existing and is_playlist_cached(args.output_dir, playlist_id):
                logger.info(f"\nSkipping previously processed playlist: {url}")
                skipped_playlists.append(url)
                continue
            
            logger.info(f"\nProcessing playlist {i} of {total_playlists}: {url}")
            result = process_playlist(sp, url, args.output_dir, args.include_artist, 
                                    getattr(args, 'no_playlist_folders', False))
            
            if result:
                # Unpack result if it returned values
                playlist_output_dir, safe_name, playlist_id = result
                # Store folder mapping for combined analysis
                playlist_folders[playlist_id] = safe_name
            
            processed_playlists.append(url)
            
        except SpotifyExtractorError as e:
            logger.error(f"Failed to process playlist {url}")
            logger.error(f"Error Type: {e.error_type}")
            logger.error(f"Error Message: {str(e)}")
            failed_playlists.append((url, str(e)))
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing playlist {url}: {str(e)}")
            failed_playlists.append((url, str(e)))
            continue
    
    # Handle retries if enabled
    if args.retry_failed and failed_playlists:
        retry_playlists(sp, failed_playlists, args, playlist_folders)
    
    # Generate combined analysis if requested
    if args.combined_analysis and processed_playlists:
        try:
            generate_combined_analysis(args.output_dir, processed_playlists, playlist_folders)
        except Exception as e:
            logger.error(f"Failed to generate combined analysis: {str(e)}")
    # Generate hidden gems report if requested and not already done via combined analysis
    elif args.hidden_gems and processed_playlists:
        try:
            # We need to collect all tracks from processed playlists
            all_tracks = []
            playlist_name = None
            playlist_output_dir = args.output_dir
            
            if len(processed_playlists) == 1:
                # If only one playlist, get its name and output dir
                url = processed_playlists[0]
                playlist_id = validate_spotify_url(url)
                playlist_folder = playlist_folders.get(playlist_id)
                
                # Find the JSON file to get the metadata
                json_file = get_playlist_cache_path(args.output_dir, playlist_id)
                if json_file and os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'metadata' in data:
                            playlist_name = data['metadata'].get('name')
                
                if playlist_folder and not args.no_playlist_folders:
                    playlist_output_dir = os.path.join(args.output_dir, playlist_folder)
            
            # Collect tracks from all processed playlists
            for url in processed_playlists:
                playlist_id = validate_spotify_url(url)
                
                json_file = get_playlist_cache_path(args.output_dir, playlist_id)
                if json_file and os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'tracks' in data:
                            all_tracks.extend(data['tracks'])
            
            if all_tracks:
                gems_file, urls_file = generate_hidden_gems_report(
                    playlist_output_dir, all_tracks, 
                    args.min_pop, args.max_pop, args.min_score, args.top_gems,
                    playlist_name=playlist_name
                )
                logger.info(f"Hidden gems report saved to: {gems_file}")
                
                # Store the URLs file for possible playlist creation
                if playlist_name:
                    playlist_urls_files[playlist_name] = urls_file
                else:
                    playlist_urls_files["combined"] = urls_file
            else:
                logger.error("No tracks found for hidden gems analysis")
                
        except Exception as e:
            logger.error(f"Failed to generate hidden gems report: {str(e)}")
    
    # Create playlist if requested and we have URLs files
    if getattr(args, 'create_playlist', False) and not args.combined_analysis:
        try:
            # Use user-specified file or find the appropriate one
            urls_file = getattr(args, 'urls_file', None)
            
            if not urls_file and playlist_urls_files:
                # If only one playlist was processed, use its URLs file
                if len(playlist_urls_files) == 1:
                    _, urls_file = list(playlist_urls_files.items())[0]
                else:
                    # Otherwise use the combined one if available
                    urls_file = playlist_urls_files.get("combined")
            
            if urls_file and os.path.exists(urls_file):
                # Set up OAuth for user authorization
                scope = "playlist-modify-private"
                if getattr(args, 'playlist_public', False):
                    scope += " playlist-modify-public"
                
                sp_oauth = spotipy.oauth2.SpotifyOAuth(
                    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
                    redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback'),
                    scope=scope
                )
                
                # Create the playlist
                playlist_url = create_spotify_playlist(
                    sp_oauth=sp_oauth,
                    urls_file=urls_file,
                    playlist_name=getattr(args, 'playlist_name', "Hidden Gems"),
                    description=getattr(args, 'playlist_description', 
                                      "Discovered gems from playlists analyzed by Spotify Playlist Extractor"),
                    public=getattr(args, 'playlist_public', False)
                )
                
                logger.info(f"Created Spotify playlist: {playlist_url}")
            else:
                logger.error("No URLs file found for playlist creation")
        
        except Exception as e:
            logger.error(f"Failed to create Spotify playlist: {str(e)}")
    
    # Display final summary
    display_processing_summary(total_playlists, processed_playlists, failed_playlists, skipped_playlists)

def retry_playlists(sp: spotipy.Spotify, failed_playlists: List[Tuple[str, str]], args: argparse.Namespace, 
                    playlist_folders: Dict[str, str] = None) -> None:
    """Retry processing failed playlists."""
    logger.info("\nRetrying failed playlists...")
    
    for url, original_error in failed_playlists[:]:  # Work on a copy of the list
        for attempt in range(args.retry_limit):
            try:
                logger.info(f"\nRetrying playlist {url} (Attempt {attempt + 1}/{args.retry_limit})")
                result = process_playlist(sp, url, args.output_dir, args.include_artist, 
                                        getattr(args, 'no_playlist_folders', False))
                
                if result and playlist_folders is not None:
                    # Store folder mapping if result was returned
                    _, safe_name, playlist_id = result
                    playlist_folders[playlist_id] = safe_name
                
                failed_playlists.remove((url, original_error))
                break
            except Exception as e:
                logger.error(f"Retry attempt {attempt + 1} failed: {str(e)}")
                if attempt == args.retry_limit - 1:
                    logger.error(f"All retry attempts failed for {url}")

def display_processing_summary(total: int, processed: List[str], failed: List[Tuple[str, str]], skipped: List[str]) -> None:
    """Display a summary of the playlist processing results."""
    logger.info("\nProcessing Summary:")
    logger.info(f"Total Playlists: {total}")
    logger.info(f"Successfully Processed: {len(processed)}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Skipped (Previously Processed): {len(skipped)}")
    
    if failed:
        logger.info("\nFailed Playlists:")
        for url, error in failed:
            logger.info(f"- {url}")
            logger.info(f"  Error: {error}")

def generate_hidden_gems_report(output_dir: str, all_tracks: List[Dict], 
                               min_pop: int = 0, max_pop: int = 40, 
                               min_score: int = 20, top_gems: int = 30,
                               playlist_name: str = "") -> Tuple[str, str]:
    """Generate a detailed hidden gems report with advanced scoring.
    
    Args:
        output_dir: Directory to save the report
        all_tracks: List of track data dictionaries
        min_pop: Minimum popularity score to consider (0-100)
        max_pop: Maximum popularity score to consider (0-100)
        min_score: Minimum gem score to include in report (0-50)
        top_gems: Number of top gems to include in playlist creation section
        playlist_name: Optional name of the playlist for the report title
        
    Returns:
        Tuple containing paths to (gems_file, playlist_urls_file)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_prefix = f"{playlist_name}_" if playlist_name else ""
    gems_file = os.path.join(output_dir, f"{file_prefix}hidden_gems_{timestamp}.txt")
    
    # Score tracks based on criteria
    scored_tracks = []
    
    for track in all_tracks:
        score = 0
        score_components = []
        
        # Base Popularity Score (0-20 points)
        pop = track['popularity']
        if min_pop <= pop <= 20:
            pop_score = 20
            score_components.append(f"Low popularity (0-20): +20 points")
        elif 21 <= pop <= max_pop:
            pop_score = 15
            score_components.append(f"Rising popularity (21-40): +15 points")
        else:
            pop_score = 0
        score += pop_score
        
        # Artist Collaboration (0-10 points)
        if len(track['artists']) > 1:
            score += 10
            score_components.append(f"Artist collaboration ({len(track['artists'])} artists): +10 points")
        
        # Track Duration (0-10 points)
        duration_min = track['duration_ms'] / (1000 * 60)
        if 5 <= duration_min <= 9:
            score += 10
            score_components.append(f"Extended track length ({duration_min:.1f} minutes): +10 points")
        
        # Album tracks analysis (0-10 points)
        album_type = track['album'].get('album_type', '').lower()
        total_tracks = track['album'].get('total_tracks', 0)
        if album_type in ('single', 'ep') and 1 <= total_tracks <= 4:
            score += 10
            score_components.append(f"Focus release ({album_type.upper()}, {total_tracks} tracks): +10 points")
        
        # Add to scored tracks with detailed scoring breakdown
        track_info = {
            'track': track,
            'score': score,
            'score_components': score_components,
            'popularity': pop
        }
        scored_tracks.append(track_info)
    
    # Filter and sort tracks
    potential_gems = [t for t in scored_tracks if t['score'] >= min_score]
    potential_gems.sort(key=lambda x: (-x['score'], x['popularity']))
    
    # Calculate statistics
    total_analyzed = len(all_tracks)
    gems_found = len(potential_gems)
    avg_score = sum(t['score'] for t in potential_gems) / gems_found if gems_found > 0 else 0
    
    # Group by score categories
    elite_gems = [t for t in potential_gems if t['score'] >= 40]  # 40+ points
    quality_gems = [t for t in potential_gems if 30 <= t['score'] < 40]  # 30-39 points
    standard_gems = [t for t in potential_gems if 20 <= t['score'] < 30]  # 20-29 points
    
    # Group by popularity brackets
    ultra_underground = [t for t in scored_tracks if min_pop <= t['popularity'] <= 10 and t['score'] >= min_score]
    deep_underground = [t for t in scored_tracks if 11 <= t['popularity'] <= 20 and t['score'] >= min_score]
    rising_underground = [t for t in scored_tracks if 21 <= t['popularity'] <= max_pop and t['score'] >= min_score]
    
    # Get top gems for playlist
    playlist_gems = sorted(scored_tracks, key=lambda x: (-x['score'], x['popularity']))[:top_gems]
    
    # Create playlist URLs file for easy creation
    playlist_urls_file = os.path.join(output_dir, f"{file_prefix}hidden_gems_playlist_urls_{timestamp}.txt")
    with open(playlist_urls_file, 'w', encoding='utf-8') as f:
        for gem in playlist_gems:
            f.write(f"{gem['track']['url']}\n")
    
    # Write the report
    with open(gems_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("💎 HIDDEN GEMS ANALYSIS 💎\n")
        f.write("==========================\n\n")
        
        if playlist_name:
            f.write(f"Playlist: {playlist_name}\n")
            f.write("-" * (len("Playlist: ") + len(playlist_name)) + "\n\n")
        
        # Statistics Section
        f.write("📊 ANALYSIS STATISTICS\n")
        f.write("---------------------\n")
        f.write(f"Total Tracks Analyzed: {total_analyzed}\n")
        f.write(f"Hidden Gems Found: {gems_found} ({(gems_found/total_analyzed)*100:.1f}% of tracks)\n")
        f.write(f"Average Gem Score: {avg_score:.1f} / 50\n")
        f.write(f"Elite Gems (40+ points): {len(elite_gems)}\n")
        f.write(f"Quality Gems (30-39 points): {len(quality_gems)}\n")
        f.write(f"Standard Gems (20-29 points): {len(standard_gems)}\n\n")
        
        # Top Gems Section
        f.write("🏆 TOP HIDDEN GEMS\n")
        f.write("----------------\n")
        top_gems_list = sorted(scored_tracks, key=lambda x: (-x['score'], x['popularity']))[:15]
        
        for i, gem in enumerate(top_gems_list, 1):
            track = gem['track']
            artists = ', '.join(track['artist_names'])
            f.write(f"{i}. [{gem['score']:>2}/50] {track['name']} by {artists}\n")
            f.write(f"   Popularity: {track['popularity']}/100\n")
            f.write(f"   Album: {track['album']['name']} ({track['album']['release_date']})\n")
            
            # Score breakdown
            f.write(f"   Scoring: {gem['score']} points\n")
            for component in gem['score_components']:
                f.write(f"    - {component}\n")
                
            f.write(f"   URL: {track['url']}\n\n")
        
        # Gems by Category
        f.write("💎 GEMS BY SCORE CATEGORY\n")
        f.write("------------------------\n\n")
        
        # Elite Gems
        f.write("Elite Gems (40+ points):\n")
        if elite_gems:
            for gem in elite_gems:
                track = gem['track']
                artists = ', '.join(track['artist_names'])
                f.write(f"- [{gem['score']:>2}/50] {track['name']} by {artists} (Pop: {track['popularity']})\n")
        else:
            f.write("None found\n")
        f.write("\n")
        
        # Quality Gems
        f.write("Quality Gems (30-39 points):\n")
        if quality_gems:
            for gem in quality_gems:
                track = gem['track']
                artists = ', '.join(track['artist_names'])
                f.write(f"- [{gem['score']:>2}/50] {track['name']} by {artists} (Pop: {track['popularity']})\n")
        else:
            f.write("None found\n")
        f.write("\n")
        
        # By Popularity
        f.write("💿 GEMS BY POPULARITY BRACKET\n")
        f.write("---------------------------\n\n")
        
        # Ultra Underground
        f.write("Ultra Underground (0-10 popularity):\n")
        if ultra_underground:
            for gem in sorted(ultra_underground, key=lambda x: -x['score'])[:20]:
                track = gem['track']
                artists = ', '.join(track['artist_names'])
                f.write(f"- [{gem['score']:>2}/50] {track['name']} by {artists} (Pop: {track['popularity']})\n")
        else:
            f.write("None found\n")
        f.write("\n")
        
        # Deep Underground
        f.write("Deep Underground (11-20 popularity):\n")
        if deep_underground:
            for gem in sorted(deep_underground, key=lambda x: -x['score'])[:20]:
                track = gem['track']
                artists = ', '.join(track['artist_names'])
                f.write(f"- [{gem['score']:>2}/50] {track['name']} by {artists} (Pop: {track['popularity']})\n")
        else:
            f.write("None found\n")
        f.write("\n")
        
        # Rising Underground
        f.write("Rising Underground (21-40 popularity):\n")
        if rising_underground:
            for gem in sorted(rising_underground, key=lambda x: -x['score'])[:20]:
                track = gem['track']
                artists = ', '.join(track['artist_names'])
                f.write(f"- [{gem['score']:>2}/50] {track['name']} by {artists} (Pop: {track['popularity']})\n")
        else:
            f.write("None found\n")
        f.write("\n")
        
        # Playlist Creation Section
        f.write("🎧 PLAYLIST CREATION\n")
        f.write("------------------\n")
        f.write(f"A file with top {top_gems} gem URLs has been created at:\n")
        f.write(f"{playlist_urls_file}\n\n")
        f.write("You can either:\n")
        f.write("1. Copy these URLs manually to create a Hidden Gems playlist in Spotify\n")
        f.write("2. Use the --create-playlist option to automatically create it (requires authorization)\n\n")
        
        # Just list the first 10 here, rest are in the file
        f.write("First 10 tracks for the playlist:\n")
        for i, gem in enumerate(playlist_gems[:10], 1):
            track = gem['track']
            artists = ', '.join(track['artist_names'])
            f.write(f"{i}. {track['name']} by {artists}\n")

    return gems_file, playlist_urls_file

def generate_combined_analysis(output_dir: str, processed_urls: List[str], playlist_folders: Dict[str, str] = None) -> None:
    """Generate a combined analysis of all processed playlists.
    
    Args:
        output_dir: Base output directory
        processed_urls: List of playlist URLs that were successfully processed
        playlist_folders: Dictionary mapping playlist IDs to folder names
    """
    try:
        all_tracks = []
        playlist_data = []
        
        # Collect all track data
        for url in processed_urls:
            try:
                # Extract playlist ID
                playlist_id = validate_spotify_url(url)
                playlist_folder = None
                
                # Check if we have a folder mapping
                if playlist_folders and playlist_id in playlist_folders:
                    playlist_folder = playlist_folders[playlist_id]
                    
                # Find the most recent JSON file for this playlist
                json_file = None
                
                # First try to find by reference file
                ref_pattern = os.path.join(output_dir, "*_ref.json")
                for ref_file in glob.glob(ref_pattern):
                    try:
                        with open(ref_file, 'r', encoding='utf-8') as f:
                            ref_data = json.load(f)
                            if ref_data.get('id') == playlist_id:
                                json_file = ref_data.get('files', {}).get('json', '')
                                if json_file and os.path.exists(json_file):
                                    break
                    except Exception:
                        continue
                
                # If not found by reference, try direct search
                if not json_file or not os.path.exists(json_file):
                    if playlist_folder:
                        # Search in specific playlist folder
                        folder_path = os.path.join(output_dir, playlist_folder)
                        pattern = os.path.join(folder_path, "*.json")
                        files = glob.glob(pattern)
                        if files:
                            json_file = max(files, key=os.path.getctime)
                    else:
                        # Search in all subdirectories
                        json_file = get_playlist_cache_path(output_dir, playlist_id)
                
                if json_file and os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'tracks' in data:
                            # Add playlist ID to metadata if not present
                            metadata = data.get('metadata', {})
                            if 'id' not in metadata:
                                metadata['id'] = playlist_id
                            playlist_data.append(metadata)
                            all_tracks.extend(data['tracks'])
                        else:
                            logger.warning(f"Invalid data format in cache for playlist {url}")
                else:
                    logger.warning(f"Cache not found for playlist {url}, skipping from combined analysis")
            except Exception as e:
                logger.warning(f"Error loading data for playlist {url}: {str(e)}")
                continue
        
        if not all_tracks:
            raise SpotifyExtractorError(
                "No track data available for combined analysis",
                "analysis_error"
            )
        
        # Generate analysis file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = os.path.join(output_dir, f"combined_analysis_{timestamp}.txt")
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("Combined Playlist Analysis\n")
            f.write("=========================\n\n")
            
            # Playlist Overview
            f.write("Playlist Overview\n")
            f.write("----------------\n")
            f.write(f"Total Playlists Analyzed: {len(playlist_data)}\n")
            total_tracks = len(all_tracks)
            f.write(f"Total Tracks: {total_tracks}\n\n")
            
            f.write("Included Playlists:\n")
            for pl in playlist_data:
                f.write(f"- {pl.get('name', 'Unknown')} by {pl.get('owner', 'Unknown')} ({pl.get('total_tracks', 0)} tracks)\n")
            f.write("\n")
            
            # All Tracks Sorted by Popularity
            f.write("All Tracks Sorted by Popularity\n")
            f.write("-----------------------------\n")
            sorted_tracks = sorted(all_tracks, key=lambda x: x['popularity'])
            for track in sorted_tracks:
                artists = ', '.join(track['artist_names'])
                f.write(f"[{track['popularity']:>3}/100] {track['name']} by {artists}\n")
                f.write(f"         Added: {track['added_at']}\n")
                f.write(f"         Album: {track['album']['name']} ({track['album']['release_date']})\n")
                f.write(f"         URL: {track['url']}\n\n")
            
            # Popularity Distribution
            # Fixed popularity range definition
            popularity_ranges = {
                "0-10": 0, 
                "11-20": 0, 
                "21-30": 0, 
                "31-40": 0,
                "41-50": 0, 
                "51-60": 0, 
                "61-70": 0, 
                "71-80": 0,
                "81-90": 0, 
                "91-100": 0
            }
            
            for track in all_tracks:
                pop = track['popularity']
                if 0 <= pop <= 10:
                    popularity_ranges["0-10"] += 1
                elif 11 <= pop <= 20:
                    popularity_ranges["11-20"] += 1
                elif 21 <= pop <= 30:
                    popularity_ranges["21-30"] += 1
                elif 31 <= pop <= 40:
                    popularity_ranges["31-40"] += 1
                elif 41 <= pop <= 50:
                    popularity_ranges["41-50"] += 1
                elif 51 <= pop <= 60:
                    popularity_ranges["51-60"] += 1
                elif 61 <= pop <= 70:
                    popularity_ranges["61-70"] += 1
                elif 71 <= pop <= 80:
                    popularity_ranges["71-80"] += 1
                elif 81 <= pop <= 90:
                    popularity_ranges["81-90"] += 1
                elif 91 <= pop <= 100:
                    popularity_ranges["91-100"] += 1
            
            f.write("\nPopularity Distribution:\n")
            f.write("----------------------\n")
            for range_key, count in popularity_ranges.items():
                percentage = (count / total_tracks) * 100 if total_tracks > 0 else 0
                bar = "█" * int(percentage / 2)  # Visual bar representation
                f.write(f"{range_key:>7}: {bar} {count:>4} tracks ({percentage:>5.1f}%)\n")
            
            # Underground Tracks (0-30 popularity)
            underground_tracks = [t for t in all_tracks if t['popularity'] <= 30]
            underground_tracks.sort(key=lambda x: x['popularity'])
            
            f.write("\nPotential Hidden Gems (Popularity <= 30):\n")
            f.write("--------------------------------------\n")
            for track in underground_tracks:
                artists = ", ".join(track['artist_names'])
                f.write(f"[{track['popularity']:>3}] {track['name']} by {artists}\n")
                f.write(f"      Added: {track['added_at']}\n")
                f.write(f"      URL: {track['url']}\n\n")
            
            # Artist Analysis
            artist_tracks = {}
            for track in all_tracks:
                for artist in track['artists']:
                    if artist['id'] not in artist_tracks:
                        artist_tracks[artist['id']] = {
                            'name': artist['name'],
                            'tracks': [],
                            'avg_popularity': 0
                        }
                    artist_tracks[artist['id']]['tracks'].append(track)
            
            # Calculate average popularity for each artist
            for artist_id, data in artist_tracks.items():
                total_pop = sum(t['popularity'] for t in data['tracks'])
                data['avg_popularity'] = total_pop / len(data['tracks'])
            
            # Find artists with low average popularity but multiple tracks
            underground_artists = {
                aid: data for aid, data in artist_tracks.items()
                if data['avg_popularity'] <= 30 and len(data['tracks']) >= 2
            }
            
            if underground_artists:
                f.write("\nPromising Underground Artists:\n")
                f.write("---------------------------\n")
                for artist_id, data in sorted(underground_artists.items(), 
                                           key=lambda x: (x[1]['avg_popularity'], -len(x[1]['tracks']))):
                    f.write(f"\n{data['name']}\n")
                    f.write(f"Average Popularity: {data['avg_popularity']:.1f}\n")
                    f.write(f"Tracks in Collection: {len(data['tracks'])}\n")
                    f.write("Tracks:\n")
                    for track in sorted(data['tracks'], key=lambda x: x['popularity']):
                        f.write(f"- [{track['popularity']:>3}] {track['name']}\n")
            
            logger.info(f"\nCombined analysis saved to: {analysis_file}")
        
        # Create a special hidden gems report with scoring
        if hasattr(args, 'hidden_gems') or hasattr(args, 'combined_analysis'):
            min_pop = getattr(args, 'min_pop', 0)
            max_pop = getattr(args, 'max_pop', 40)
            min_score = getattr(args, 'min_score', 20)
            top_gems = getattr(args, 'top_gems', 30)
            
            # Generate a combined hidden gems report
            gems_file, playlist_urls_file = generate_hidden_gems_report(output_dir, all_tracks, 
                                                                      min_pop, max_pop, min_score, top_gems,
                                                                      playlist_name="Combined_Playlists")
            logger.info(f"Combined hidden gems report saved to: {gems_file}")
            
            # Also generate individual hidden gems reports for each playlist folder
            if playlist_folders and not getattr(args, 'no_playlist_folders', False):
                for playlist_id, folder_name in playlist_folders.items():
                    # Find playlist-specific tracks
                    playlist_tracks = []
                    for url in processed_urls:
                        if validate_spotify_url(url) == playlist_id:
                            json_file = get_playlist_cache_path(output_dir, playlist_id)
                            if json_file and os.path.exists(json_file):
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    if isinstance(data, dict) and 'tracks' in data:
                                        playlist_tracks.extend(data['tracks'])
                                        playlist_name = data.get('metadata', {}).get('name', folder_name)
                    
                    if playlist_tracks:
                        # Find the correct folder path
                        folder_path = os.path.join(output_dir, folder_name)
                        # Generate playlist-specific gems report
                        pl_gems_file, pl_urls_file = generate_hidden_gems_report(
                            folder_path, playlist_tracks, 
                            min_pop, max_pop, min_score, top_gems,
                            playlist_name=playlist_name
                        )
                        logger.info(f"Playlist-specific hidden gems report saved to: {pl_gems_file}")
            
            # If create playlist option is enabled, do it for the combined list
            if getattr(args, 'create_playlist', False):
                try:
                    # Use user-specified file if provided, otherwise use the one we just generated
                    urls_file = getattr(args, 'urls_file', None) or playlist_urls_file
                    
                    # Set up OAuth for user authorization
                    scope = "playlist-modify-private"
                    if getattr(args, 'playlist_public', False):
                        scope += " playlist-modify-public"
                    
                    sp_oauth = spotipy.oauth2.SpotifyOAuth(
                        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
                        redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback'),
                        scope=scope
                    )
                    
                    # Create the playlist
                    playlist_url = create_spotify_playlist(
                        sp_oauth=sp_oauth,
                        urls_file=urls_file,
                        playlist_name=getattr(args, 'playlist_name', "Hidden Gems"),
                        description=getattr(args, 'playlist_description', 
                                          "Discovered gems from playlists analyzed by Spotify Playlist Extractor"),
                        public=getattr(args, 'playlist_public', False)
                    )
                    
                    logger.info(f"Created Spotify playlist: {playlist_url}")
                
                except Exception as e:
                    logger.error(f"Failed to create Spotify playlist: {str(e)}")
            
    except Exception as e:
        logger.error(f"Failed to generate combined analysis: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def create_spotify_playlist(sp_oauth: spotipy.oauth2.SpotifyOAuth, 
                           urls_file: str, 
                           playlist_name: str = "Hidden Gems", 
                           description: str = "Discovered by Spotify Playlist Extractor", 
                           public: bool = False) -> str:
    """Create a new Spotify playlist from a file containing track URLs.
    
    Args:
        sp_oauth: Spotify OAuth manager for user authentication
        urls_file: Path to file containing track URLs (one per line)
        playlist_name: Name for the new playlist
        description: Description for the new playlist
        public: Whether the playlist should be public (default False)
        
    Returns:
        URL of the created playlist
        
    Raises:
        SpotifyExtractorError: If playlist creation fails
    """
    try:
        # Check if file exists
        if not os.path.exists(urls_file):
            raise SpotifyExtractorError(
                f"URLs file not found: {urls_file}",
                "file_error"
            )
        
        # Read track URLs
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if not urls:
            raise SpotifyExtractorError(
                "No valid URLs found in the file",
                "validation_error"
            )
        
        # Extract track IDs from URLs
        track_ids = []
        for url in urls:
            try:
                # Extract track ID from URL
                track_id = url.split('/')[-1].split('?')[0]
                track_ids.append(track_id)
            except Exception:
                logger.warning(f"Could not extract track ID from URL: {url}")
        
        if not track_ids:
            raise SpotifyExtractorError(
                "No valid track IDs found in the URLs",
                "validation_error"
            )
        
        # Set up authentication
        sp = spotipy.Spotify(auth_manager=sp_oauth)
        
        # Get the current user
        user_info = sp.current_user()
        user_id = user_info['id']
        
        # Create a new playlist
        timestamp = datetime.now().strftime("%Y-%m-%d")
        playlist_name_with_date = f"{playlist_name} ({timestamp})"
        
        logger.info(f"Creating playlist '{playlist_name_with_date}' for user {user_id}")
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name_with_date,
            public=public,
            description=description
        )
        
        playlist_id = playlist['id']
        playlist_url = playlist['external_urls']['spotify']
        
        # Add tracks to the playlist (in batches of 100, which is Spotify's limit)
        track_batches = [track_ids[i:i+100] for i in range(0, len(track_ids), 100)]
        
        for batch in track_batches:
            sp.playlist_add_items(playlist_id=playlist_id, items=batch)
        
        logger.info(f"Created playlist with {len(track_ids)} tracks: {playlist_url}")
        return playlist_url
        
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 401:
            raise SpotifyExtractorError(
                "Authentication failed. Please check your credentials or reauthorize.",
                "auth_error",
                e
            )
        elif e.http_status == 403:
            raise SpotifyExtractorError(
                "Forbidden. You don't have permission to create playlists.",
                "auth_error",
                e
            )
        else:
            raise SpotifyExtractorError(
                f"Spotify API error: {str(e)}",
                "api_error",
                e
            )
    except Exception as e:
        raise SpotifyExtractorError(
            f"Failed to create Spotify playlist: {str(e)}",
            "playlist_creation_error",
            e
        )

def main():
    """Main entry point for the script."""
    global args  # Make args global so other functions can access it
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Collect all playlist URLs
        playlist_urls = []
        if args.urls:
            playlist_urls.extend(args.urls)
        if args.file:
            playlist_urls.extend(read_playlist_urls(args.file))
        
        if not playlist_urls:
            raise SpotifyExtractorError(
                "No playlist URLs provided. Use positional arguments or --file option.",
                "validation_error"
            )
        
        # Normalize and validate output directory
        output_dir = normalize_path(args.output_dir)
        create_output_dir(output_dir)
        
        # Set up logging
        setup_logging(output_dir)
        
        # Initialize Spotify client
        sp = initialize_spotify()
        logger.info(f"Using Client ID: {os.getenv('SPOTIFY_CLIENT_ID')[:5]}...")
        
        # Process playlists
        process_playlists(sp, playlist_urls, args)
        
    except SpotifyExtractorError as e:
        logger.error(f"Error Type: {e.error_type}")
        logger.error(f"Error Message: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 