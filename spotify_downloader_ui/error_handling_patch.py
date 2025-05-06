"""
Patching utilities for error handling in the application.
"""

import logging
import sys
import os
import traceback
from typing import Callable, Dict, Optional, Any

logger = logging.getLogger(__name__)

def patch_error_service():
    """Apply patches to error handling to ensure compatibility with both new and old code."""
    try:
        from PySide6.QtWidgets import QMessageBox
        from spotify_downloader_ui.services.error_service import ErrorService
        
        # Store the original handle_error method
        original_handle_error = ErrorService.handle_error
        
        # Create a replacement show_error method that won't crash
        def patched_show_error(self, title: str, message: str, parent=None) -> None:
            """Show an error dialog with the specified details.
            
            Args:
                title: Dialog title
                message: Error message
                parent: Parent widget
            """
            logger.debug(f"Patched show_error called with title: {title}")
            
            # Create a basic error message box
            msg_box = QMessageBox(parent)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec_()
            
        # Add the method to the class
        if not hasattr(ErrorService, 'show_error') or ErrorService.show_error.__name__ != 'patched_show_error':
            ErrorService.show_error = patched_show_error
            logger.info("Successfully patched ErrorService with show_error method")
        
    except ImportError as e:
        logger.error(f"Failed to patch ErrorService: {e}")
    except Exception as e:
        logger.error(f"Error during ErrorService patching: {e}")
        logger.debug(traceback.format_exc())

def patch_dependency_check():
    """Apply a patch to make dependency checks work with PySide6."""
    try:
        # Find the spotify_downloader module
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src import spotify_downloader
        
        # Create a patched version of check_dependencies that won't crash on error
        original_check = spotify_downloader.check_dependencies
        
        def patched_check_dependencies() -> bool:
            """Patched version of dependency checker that handles exceptions better."""
            try:
                return original_check()
            except Exception as e:
                logger.error(f"Dependency check failed with error: {e}")
                # Just return False rather than crashing
                return False
                
        # Replace the original function with our patched version
        spotify_downloader.check_dependencies = patched_check_dependencies
        logger.info("Successfully patched dependency check function")
        
    except ImportError as e:
        logger.error(f"Failed to patch dependency check: {e}")
    except Exception as e:
        logger.error(f"Error during dependency check patching: {e}")
        logger.debug(traceback.format_exc())

def patch_playlist_service():
    """Apply a patch to the playlist service to handle dictionary parameters."""
    try:
        from spotify_downloader_ui.services.playlist_service import PlaylistService
        
        # Get the original method
        original_process_playlist = PlaylistService.process_playlist
        
        # Create a patched version that ensures output_dir is always a string
        def patched_process_playlist(self, url: str, output_dir: str, include_artist: bool = False,
                                    create_playlist_folders: bool = True):
            """Patched version of process_playlist that ensures output_dir is a string."""
            # Define local variables to avoid using undefined 'args'
            actual_output_dir = "output"
            actual_include_artist = include_artist
            actual_create_playlist_folders = create_playlist_folders
            
            # Ensure output_dir is a string
            if isinstance(output_dir, dict):
                # Extract relevant options
                options = output_dir
                if "output_dir" in options and isinstance(options["output_dir"], str):
                    actual_output_dir = options["output_dir"]
                else:
                    actual_output_dir = "output"
                    
                # Extract other options if they exist
                if "include_artist" in options:
                    actual_include_artist = options["include_artist"]
                if "create_playlist_folders" in options:
                    actual_create_playlist_folders = options["create_playlist_folders"]
                    
                logger.info(f"Patched process_playlist using output_dir: {actual_output_dir}, "
                          f"include_artist: {actual_include_artist}, "
                          f"create_playlist_folders: {actual_create_playlist_folders}")
            else:
                # If it's already a string, use it directly
                actual_output_dir = output_dir if isinstance(output_dir, str) else "output"
                
            # Call the original method with the fixed parameters
            return original_process_playlist(self, url, actual_output_dir, actual_include_artist, actual_create_playlist_folders)
        
        # Replace the method
        PlaylistService.process_playlist = patched_process_playlist
        logger.info("Successfully patched PlaylistService.process_playlist")
        
    except ImportError as e:
        logger.error(f"Failed to patch PlaylistService: {e}")
    except Exception as e:
        logger.error(f"Error during PlaylistService patching: {e}")
        logger.debug(traceback.format_exc())

def apply_all_patches():
    """Apply all patches for error handling."""
    logger.info("Applying all UI patches...")
    patch_error_service()
    patch_dependency_check()
    patch_playlist_service()
    logger.info("All UI patches applied") 