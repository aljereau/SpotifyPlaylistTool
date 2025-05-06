"""
Error handling service for the Spotify Downloader UI.
"""

import logging
import traceback
import sys
from typing import Callable, Dict, Optional, Any
from PySide6.QtWidgets import QMessageBox

# Import the backend error class for type checking
try:
    from src.spotify_playlist_extractor import SpotifyExtractorError
except ImportError:
    # Create a placeholder if we can't import the real one
    class SpotifyExtractorError(Exception):
        def __init__(self, message: str, error_type: str = "general", original_error: Optional[Exception] = None):
            self.message = message
            self.error_type = error_type
            self.original_error = original_error
            super().__init__(self.message)

logger = logging.getLogger(__name__)

class ErrorService:
    """Service for handling and displaying errors in the UI."""
    
    def __init__(self):
        """Initialize the error handling service."""
        self._error_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
        logger.info("Error handling service initialized")
    
    def _register_default_handlers(self):
        """Register default error handlers."""
        # Register handlers for known error types
        self.register_error_handler("auth_error", self._handle_auth_error)
        self.register_error_handler("validation_error", self._handle_validation_error)
        self.register_error_handler("api_error", self._handle_api_error)
        self.register_error_handler("not_found_error", self._handle_not_found_error)
        self.register_error_handler("access_error", self._handle_access_error)
        self.register_error_handler("env_error", self._handle_env_error)
        self.register_error_handler("metadata_error", self._handle_metadata_error)
        self.register_error_handler("initialization_error", self._handle_initialization_error)
    
    def register_error_handler(self, error_type: str, handler: Callable) -> None:
        """Register a handler for a specific error type.
        
        Args:
            error_type: The type of error to handle
            handler: Function to handle the error
        """
        self._error_handlers[error_type] = handler
        logger.debug(f"Registered error handler for {error_type}")
    
    def handle_error(self, error: Exception, parent=None) -> None:
        """Handle an error by displaying appropriate UI feedback.
        
        Args:
            error: The exception to handle
            parent: Parent widget for UI dialogs
        """
        # Log the error
        logger.error(f"Error: {str(error)}")
        if hasattr(error, "__traceback__"):
            logger.debug(traceback.format_tb(error.__traceback__))
        
        # Handle SpotifyExtractorError specially
        if isinstance(error, SpotifyExtractorError):
            self._handle_spotify_extractor_error(error, parent)
        else:
            # For generic errors, show a general error dialog
            self._show_error_dialog(
                "Application Error",
                f"An unexpected error occurred: {str(error)}",
                QMessageBox.Icon.Critical,
                parent
            )
    
    def _handle_spotify_extractor_error(self, error: SpotifyExtractorError, parent=None) -> None:
        """Handle a SpotifyExtractorError based on its type.
        
        Args:
            error: The SpotifyExtractorError to handle
            parent: Parent widget for UI dialogs
        """
        # Get the appropriate handler or use default
        handler = self._error_handlers.get(error.error_type, self._handle_general_error)
        handler(error, parent)
    
    def _handle_general_error(self, error: SpotifyExtractorError, parent=None) -> None:
        """Handle a general SpotifyExtractorError.
        
        Args:
            error: The error to handle
            parent: Parent widget for UI dialogs
        """
        self._show_error_dialog(
            "Error",
            f"An error occurred: {error.message}",
            QMessageBox.Icon.Warning,
            parent
        )
    
    def _handle_auth_error(self, error: SpotifyExtractorError, parent=None) -> None:
        """Handle authentication errors.
        
        Args:
            error: The error to handle
            parent: Parent widget for UI dialogs
        """
        self._show_error_dialog(
            "Authentication Error",
            f"Failed to authenticate with Spotify: {error.message}\n\n"
            "Please check your API credentials in the settings.",
            QMessageBox.Icon.Critical,
            parent
        )
    
    def _handle_validation_error(self, error: SpotifyExtractorError, parent=None) -> None:
        """Handle validation errors.
        
        Args:
            error: The error to handle
            parent: Parent widget for UI dialogs
        """
        self._show_error_dialog(
            "Invalid Input",
            f"Validation error: {error.message}",
            QMessageBox.Icon.Warning,
            parent
        )
    
    def _handle_api_error(self, error: SpotifyExtractorError, parent=None) -> None:
        """Handle Spotify API errors.
        
        Args:
            error: The error to handle
            parent: Parent widget for UI dialogs
        """
        self._show_error_dialog(
            "API Error",
            f"Spotify API error: {error.message}\n\n"
            "This might be due to API rate limits or service unavailability.",
            QMessageBox.Icon.Warning,
            parent
        )
    
    def _handle_not_found_error(self, error: SpotifyExtractorError, parent=None) -> None:
        """Handle not found errors.
        
        Args:
            error: The error to handle
            parent: Parent widget for UI dialogs
        """
        self._show_error_dialog(
            "Not Found",
            f"The requested playlist could not be found: {error.message}",
            QMessageBox.Icon.Warning,
            parent
        )
    
    def _handle_access_error(self, error: SpotifyExtractorError, parent=None) -> None:
        """Handle access denied errors.
        
        Args:
            error: The error to handle
            parent: Parent widget for UI dialogs
        """
        self._show_error_dialog(
            "Access Denied",
            f"Access denied: {error.message}\n\n"
            "The playlist might be private or require additional permissions.",
            QMessageBox.Icon.Warning,
            parent
        )
    
    def _handle_env_error(self, error: SpotifyExtractorError, parent=None) -> None:
        """Handle environment configuration errors.
        
        Args:
            error: The error to handle
            parent: Parent widget for UI dialogs
        """
        self._show_error_dialog(
            "Configuration Error",
            f"Environment configuration error: {error.message}\n\n"
            "Please check your environment variables or .env file.",
            QMessageBox.Icon.Critical,
            parent
        )
    
    def _handle_metadata_error(self, error: SpotifyExtractorError, parent=None) -> None:
        """Handle metadata errors.
        
        Args:
            error: The error to handle
            parent: Parent widget for UI dialogs
        """
        self._show_error_dialog(
            "Metadata Error",
            f"Error processing playlist metadata: {error.message}",
            QMessageBox.Icon.Warning,
            parent
        )
    
    def _handle_initialization_error(self, error: SpotifyExtractorError, parent=None) -> None:
        """Handle initialization errors.
        
        Args:
            error: The error to handle
            parent: Parent widget for UI dialogs
        """
        self._show_error_dialog(
            "Initialization Error",
            f"Failed to initialize: {error.message}\n\n"
            "The application may not function correctly.",
            QMessageBox.Icon.Critical,
            parent
        )
    
    def _show_error_dialog(self, title: str, message: str, icon: QMessageBox.Icon, parent=None) -> None:
        """Show an error dialog with the specified details.
        
        Args:
            title: Dialog title
            message: Error message
            icon: Dialog icon
            parent: Parent widget
        """
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec_() 