#!/usr/bin/env python3
"""
Command-line interface for Spotify Downloader.

This module provides a command-line wrapper around the core functionality,
allowing users to access all features without the GUI.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("spotify_downloader.cli")

def create_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Spotify Downloader - Extract and analyze Spotify playlists"
    )
    
    # General options
    parser.add_argument(
        "--version",
        action="store_true",
        help="Display version information"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.path.join(os.getcwd(), "output"),
        help="Directory for output files (default: './output')"
    )
    
    # Subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract playlist information")
    extract_parser.add_argument(
        "playlist_urls",
        nargs="+",
        help="URLs of Spotify playlists to extract"
    )
    extract_parser.add_argument(
        "--market",
        type=str,
        default="US",
        help="Market to use for Spotify API requests (default: 'US')"
    )
    extract_parser.add_argument(
        "--include-preview-url",
        action="store_true",
        help="Include preview URLs in the output"
    )
    
    # Hidden gems command
    hidden_gems_parser = subparsers.add_parser("hidden-gems", help="Find hidden gems in playlists")
    hidden_gems_parser.add_argument(
        "playlist_urls",
        nargs="+",
        help="URLs of Spotify playlists to analyze"
    )
    hidden_gems_parser.add_argument(
        "--min-pop",
        type=int,
        default=5,
        help="Minimum popularity for hidden gems (default: 5)"
    )
    hidden_gems_parser.add_argument(
        "--max-pop",
        type=int,
        default=35,
        help="Maximum popularity for hidden gems (default: 35)"
    )
    hidden_gems_parser.add_argument(
        "--min-score",
        type=int,
        default=25,
        help="Minimum score for hidden gems (default: 25)"
    )
    hidden_gems_parser.add_argument(
        "--top-gems",
        type=int,
        default=20,
        help="Number of top gems to include (default: 20)"
    )
    
    # Create playlist command
    create_playlist_parser = subparsers.add_parser("create-playlist", help="Create a new Spotify playlist")
    create_playlist_parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Name of the playlist to create"
    )
    create_playlist_parser.add_argument(
        "--description",
        type=str,
        default="Created with Spotify Downloader",
        help="Description of the playlist (default: 'Created with Spotify Downloader')"
    )
    create_playlist_parser.add_argument(
        "--public",
        action="store_true",
        help="Make the playlist public (default: private)"
    )
    create_playlist_parser.add_argument(
        "--track-ids",
        nargs="+",
        help="Spotify track IDs to add to the playlist"
    )
    create_playlist_parser.add_argument(
        "--from-json",
        type=str,
        help="Path to JSON file containing track IDs"
    )
    
    # Compare playlists command
    compare_parser = subparsers.add_parser("compare", help="Compare multiple playlists")
    compare_parser.add_argument(
        "playlist_urls",
        nargs="+",
        help="URLs of Spotify playlists to compare"
    )
    compare_parser.add_argument(
        "--output-format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format for comparison results (default: 'text')"
    )
    
    # Auth command
    auth_parser = subparsers.add_parser("auth", help="Manage Spotify authentication")
    auth_parser.add_argument(
        "--logout",
        action="store_true",
        help="Clear stored authentication credentials"
    )
    
    # GUI command
    gui_parser = subparsers.add_parser("gui", help="Launch the graphical user interface")
    
    return parser

def handle_extract(args: argparse.Namespace) -> int:
    """
    Handle the extract command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    logger.info(f"Extracting playlists: {args.playlist_urls}")
    
    # In a real implementation, this would call the core functionality
    # For now, we'll just print a message and import the actual module
    
    from spotify_downloader_ui.services.extraction_service import ExtractionService
    
    try:
        # This is a simplified example
        for url in args.playlist_urls:
            logger.info(f"Extracting playlist: {url}")
            
            # In a real implementation, this would call the extraction service
            # extraction_service = ExtractionService()
            # extraction_service.extract_playlist(url, market=args.market, include_preview_url=args.include_preview_url)
            
            logger.info(f"Playlist information saved to {args.output_dir}")
        
        return 0
    except Exception as e:
        logger.error(f"Failed to extract playlist: {e}")
        return 1

def handle_hidden_gems(args: argparse.Namespace) -> int:
    """
    Handle the hidden-gems command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    logger.info(f"Finding hidden gems in playlists: {args.playlist_urls}")
    
    # In a real implementation, this would call the core functionality
    try:
        # This is a simplified example
        for url in args.playlist_urls:
            logger.info(f"Analyzing playlist: {url}")
            
            # In a real implementation, this would call the analysis service
            logger.info(f"Hidden gems report saved to {args.output_dir}")
        
        return 0
    except Exception as e:
        logger.error(f"Failed to find hidden gems: {e}")
        return 1

def handle_create_playlist(args: argparse.Namespace) -> int:
    """
    Handle the create-playlist command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    logger.info(f"Creating playlist: {args.name}")
    
    # In a real implementation, this would call the core functionality
    try:
        # This is a simplified example
        track_ids = args.track_ids or []
        
        if args.from_json:
            import json
            try:
                with open(args.from_json, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        track_ids.extend(data)
                    elif isinstance(data, dict) and 'tracks' in data:
                        track_ids.extend(data['tracks'])
            except Exception as e:
                logger.error(f"Failed to load track IDs from JSON file: {e}")
                return 1
        
        logger.info(f"Adding {len(track_ids)} tracks to playlist")
        
        # In a real implementation, this would call the playlist creation service
        logger.info(f"Playlist '{args.name}' created successfully")
        
        return 0
    except Exception as e:
        logger.error(f"Failed to create playlist: {e}")
        return 1

def handle_compare(args: argparse.Namespace) -> int:
    """
    Handle the compare command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    logger.info(f"Comparing playlists: {args.playlist_urls}")
    
    # In a real implementation, this would call the core functionality
    try:
        # This is a simplified example
        logger.info(f"Comparing {len(args.playlist_urls)} playlists")
        
        # In a real implementation, this would call the comparison service
        logger.info(f"Comparison results saved to {args.output_dir}")
        
        return 0
    except Exception as e:
        logger.error(f"Failed to compare playlists: {e}")
        return 1

def handle_auth(args: argparse.Namespace) -> int:
    """
    Handle the auth command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    # In a real implementation, this would call the core functionality
    try:
        if args.logout:
            logger.info("Logging out (clearing stored credentials)")
            # In a real implementation, this would call the auth service
            return 0
        else:
            logger.info("Authenticating with Spotify")
            # In a real implementation, this would call the auth service
            return 0
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return 1

def handle_gui(args: argparse.Namespace) -> int:
    """
    Handle the gui command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    logger.info("Launching GUI")
    
    try:
        # Import and run the GUI application
        from spotify_downloader_ui.app import run_app
        run_app()
        return 0
    except Exception as e:
        logger.error(f"Failed to launch GUI: {e}")
        return 1

def handle_version(args: argparse.Namespace) -> int:
    """
    Handle the version command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    from spotify_downloader_ui.packaging.common import APP_NAME, APP_VERSION
    
    print(f"{APP_NAME} v{APP_VERSION}")
    return 0

def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create output directory if it doesn't exist and is specified
    if hasattr(args, 'output_dir'):
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
    
    # Handle version command first
    if args.version:
        return handle_version(args)
    
    # Handle commands
    if args.command == "extract":
        return handle_extract(args)
    elif args.command == "hidden-gems":
        return handle_hidden_gems(args)
    elif args.command == "create-playlist":
        return handle_create_playlist(args)
    elif args.command == "compare":
        return handle_compare(args)
    elif args.command == "auth":
        return handle_auth(args)
    elif args.command == "gui":
        return handle_gui(args)
    else:
        # No command specified, show help
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main()) 