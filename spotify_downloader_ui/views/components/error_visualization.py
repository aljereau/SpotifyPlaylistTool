"""
Error visualization component.

This component provides a visual representation of errors with details 
and suggestions for resolution.
"""

import logging
import traceback
from typing import Dict, List, Optional, Union, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QFrame, QSizePolicy, QSpacerItem, QScrollArea
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import (
    QIcon, QPixmap, QColor, QPalette, QFont, QTextCursor, 
    QTextCharFormat, QBrush
)

from .completion_animation import CrossAnimation

logger = logging.getLogger(__name__)

class ErrorVisualization(QWidget):
    """Widget for visualizing errors with details and suggestions."""
    
    # Signals
    retry_requested = Signal()
    close_requested = Signal()
    
    def __init__(self, parent=None):
        """Initialize the error visualization widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Error state
        self._error_type = ""
        self._error_message = ""
        self._error_details = ""
        self._suggestions = []
        
        self._init_ui()
        
        logger.debug("Error visualization initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        # Error icon/animation
        self.error_animation = CrossAnimation()
        self.error_animation.setFixedSize(48, 48)
        header_layout.addWidget(self.error_animation, 0, Qt.AlignmentFlag.AlignTop)
        
        # Error title and message
        title_layout = QVBoxLayout()
        
        self.error_type_label = QLabel("Error")
        self.error_type_label.setObjectName("error_type_label")
        font = self.error_type_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.error_type_label.setFont(font)
        title_layout.addWidget(self.error_type_label)
        
        self.error_message_label = QLabel("An error has occurred.")
        self.error_message_label.setObjectName("error_message_label")
        self.error_message_label.setWordWrap(True)
        title_layout.addWidget(self.error_message_label)
        
        header_layout.addLayout(title_layout, 1)
        main_layout.addLayout(header_layout)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        separator.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(separator)
        
        # Error details (in a scroll area)
        details_group_label = QLabel("Error Details")
        details_group_label.setObjectName("details_group_label")
        font = details_group_label.font()
        font.setBold(True)
        details_group_label.setFont(font)
        main_layout.addWidget(details_group_label)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMinimumHeight(100)
        self.details_text.setStyleSheet("background-color: #f5f5f5; border: 1px solid #e0e0e0;")
        main_layout.addWidget(self.details_text)
        
        # Suggestions
        suggestions_label = QLabel("Suggestions")
        suggestions_label.setObjectName("suggestions_label")
        font = suggestions_label.font()
        font.setBold(True)
        suggestions_label.setFont(font)
        main_layout.addWidget(suggestions_label)
        
        # Suggestions are added dynamically
        self.suggestions_layout = QVBoxLayout()
        main_layout.addLayout(self.suggestions_layout)
        
        # Spacer to push buttons to the bottom
        main_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, 
                                       QSizePolicy.Policy.Expanding))
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.retry_button = QPushButton("Retry")
        self.retry_button.clicked.connect(self.retry_requested)
        buttons_layout.addWidget(self.retry_button)
        
        buttons_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_requested)
        buttons_layout.addWidget(self.close_button)
        
        main_layout.addLayout(buttons_layout)
        
        # Start error animation
        self.error_animation.start()
    
    def set_error(self, error_type: str, error_message: str, error_details: str = "",
                 suggestions: List[str] = None):
        """Set the error information.
        
        Args:
            error_type: Type of error (e.g., "Network Error")
            error_message: Error message
            error_details: Detailed error information
            suggestions: List of suggestions for resolving the error
        """
        self._error_type = error_type
        self._error_message = error_message
        self._error_details = error_details
        self._suggestions = suggestions or []
        
        # Update UI
        self.error_type_label.setText(error_type)
        self.error_message_label.setText(error_message)
        
        # Format and set details
        self._set_formatted_details(error_details)
        
        # Update suggestions
        self._update_suggestions()
        
        # Restart animation
        self.error_animation.start()
    
    def set_from_exception(self, ex: Exception, title: str = "Error"):
        """Set error from an exception.
        
        Args:
            ex: Exception to display
            title: Error type/title
        """
        # Get exception details
        error_type = title or ex.__class__.__name__
        error_message = str(ex)
        error_details = "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        
        # Generate suggestions based on error type
        suggestions = self._generate_suggestions_for_exception(ex)
        
        self.set_error(error_type, error_message, error_details, suggestions)
    
    def _generate_suggestions_for_exception(self, ex: Exception) -> List[str]:
        """Generate suggestions based on exception type.
        
        Args:
            ex: Exception to analyze
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Add general suggestion
        suggestions.append("Try the operation again.")
        
        # Add specific suggestions based on exception type
        if isinstance(ex, ConnectionError) or "Connection" in ex.__class__.__name__:
            suggestions.append("Check your internet connection.")
            suggestions.append("Verify that the Spotify API is accessible.")
            suggestions.append("Check if your firewall is blocking connections.")
        elif isinstance(ex, TimeoutError) or "Timeout" in ex.__class__.__name__:
            suggestions.append("The operation timed out. Try again later when the server might be less busy.")
            suggestions.append("Check your internet connection speed.")
        elif isinstance(ex, ValueError) or "Value" in ex.__class__.__name__:
            suggestions.append("Check that all input values are correct.")
            suggestions.append("Verify that the Spotify URL is valid and properly formatted.")
        elif isinstance(ex, PermissionError) or "Permission" in ex.__class__.__name__ or "Access" in ex.__class__.__name__:
            suggestions.append("Check that you have the necessary permissions to access these resources.")
            suggestions.append("Verify your Spotify credentials.")
        elif "Auth" in ex.__class__.__name__:
            suggestions.append("Verify your Spotify API credentials.")
            suggestions.append("You may need to reauthenticate with Spotify.")
        
        return suggestions
    
    def _set_formatted_details(self, details: str):
        """Format and set the error details with syntax highlighting.
        
        Args:
            details: Error details text
        """
        self.details_text.clear()
        
        # Set a monospace font
        font = QFont("Consolas, Courier New, monospace")
        font.setPointSize(9)
        self.details_text.setFont(font)
        
        if not details:
            self.details_text.setPlainText("No additional details available.")
            return
        
        cursor = QTextCursor(self.details_text.document())
        
        # Define text formats
        normal_format = QTextCharFormat()
        normal_format.setForeground(QBrush(QColor("#333333")))
        
        error_format = QTextCharFormat()
        error_format.setForeground(QBrush(QColor("#d32f2f")))
        error_format.setFontWeight(QFont.Weight.Bold)
        
        path_format = QTextCharFormat()
        path_format.setForeground(QBrush(QColor("#0d47a1")))
        
        # Split lines and format
        lines = details.split('\n')
        for i, line in enumerate(lines):
            # Apply different formatting based on line content
            if "Error:" in line or "Exception:" in line:
                cursor.insertText(line, error_format)
            elif line.startswith("  File ") or ".py" in line:
                cursor.insertText(line, path_format)
            else:
                cursor.insertText(line, normal_format)
            
            # Add newline (except for the last line)
            if i < len(lines) - 1:
                cursor.insertBlock()
    
    def _update_suggestions(self):
        """Update the suggestions list in the UI."""
        # Clear existing suggestions
        while self.suggestions_layout.count():
            item = self.suggestions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # No suggestions
        if not self._suggestions:
            no_suggestions = QLabel("No specific suggestions available.")
            no_suggestions.setStyleSheet("color: #757575;")
            self.suggestions_layout.addWidget(no_suggestions)
            return
        
        # Add each suggestion with a bullet point
        for suggestion in self._suggestions:
            suggestion_layout = QHBoxLayout()
            
            # Bullet point
            bullet = QLabel("•")
            bullet.setStyleSheet("color: #2196F3; font-weight: bold;")
            suggestion_layout.addWidget(bullet)
            
            # Suggestion text
            text = QLabel(suggestion)
            text.setWordWrap(True)
            suggestion_layout.addWidget(text, 1)
            
            self.suggestions_layout.addLayout(suggestion_layout)
    
    def clear(self):
        """Clear all error information."""
        self.error_type_label.setText("Error")
        self.error_message_label.setText("")
        self.details_text.clear()
        
        # Clear suggestions
        while self.suggestions_layout.count():
            item = self.suggestions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater() 