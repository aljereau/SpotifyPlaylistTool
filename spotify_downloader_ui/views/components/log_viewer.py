"""
Log Viewer component for displaying and filtering log messages.
"""

import logging
import re
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QLineEdit, QToolBar, QFrame,
    QCheckBox, QSplitter, QMenu, QToolButton, QFileDialog, 
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat, QAction, QIcon, QTextDocument, QAction, QAction

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class LogEntry:
    """Represents a single log entry."""
    
    def __init__(self, 
                 timestamp: datetime,
                 level: LogLevel,
                 message: str,
                 source: str = "",
                 category: str = ""):
        """Initialize a log entry.
        
        Args:
            timestamp: Timestamp of the log entry
            level: Log severity level
            message: Log message text
            source: Source of the log (e.g., component name)
            category: Log category for grouping
        """
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.source = source
        self.category = category
        self.group_id = None  # For collapsible groups
    
    @property
    def formatted_timestamp(self) -> str:
        """Get formatted timestamp string.
        
        Returns:
            Formatted timestamp
        """
        return self.timestamp.strftime("%H:%M:%S.%f")[:-3]
    
    @property
    def level_name(self) -> str:
        """Get the level name.
        
        Returns:
            Level name string
        """
        return self.level.name
    
    @property
    def display_text(self) -> str:
        """Get full formatted log entry text.
        
        Returns:
            Formatted log entry
        """
        source_text = f"[{self.source}] " if self.source else ""
        category_text = f"({self.category}) " if self.category else ""
        
        return f"{self.formatted_timestamp} {self.level_name}: {source_text}{category_text}{self.message}"

class LogGroup:
    """Represents a group of related log entries."""
    
    def __init__(self, title: str, is_collapsible: bool = True):
        """Initialize a log group.
        
        Args:
            title: Group title
            is_collapsible: Whether the group can be collapsed
        """
        self.title = title
        self.is_collapsible = is_collapsible
        self.entries = []
        self.is_collapsed = False
        self.id = id(self)  # Unique ID for the group

class LogViewer(QWidget):
    """Advanced log viewer component with filtering and searching."""
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the log viewer.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        super().__init__()
        
        self.config_service = config_service
        self.error_service = error_service
        
        # Log storage
        self.log_entries = []
        self.log_groups = {}
        self.current_group = None
        
        # Log display settings
        self.max_entries = 1000
        self.auto_scroll = True
        self.last_scroll_position = 0
        self.active_filters = {
            'level': LogLevel.DEBUG,  # Show all levels at or above this
            'search_text': '',
            'source': '',
            'category': ''
        }
        
        # UI state
        self.is_searching = False
        self.search_results = []
        self.current_result_index = -1
        
        # Highlighting formats
        self.highlight_formats = self._create_highlight_formats()
        
        self._init_ui()
        
        logger.info("Log viewer initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        # Filter controls
        filter_label = QLabel("Level:")
        header_layout.addWidget(filter_label)
        
        self.level_combo = QComboBox()
        self.level_combo.addItem("DEBUG", LogLevel.DEBUG.value)
        self.level_combo.addItem("INFO", LogLevel.INFO.value)
        self.level_combo.addItem("WARNING", LogLevel.WARNING.value)
        self.level_combo.addItem("ERROR", LogLevel.ERROR.value)
        self.level_combo.addItem("CRITICAL", LogLevel.CRITICAL.value)
        self.level_combo.setCurrentIndex(1)  # Default to INFO
        self.level_combo.currentIndexChanged.connect(self._on_level_filter_changed)
        header_layout.addWidget(self.level_combo)
        
        # Search box
        header_layout.addWidget(QLabel("Search:"))
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search logs...")
        self.search_box.returnPressed.connect(self._on_search)
        self.search_box.textChanged.connect(self._on_search_text_changed)
        header_layout.addWidget(self.search_box)
        
        self.search_next_button = QPushButton("Next")
        self.search_next_button.clicked.connect(self._on_search_next)
        self.search_next_button.setEnabled(False)
        header_layout.addWidget(self.search_next_button)
        
        self.search_prev_button = QPushButton("Prev")
        self.search_prev_button.clicked.connect(self._on_search_prev)
        self.search_prev_button.setEnabled(False)
        header_layout.addWidget(self.search_prev_button)
        
        # Advanced filters button
        self.advanced_filters_button = QToolButton()
        self.advanced_filters_button.setText("Filters")
        self.advanced_filters_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        # Create filter menu
        self.filter_menu = QMenu(self)
        
        # Source filter
        self.source_action = QAction("Filter by Source", self)
        self.source_action.setCheckable(True)
        self.filter_menu.addAction(self.source_action)
        
        # Category filter
        self.category_action = QAction("Filter by Category", self)
        self.category_action.setCheckable(True)
        self.filter_menu.addAction(self.category_action)
        
        # Add separator
        self.filter_menu.addSeparator()
        
        # Show debug sources
        self.show_debug_action = QAction("Show Debug Sources", self)
        self.show_debug_action.setCheckable(True)
        self.show_debug_action.setChecked(True)
        self.filter_menu.addAction(self.show_debug_action)
        
        self.advanced_filters_button.setMenu(self.filter_menu)
        header_layout.addWidget(self.advanced_filters_button)
        
        # Add controls to main layout
        main_layout.addLayout(header_layout)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.log_display.setStyleSheet("font-family: monospace;")
        self.log_display.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)
        main_layout.addWidget(self.log_display)
        
        # Bottom toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # Clear button
        self.clear_action = QAction("Clear", self)
        self.clear_action.triggered.connect(self._on_clear)
        toolbar.addAction(self.clear_action)
        
        # Auto-scroll toggle
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.stateChanged.connect(self._on_auto_scroll_changed)
        toolbar.addWidget(self.auto_scroll_check)
        
        # Group toggle
        self.group_check = QCheckBox("Group logs")
        self.group_check.setChecked(False)
        self.group_check.stateChanged.connect(self._on_group_changed)
        toolbar.addWidget(self.group_check)
        
        # Expand/collapse groups
        self.expand_all_action = QAction("Expand All", self)
        self.expand_all_action.triggered.connect(self._on_expand_all)
        toolbar.addAction(self.expand_all_action)
        
        self.collapse_all_action = QAction("Collapse All", self)
        self.collapse_all_action.triggered.connect(self._on_collapse_all)
        toolbar.addAction(self.collapse_all_action)
        
        # Spacer
        toolbar.addSeparator()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        # Export button
        self.export_action = QAction("Export Logs", self)
        self.export_action.triggered.connect(self._on_export)
        toolbar.addAction(self.export_action)
        
        main_layout.addWidget(toolbar)
        
        # Set up auto-scroll timer
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self._check_auto_scroll)
        self.scroll_timer.start(500)  # Check every 500 ms
    
    def _create_highlight_formats(self) -> Dict[str, QTextCharFormat]:
        """Create text formats for highlighting.
        
        Returns:
            Dictionary of named formats
        """
        formats = {}
        
        # Log level formats
        debug_format = QTextCharFormat()
        debug_format.setForeground(QColor(100, 100, 100))  # Gray
        formats['DEBUG'] = debug_format
        
        info_format = QTextCharFormat()
        info_format.setForeground(QColor(0, 0, 0))  # Black (default)
        formats['INFO'] = info_format
        
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(200, 150, 0))  # Orange
        formats['WARNING'] = warning_format
        
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(200, 0, 0))  # Red
        formats['ERROR'] = error_format
        
        critical_format = QTextCharFormat()
        critical_format.setForeground(QColor(200, 0, 0))  # Red
        critical_format.setFontWeight(700)  # Bold
        formats['CRITICAL'] = critical_format
        
        # Search highlight
        search_format = QTextCharFormat()
        search_format.setBackground(QColor(255, 255, 0))  # Yellow
        search_format.setForeground(QColor(0, 0, 0))  # Black text
        formats['SEARCH'] = search_format
        
        # Current search result
        current_search_format = QTextCharFormat()
        current_search_format.setBackground(QColor(255, 165, 0))  # Orange
        current_search_format.setForeground(QColor(0, 0, 0))  # Black text
        formats['CURRENT_SEARCH'] = current_search_format
        
        # Timestamp format
        timestamp_format = QTextCharFormat()
        timestamp_format.setForeground(QColor(0, 100, 0))  # Dark green
        formats['TIMESTAMP'] = timestamp_format
        
        # Group header
        group_format = QTextCharFormat()
        group_format.setFontWeight(700)  # Bold
        group_format.setBackground(QColor(230, 230, 230))  # Light gray
        formats['GROUP'] = group_format
        
        return formats
    
    def add_log_entry(self, 
                     level: LogLevel, 
                     message: str, 
                     source: str = "", 
                     category: str = "") -> None:
        """Add a new log entry.
        
        Args:
            level: Log severity level
            message: Log message text
            source: Source of the log (e.g., component name)
            category: Log category for grouping
        """
        # Create entry
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            source=source,
            category=category
        )
        
        # Add to group if active
        if self.current_group:
            entry.group_id = self.current_group.id
            self.current_group.entries.append(entry)
        
        # Add to main log list
        self.log_entries.append(entry)
        
        # Trim if exceeding max
        while len(self.log_entries) > self.max_entries:
            self.log_entries.pop(0)
        
        # Update display
        self._update_log_display()
    
    def start_group(self, title: str, is_collapsible: bool = True) -> None:
        """Start a new log group.
        
        Args:
            title: Group title
            is_collapsible: Whether the group can be collapsed
        """
        group = LogGroup(title, is_collapsible)
        self.log_groups[group.id] = group
        self.current_group = group
        
        # Add group header as special log entry
        self.add_log_entry(
            level=LogLevel.INFO,
            message=f"GROUP: {title}",
            source="SYSTEM",
            category="GROUP_HEADER"
        )
    
    def end_group(self) -> None:
        """End the current log group."""
        self.current_group = None
    
    def clear_logs(self) -> None:
        """Clear all logs."""
        self.log_entries = []
        self.log_groups = {}
        self.current_group = None
        self.log_display.clear()
    
    def export_logs(self, file_path: str) -> bool:
        """Export logs to a text file.
        
        Args:
            file_path: Path to save the log file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                for entry in self.log_entries:
                    f.write(f"{entry.display_text}\n")
            return True
        except Exception as e:
            self.error_service.show_error(
                title="Export Error",
                message=f"Failed to export logs: {str(e)}"
            )
            return False
    
    def _update_log_display(self) -> None:
        """Update the log display with current entries and filters."""
        # Remember cursor position if not auto-scrolling
        if not self.auto_scroll:
            self.last_scroll_position = self.log_display.verticalScrollBar().value()
        
        # Clear and rebuild document
        self.log_display.clear()
        
        # Get visible entries based on filters
        visible_entries = self._get_filtered_entries()
        
        # Create document with formatting
        cursor = self.log_display.textCursor()
        
        # Track if we're in a collapsed group
        in_collapsed_group = False
        current_group_id = None
        
        for entry in visible_entries:
            # Check if this is a new group or the end of a group
            if entry.group_id != current_group_id:
                in_collapsed_group = False
                current_group_id = entry.group_id
                
                if entry.group_id in self.log_groups:
                    group = self.log_groups[entry.group_id]
                    in_collapsed_group = group.is_collapsed
            
            # Skip entries in collapsed groups (except the header)
            if in_collapsed_group and "GROUP_HEADER" not in entry.category:
                continue
            
            # Format timestamp
            cursor.insertText(entry.formatted_timestamp + " ", self.highlight_formats['TIMESTAMP'])
            
            # Format level
            level_format = self.highlight_formats.get(entry.level_name, self.highlight_formats['INFO'])
            cursor.insertText(entry.level_name + ": ", level_format)
            
            # Format source and category if present
            if entry.source:
                cursor.insertText(f"[{entry.source}] ")
            
            if entry.category and entry.category != "GROUP_HEADER":
                cursor.insertText(f"({entry.category}) ")
            
            # Special formatting for group headers
            if entry.category == "GROUP_HEADER":
                group_id = entry.group_id
                if group_id in self.log_groups:
                    group = self.log_groups[group_id]
                    collapse_indicator = "[-]" if not group.is_collapsed else "[+]"
                    cursor.insertText(f"{collapse_indicator} {entry.message[7:]}", self.highlight_formats['GROUP'])
                else:
                    cursor.insertText(entry.message, level_format)
            else:
                # Format message with search highlighting if needed
                if self.is_searching and self.active_filters['search_text']:
                    self._insert_highlighted_text(cursor, entry.message, level_format)
                else:
                    cursor.insertText(entry.message, level_format)
            
            cursor.insertBlock()
        
        # Auto-scroll to bottom if enabled
        if self.auto_scroll:
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )
        else:
            # Restore previous position
            self.log_display.verticalScrollBar().setValue(self.last_scroll_position)
    
    def _insert_highlighted_text(self, 
                                cursor: QTextCursor, 
                                text: str, 
                                base_format: QTextCharFormat) -> None:
        """Insert text with search highlighting.
        
        Args:
            cursor: Text cursor for insertion
            text: Text to insert
            base_format: Base format for non-highlighted text
        """
        search_text = self.active_filters['search_text']
        if not search_text:
            cursor.insertText(text, base_format)
            return
        
        # Find all occurrences of search text
        pattern = re.escape(search_text)
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        
        if not matches:
            cursor.insertText(text, base_format)
            return
        
        # Insert text with highlights
        last_end = 0
        for i, match in enumerate(matches):
            # Add text before the match
            if match.start() > last_end:
                cursor.insertText(text[last_end:match.start()], base_format)
            
            # Check if this is the current search result
            if i == self.current_result_index:
                cursor.insertText(text[match.start():match.end()], self.highlight_formats['CURRENT_SEARCH'])
            else:
                cursor.insertText(text[match.start():match.end()], self.highlight_formats['SEARCH'])
            
            last_end = match.end()
        
        # Add any remaining text after the last match
        if last_end < len(text):
            cursor.insertText(text[last_end:], base_format)
    
    def _get_filtered_entries(self) -> List[LogEntry]:
        """Get log entries filtered based on current settings.
        
        Returns:
            List of filtered log entries
        """
        # Filter by log level
        min_level = self.active_filters['level']
        filtered_entries = [
            entry for entry in self.log_entries
            if entry.level.value >= min_level.value
        ]
        
        # Apply text search if active
        if self.active_filters['search_text']:
            search_text = self.active_filters['search_text'].lower()
            filtered_entries = [
                entry for entry in filtered_entries
                if search_text in entry.message.lower()
            ]
        
        # Apply source filter if active
        if self.active_filters['source']:
            source = self.active_filters['source'].lower()
            filtered_entries = [
                entry for entry in filtered_entries
                if source in entry.source.lower()
            ]
        
        # Apply category filter if active
        if self.active_filters['category']:
            category = self.active_filters['category'].lower()
            filtered_entries = [
                entry for entry in filtered_entries
                if category in entry.category.lower()
            ]
        
        return filtered_entries
    
    def _search_logs(self) -> None:
        """Search logs for the current search text."""
        if not self.active_filters['search_text']:
            self.is_searching = False
            self.search_results = []
            self.current_result_index = -1
            self._update_search_buttons()
            return
        
        # Find all entries matching search
        search_text = self.active_filters['search_text'].lower()
        self.search_results = [
            i for i, entry in enumerate(self.log_entries)
            if search_text in entry.message.lower()
        ]
        
        # Update UI
        self.is_searching = True
        self.current_result_index = 0 if self.search_results else -1
        self._update_search_buttons()
        
        # Refresh display
        self._update_log_display()
    
    def _update_search_buttons(self) -> None:
        """Update state of search navigation buttons."""
        has_results = bool(self.search_results)
        self.search_next_button.setEnabled(has_results and self.current_result_index < len(self.search_results) - 1)
        self.search_prev_button.setEnabled(has_results and self.current_result_index > 0)
    
    def _check_auto_scroll(self) -> None:
        """Check if autoscroll should be active based on user scrolling behavior."""
        if not self.auto_scroll:
            return
            
        scrollbar = self.log_display.verticalScrollBar()
        
        # If user has scrolled away from bottom, temporarily disable auto-scroll
        if scrollbar.value() < scrollbar.maximum() - 50:
            self.auto_scroll = False
            self.auto_scroll_check.setChecked(False)
    
    @Slot(int)
    def _on_level_filter_changed(self, index: int) -> None:
        """Handle change in log level filter.
        
        Args:
            index: Index of selected level
        """
        # Update filter
        self.active_filters['level'] = LogLevel(self.level_combo.currentData())
        
        # Refresh display
        self._update_log_display()
    
    @Slot()
    def _on_search(self) -> None:
        """Handle search request."""
        self.active_filters['search_text'] = self.search_box.text()
        self._search_logs()
    
    @Slot(str)
    def _on_search_text_changed(self, text: str) -> None:
        """Handle search text changes.
        
        Args:
            text: Current search text
        """
        if not text:
            # Clear search
            self.active_filters['search_text'] = ''
            self.is_searching = False
            self.search_results = []
            self.current_result_index = -1
            self._update_search_buttons()
            self._update_log_display()
    
    @Slot()
    def _on_search_next(self) -> None:
        """Navigate to next search result."""
        if not self.search_results:
            return
            
        if self.current_result_index < len(self.search_results) - 1:
            self.current_result_index += 1
            self._update_search_buttons()
            self._update_log_display()
    
    @Slot()
    def _on_search_prev(self) -> None:
        """Navigate to previous search result."""
        if not self.search_results or self.current_result_index <= 0:
            return
            
        self.current_result_index -= 1
        self._update_search_buttons()
        self._update_log_display()
    
    @Slot(int)
    def _on_auto_scroll_changed(self, state: int) -> None:
        """Handle change in auto-scroll state.
        
        Args:
            state: Checkbox state
        """
        self.auto_scroll = (state == Qt.CheckState.Checked.value)
        
        if self.auto_scroll:
            # Scroll to bottom
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )
    
    @Slot(int)
    def _on_group_changed(self, state: int) -> None:
        """Handle change in grouping state.
        
        Args:
            state: Checkbox state
        """
        # Toggle collapsed state of all groups
        for group in self.log_groups.values():
            group.is_collapsed = (state == Qt.CheckState.Checked.value)
        
        # Refresh display
        self._update_log_display()
    
    @Slot()
    def _on_expand_all(self) -> None:
        """Expand all collapsed groups."""
        for group in self.log_groups.values():
            group.is_collapsed = False
        
        self._update_log_display()
    
    @Slot()
    def _on_collapse_all(self) -> None:
        """Collapse all expanded groups."""
        for group in self.log_groups.values():
            group.is_collapsed = True
        
        self._update_log_display()
    
    @Slot()
    def _on_clear(self) -> None:
        """Handle clear button click."""
        self.clear_logs()
    
    @Slot()
    def _on_export(self) -> None:
        """Handle export button click."""
        # Show file save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            "",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            self.export_logs(file_path)
    
    @Slot(int)
    def _on_scroll_changed(self, value: int) -> None:
        """Handle scrollbar value changes.
        
        Args:
            value: New scrollbar value
        """
        scrollbar = self.log_display.verticalScrollBar()
        
        # If scrolled to bottom, enable auto-scroll
        if value >= scrollbar.maximum() - 10:
            self.auto_scroll = True
            self.auto_scroll_check.setChecked(True)
        
        # Remember position
        self.last_scroll_position = value 