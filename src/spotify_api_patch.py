"""
Patch file for Spotify API client to add compatibility methods.
This file adds methods that might be missing in newer versions of the spotipy client.
"""

import logging
import sys
import os
import inspect
import spotipy
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def apply_spotify_patches():
    """Apply patches to the Spotify client class to ensure backward compatibility."""
    
    logger.info("Applying compatibility patches to Spotify client...")
    
    # Add _get_playlist_tracks method if it doesn't exist
    if not hasattr(spotipy.Spotify, '_get_playlist_tracks'):
        logger.info("Adding _get_playlist_tracks compatibility method")
        
        # Add the method as a proxy to the public method
        def _get_playlist_tracks(self, playlist_id, fields=None, limit=100, offset=0, market=None):
            """Compatibility method that wraps playlist_tracks for backward compatibility."""
            logger.debug(f"Using patched _get_playlist_tracks for {playlist_id}")
            return self.playlist_tracks(playlist_id, fields=fields, limit=limit, offset=offset, market=market)
        
        # Add the method to the Spotify class
        spotipy.Spotify._get_playlist_tracks = _get_playlist_tracks
    
    # Also patch the process_playlist function in spotify_playlist_extractor.py
    try:
        # Import the module
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src import spotify_playlist_extractor
        
        # Replace the process_playlist function with our improved version that handles dictionary input
        original_func = spotify_playlist_extractor.process_playlist
        
        # Create a simple class to mock the args Namespace that the CLI version would provide
        class MockArgs:
            """Mock argparse.Namespace for use in non-CLI contexts."""
            def __init__(self):
                # Default values for all potential args attributes
                self.hidden_gems = False
                self.combined_analysis = False
                self.min_pop = 0
                self.max_pop = 40
                self.min_score = 20
                self.top_gems = 30
                self.create_playlist = False
                self.skip_existing = False
                self.retry_failed = False
                self.retry_limit = 3
                self.no_playlist_folders = False
                self.include_artist = False
                self.output_dir = "output"
                self.batch_size = 5
                
            def __repr__(self):
                return f"MockArgs(hidden_gems={self.hidden_gems}, output_dir='{self.output_dir}')"
        
        # Create an improved version that better handles the output_dir parameter
        def patched_process_playlist(*args, **kwargs):
            """Patched version of process_playlist to handle both string and dict outputs."""
            # Create a mock args object that will be available in the global scope of spotify_playlist_extractor
            mock_args = MockArgs()
            
            # Handle parameter conversion if needed
            if len(args) >= 2:
                sp_client = args[0]  # First arg is the Spotify client
                output_dir_arg = args[1]  # Second arg should be output_dir
                
                # If it's a dict, extract the string output_dir and other options
                if isinstance(output_dir_arg, dict):
                    options = output_dir_arg
                    
                    # Extract and set output_dir
                    if "output_dir" in options and isinstance(options["output_dir"], str):
                        str_output_dir = options["output_dir"]
                        mock_args.output_dir = str_output_dir
                    else:
                        str_output_dir = "output"
                    
                    # Extract and set other options in both args and the modified args list
                    if "include_artist" in options:
                        mock_args.include_artist = options["include_artist"]
                    
                    if "create_playlist_folders" in options:
                        mock_args.no_playlist_folders = not options["create_playlist_folders"]
                    
                    # Set output_dir in mock_args which will be used in the original function
                    mock_args.output_dir = str_output_dir
                    
                    # Build the correct args for the function call
                    if len(args) >= 3:
                        url = args[2]
                        logger.info(f"Patched process_playlist: converting dict to string path: {str_output_dir}")
                        
                        # Rebuild args with the string output_dir
                        new_args = list(args)
                        new_args[1] = str_output_dir
                        args = tuple(new_args)
                else:
                    # If output_dir is already a string, just set it in mock_args
                    mock_args.output_dir = output_dir_arg
            
            # Inject the mock_args into the module's global namespace
            # This ensures the 'args' variable is available when the original function executes
            original_globals = dict(spotify_playlist_extractor.__dict__)
            spotify_playlist_extractor.__dict__['args'] = mock_args
            
            try:
                # Call the original function
                logger.debug(f"Calling original process_playlist with mock args: {mock_args}")
                return original_func(*args, **kwargs)
            finally:
                # Clean up: Remove our injected args to avoid side effects
                if 'args' in spotify_playlist_extractor.__dict__ and spotify_playlist_extractor.__dict__['args'] is mock_args:
                    del spotify_playlist_extractor.__dict__['args']
        
        # Replace the original function with our patched version
        spotify_playlist_extractor.process_playlist = patched_process_playlist
        logger.info("Successfully patched spotify_playlist_extractor.process_playlist")
        
    except ImportError as e:
        logger.warning(f"Could not patch spotify_playlist_extractor: {e}")
    except Exception as e:
        logger.warning(f"Error while patching spotify_playlist_extractor: {e}")
    
    logger.info("Spotify API patches applied successfully") 