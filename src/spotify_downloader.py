#!/usr/bin/env python3
"""
Spotify Playlist Downloader
A tool to download tracks from Spotify playlists using the spotify_playlist_extractor module.
"""

import argparse
import sys
import os
import logging
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# Import from the spotify_playlist_extractor module
try:
    from spotify_playlist_extractor import (
        validate_spotify_url,
        initialize_spotify,
        process_playlist,
        get_playlist_metadata,
        get_all_tracks,
        SpotifyExtractorError
    )
except ImportError:
    # When imported from a different directory or as a script
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.spotify_playlist_extractor import (
        validate_spotify_url,
        initialize_spotify,
        process_playlist,
        get_playlist_metadata,
        get_all_tracks,
        SpotifyExtractorError
    )

# Ensure output directory exists
output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
os.makedirs(output_dir, exist_ok=True)

# Configure logging
log_file = os.path.join(output_dir, "spotify_downloader.log")
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
except Exception as e:
    # Fall back to console-only logging if file logging fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    print(f"Warning: Could not set up file logging: {str(e)}")

logger = logging.getLogger(__name__)

class DownloaderError(Exception):
    """Custom exception class for Spotify Downloader errors."""
    def __init__(self, message: str, error_type: str = "general", original_error: Optional[Exception] = None):
        self.message = message
        self.error_type = error_type
        self.original_error = original_error
        super().__init__(self.message)

def check_dependencies() -> bool:
    """Check if required external dependencies are installed."""
    try:
        # Check if yt-dlp is installed
        subprocess.run(
            ["yt-dlp", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            check=True
        )
        
        # Check if ffmpeg is installed
        subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            check=True
        )
        
        return True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"Required dependencies check failed: {str(e)}")
        return False

def search_track_on_youtube(track_info: Dict) -> str:
    """
    Create a search query for YouTube based on track information.
    
    Args:
        track_info: Dictionary containing track data
        
    Returns:
        Search query string for YouTube
    """
    # Format: "Artist - Track Name"
    artists = ", ".join(track_info.get('artist_names', []))
    track_name = track_info.get('name', '')
    
    # Clean up track name - remove featuring, remix, etc. info for better search results
    track_name = track_name.split(" - ")[0]  # Remove anything after hyphen
    track_name = track_name.split(" (feat")[0]  # Remove featuring info
    track_name = track_name.split(" (with")[0]  # Remove "with artist" info
    track_name = track_name.split(" [")[0]  # Remove bracketed info
    
    # Create search query
    search_query = f"{artists} - {track_name}"
    
    return search_query

def download_track(track_info: Dict, output_dir: str, format_str: str = "mp3", 
                 retry_count: int = 3, skip_existing: bool = True) -> Dict:
    """
    Download a track using yt-dlp.
    
    Args:
        track_info: Dictionary containing track data
        output_dir: Directory to save downloaded tracks
        format_str: Output format (mp3, m4a, etc.)
        retry_count: Number of retries if download fails
        skip_existing: Whether to skip existing files
        
    Returns:
        Dictionary with download status and information
    """
    search_query = search_track_on_youtube(track_info)
    # Remove special characters that might cause issues with filenames
    safe_query = "".join(c if c.isalnum() or c in " -_.,()[]" else "_" for c in search_query)
    
    # Set up output template that includes track metadata
    output_template = os.path.join(
        output_dir, 
        f"{safe_query}.%(ext)s"
    )
    
    # Build command
    command = [
        "yt-dlp",
        "-x",  # Extract audio
        f"--audio-format={format_str}",
        "--audio-quality=0",  # Best quality
        "-o", output_template,
        "--embed-metadata",
        "--max-filesize", "25m",  # Skip files larger than 25MB (likely not the right track)
        "ytsearch:" + search_query
    ]
    
    # Add additional options
    if skip_existing:
        command.append("--ignore-errors")
    
    # Track status information
    status = {
        "track": track_info,
        "success": False,
        "file_path": None,
        "error": None,
        "search_query": search_query
    }
    
    for attempt in range(retry_count):
        try:
            # If not first attempt, wait a bit before retrying
            if attempt > 0:
                time.sleep(2)
                logger.info(f"Retry {attempt} for track: {search_query}")
            
            # Run yt-dlp
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False  # Don't raise error, we'll handle it
            )
            
            # Check if successful
            if process.returncode == 0:
                # Find the downloaded file by searching in the output directory
                files = list(Path(output_dir).glob(f"{safe_query}*.{format_str}"))
                if files:
                    downloaded_file = str(files[0])
                    
                    # Add metadata to the file
                    add_metadata_to_file(downloaded_file, track_info, format_str)
                    
                    status["success"] = True
                    status["file_path"] = downloaded_file
                    break
                else:
                    logger.warning(f"Download seemed successful but file not found for: {search_query}")
                    status["error"] = "File not found after download"
            else:
                error_message = process.stderr.strip()
                logger.warning(f"Download failed for {search_query}: {error_message}")
                status["error"] = error_message
                
        except Exception as e:
            logger.warning(f"Error during download of {search_query}: {str(e)}")
            status["error"] = str(e)
    
    return status

def add_metadata_to_file(file_path: str, track_info: Dict, format_str: str) -> None:
    """
    Add metadata to the downloaded audio file.
    
    Args:
        file_path: Path to the audio file
        track_info: Dictionary containing track metadata
        format_str: File format (mp3, m4a, etc.)
    """
    try:
        # Use ffmpeg to add metadata
        command = [
            "ffmpeg",
            "-i", file_path,
            "-c", "copy",
            "-metadata", f"title={track_info.get('name', '')}",
            "-metadata", f"artist={', '.join(track_info.get('artist_names', []))}",
            "-metadata", f"album={track_info.get('album', {}).get('name', '')}",
            "-metadata", f"date={track_info.get('album', {}).get('release_date', '')}",
            "-y",  # Overwrite output file
            f"{file_path}.temp.{format_str}"
        ]
        
        # Execute command
        subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        # Replace original file with new one
        os.replace(f"{file_path}.temp.{format_str}", file_path)
        
    except Exception as e:
        logger.warning(f"Failed to add metadata to {file_path}: {str(e)}")
        # Continue without metadata if failed

def download_tracks(tracks: List[Dict], output_dir: str, format_str: str = "mp3", 
                  max_workers: int = 4, skip_existing: bool = True) -> List[Dict]:
    """
    Download multiple tracks using a thread pool.
    
    Args:
        tracks: List of track dictionaries to download
        output_dir: Directory to save downloaded tracks
        format_str: Output format (mp3, m4a, etc.)
        max_workers: Maximum number of concurrent downloads
        skip_existing: Whether to skip existing files
        
    Returns:
        List of dictionaries with download status for each track
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process tracks
    download_results = []
    
    logger.info(f"Starting download of {len(tracks)} tracks to {output_dir}")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a list of futures
        futures = [
            executor.submit(
                download_track, 
                track, 
                output_dir, 
                format_str,
                3,  # retry_count
                skip_existing
            )
            for track in tracks
        ]
        
        # Process results as they complete with progress bar
        for future in tqdm(futures, desc="Downloading tracks", unit="track"):
            try:
                result = future.result()
                download_results.append(result)
                
                # Log result
                track_name = result['track'].get('name', 'Unknown')
                if result['success']:
                    logger.info(f"Successfully downloaded: {track_name}")
                else:
                    logger.warning(f"Failed to download: {track_name}, Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error processing download result: {str(e)}")
                download_results.append({
                    "track": {"name": "Unknown"},
                    "success": False,
                    "error": str(e)
                })
    
    # Summarize download status
    successful = sum(1 for r in download_results if r['success'])
    logger.info(f"Download complete. Successfully downloaded {successful} of {len(tracks)} tracks.")
    
    return download_results

def download_playlist(url: str, output_dir: str, format_str: str = "mp3", 
                     max_workers: int = 4, skip_existing: bool = True) -> Tuple[Dict, List[Dict]]:
    """
    Download a Spotify playlist.
    
    Args:
        url: Spotify playlist URL
        output_dir: Directory to save downloaded tracks
        format_str: Output format (mp3, m4a, etc.)
        max_workers: Maximum number of concurrent downloads
        skip_existing: Whether to skip existing files
        
    Returns:
        Tuple of (playlist metadata, list of download results)
    """
    try:
        # First process the playlist using spotify_playlist_extractor
        sp = initialize_spotify()
        
        # Get playlist ID
        playlist_id = validate_spotify_url(url)
        
        # Get playlist metadata
        metadata = get_playlist_metadata(sp, playlist_id)
        
        # Get all tracks
        tracks = get_all_tracks(sp, playlist_id)
        
        # Create a playlist-specific directory
        playlist_dir = os.path.join(output_dir, metadata.get('name', playlist_id))
        os.makedirs(playlist_dir, exist_ok=True)
        
        # Save playlist metadata and track information
        playlist_info = {
            "metadata": metadata,
            "tracks": tracks,
            "url": url,
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(os.path.join(playlist_dir, "playlist_info.json"), "w", encoding="utf-8") as f:
            json.dump(playlist_info, f, indent=2, ensure_ascii=False)
        
        # Create a directory for the downloaded tracks
        downloads_dir = os.path.join(playlist_dir, "Downloads")
        
        # Download the tracks
        download_results = download_tracks(
            tracks=tracks,
            output_dir=downloads_dir,
            format_str=format_str,
            max_workers=max_workers,
            skip_existing=skip_existing
        )
        
        # Save download results
        with open(os.path.join(playlist_dir, "download_results.json"), "w", encoding="utf-8") as f:
            # Convert any Path objects to strings for JSON serialization
            sanitized_results = []
            for result in download_results:
                result_copy = result.copy()
                if isinstance(result_copy.get('file_path'), Path):
                    result_copy['file_path'] = str(result_copy['file_path'])
                sanitized_results.append(result_copy)
                
            json.dump(sanitized_results, f, indent=2, ensure_ascii=False)
        
        return metadata, download_results
    
    except SpotifyExtractorError as e:
        logger.error(f"Spotify Extractor Error: {str(e)}")
        raise DownloaderError(
            f"Failed to process playlist: {str(e)}",
            error_type="spotify_error",
            original_error=e
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise DownloaderError(
            f"Unexpected error: {str(e)}",
            error_type="unexpected_error",
            original_error=e
        )

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Download tracks from Spotify playlists using yt-dlp.'
    )
    
    # Input options
    input_group = parser.add_argument_group('Input Options')
    input_group.add_argument('urls', nargs='*', help='One or more Spotify playlist URLs')
    input_group.add_argument('-f', '--file', help='Text file containing Spotify playlist URLs (one per line)')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('-o', '--output-dir', default='output',
                          help='Output directory for downloaded tracks (default: output)')
    output_group.add_argument('--format', default='mp3', choices=['mp3', 'm4a', 'opus', 'wav'],
                          help='Audio format for downloaded tracks (default: mp3)')
    
    # Download options
    download_group = parser.add_argument_group('Download Options')
    download_group.add_argument('--max-workers', type=int, default=4,
                            help='Maximum number of concurrent downloads (default: 4)')
    download_group.add_argument('--skip-existing', action='store_true',
                            help='Skip downloading files that already exist')
    download_group.add_argument('--retry-count', type=int, default=3,
                            help='Number of retries for failed downloads (default: 3)')
    
    # Utility options
    utility_group = parser.add_argument_group('Utility Options')
    utility_group.add_argument('--check-deps', action='store_true',
                            help='Check if required dependencies (yt-dlp, ffmpeg) are installed')
    
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Check if required dependencies are installed
        if args.check_deps:
            if check_dependencies():
                logger.info("All required dependencies are installed.")
                print("✅ All required dependencies (yt-dlp, ffmpeg) are installed correctly.")
                sys.exit(0)
            else:
                logger.error("Required dependencies are not installed.")
                print("❌ Some required dependencies are missing. Please install yt-dlp and ffmpeg.")
                sys.exit(1)
        
        if not check_dependencies():
            logger.error("Required dependencies (yt-dlp, ffmpeg) are not installed. Please install them and try again.")
            sys.exit(1)
        
        # Collect all playlist URLs
        playlist_urls = []
        if args.urls:
            playlist_urls.extend(args.urls)
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    playlist_urls.extend([line.strip() for line in f if line.strip()])
            except Exception as e:
                logger.error(f"Failed to read playlist URLs from file {args.file}: {str(e)}")
                sys.exit(1)
        
        if not playlist_urls:
            logger.error("No playlist URLs provided. Use positional arguments or --file option.")
            sys.exit(1)
        
        # Create output directory
        try:
            os.makedirs(args.output_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create output directory {args.output_dir}: {str(e)}")
            sys.exit(1)
        
        # Process each playlist
        for url in playlist_urls:
            try:
                logger.info(f"Processing playlist: {url}")
                metadata, download_results = download_playlist(
                    url=url,
                    output_dir=args.output_dir,
                    format_str=args.format,
                    max_workers=args.max_workers,
                    skip_existing=args.skip_existing
                )
                
                # Print summary
                successful = sum(1 for r in download_results if r['success'])
                logger.info(f"Playlist: {metadata.get('name', 'Unknown')}")
                logger.info(f"Downloaded: {successful} of {len(download_results)} tracks")
                
            except DownloaderError as e:
                logger.error(f"Error downloading playlist {url}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error downloading playlist {url}: {str(e)}")
                continue
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 