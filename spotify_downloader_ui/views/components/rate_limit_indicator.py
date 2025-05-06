"""
Rate limiting indicator component.

This component provides a visual representation of API rate limits,
showing current usage, remaining requests, and reset time information.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Union
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QFrame, QSizePolicy, QToolTip
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QSize, QTimer, QEvent, QPoint, QObject
)
from PySide6.QtGui import (
    QColor, QPalette, QFont, QMouseEvent, QIcon
)

logger = logging.getLogger(__name__)

class RateLimitIndicator(QWidget):
    """Widget for displaying API rate limit information."""
    
    # Rates
    RATE_NORMAL = 0   # Normal rate
    RATE_WARNING = 1  # Getting close to the limit
    RATE_DANGER = 2   # Very close to or at the limit
    
    def __init__(self, parent=None):
        """Initialize the rate limit indicator widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Rate limit data
        self._limit = 0
        self._remaining = 0
        self._used = 0
        self._reset_time = None
        self._endpoint = "API"
        
        # Appearance
        self._normal_color = QColor(76, 175, 80)  # Green
        self._warning_color = QColor(255, 152, 0)  # Orange
        self._danger_color = QColor(244, 67, 54)   # Red
        
        # Warning thresholds (percentage of limit remaining)
        self._warning_threshold = 30  # 30% remaining
        self._danger_threshold = 10   # 10% remaining
        
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(1000)  # Update every second
        self._update_timer.timeout.connect(self._update_display)
        
        self._init_ui()
        
        # Enable tooltip events
        self.setMouseTracking(True)
        self.installEventFilter(self)
        
        logger.debug("Rate limit indicator initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Rate limit indicator bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #f5f5f5;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        
        layout.addWidget(self.progress_bar)
        
        # Info layout
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        
        # Endpoint label
        self.endpoint_label = QLabel(self._endpoint)
        self.endpoint_label.setObjectName("endpoint_label")
        font = self.endpoint_label.font()
        font.setPointSize(8)
        self.endpoint_label.setFont(font)
        info_layout.addWidget(self.endpoint_label)
        
        # Spacer
        info_layout.addStretch(1)
        
        # Rate limit info
        self.rate_info_label = QLabel("0/0")
        self.rate_info_label.setObjectName("rate_info_label")
        font = self.rate_info_label.font()
        font.setPointSize(8)
        self.rate_info_label.setFont(font)
        info_layout.addWidget(self.rate_info_label)
        
        # Reset time info
        self.reset_label = QLabel("")
        self.reset_label.setObjectName("reset_label")
        font = self.reset_label.font()
        font.setPointSize(8)
        self.reset_label.setFont(font)
        info_layout.addWidget(self.reset_label)
        
        layout.addLayout(info_layout)
    
    def set_rate_limit_info(self, limit: int, remaining: int, 
                          reset_time: Union[int, datetime, None] = None,
                          endpoint: str = None):
        """Set the rate limit information.
        
        Args:
            limit: Total request limit
            remaining: Remaining requests
            reset_time: Time when the limit resets (timestamp or datetime)
            endpoint: API endpoint description
        """
        self._limit = max(1, limit)  # Ensure limit is at least 1
        self._remaining = max(0, min(remaining, self._limit))  # Clamp remaining between 0 and limit
        self._used = self._limit - self._remaining
        
        # Convert reset time to datetime if it's a timestamp
        if reset_time is not None:
            if isinstance(reset_time, int) or isinstance(reset_time, float):
                self._reset_time = datetime.fromtimestamp(reset_time)
            else:
                self._reset_time = reset_time
        else:
            self._reset_time = None
            
        # Update endpoint if provided
        if endpoint:
            self._endpoint = endpoint
            self.endpoint_label.setText(endpoint)
        
        # Update display
        self._update_display()
        
        # Start timer if reset time is in the future
        if self._reset_time and self._reset_time > datetime.now():
            self._update_timer.start()
        else:
            self._update_timer.stop()
    
    def _update_display(self):
        """Update the visual display based on current rate limit data."""
        # Update progress bar
        if self._limit > 0:
            percent_remaining = (self._remaining / self._limit) * 100
            self.progress_bar.setValue(int(percent_remaining))
            
            # Update color based on threshold
            if percent_remaining <= self._danger_threshold:
                status = self.RATE_DANGER
                color = self._danger_color
            elif percent_remaining <= self._warning_threshold:
                status = self.RATE_WARNING
                color = self._warning_color
            else:
                status = self.RATE_NORMAL
                color = self._normal_color
                
            # Update progress bar color
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #f5f5f5;
                    border: none;
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background-color: {color.name()};
                    border-radius: 2px;
                }}
            """)
        else:
            self.progress_bar.setValue(100)
            
        # Update rate info text
        self.rate_info_label.setText(f"{self._remaining}/{self._limit}")
        
        # Update reset time
        if self._reset_time:
            now = datetime.now()
            if self._reset_time > now:
                # Calculate time remaining
                time_diff = self._reset_time - now
                minutes = time_diff.seconds // 60
                seconds = time_diff.seconds % 60
                
                # Display differently based on time remaining
                if minutes > 0:
                    reset_text = f"Resets in {minutes}m {seconds}s"
                else:
                    reset_text = f"Resets in {seconds}s"
                
                self.reset_label.setText(reset_text)
            else:
                # Reset time has passed
                self.reset_label.setText("Reset time passed")
                self._update_timer.stop()
        else:
            self.reset_label.setText("")
    
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Filter events to show custom tooltip.
        
        Args:
            watched: The object being watched
            event: The event
            
        Returns:
            True if the event was handled, False otherwise
        """
        if watched == self and event.type() == QEvent.Type.ToolTip:
            # Create detailed tooltip text
            tooltip_text = f"<b>{self._endpoint} Rate Limits</b><br>"
            tooltip_text += f"Limit: {self._limit} requests<br>"
            tooltip_text += f"Used: {self._used} requests<br>"
            tooltip_text += f"Remaining: {self._remaining} requests<br>"
            
            if self._reset_time:
                # Format reset time
                time_str = self._reset_time.strftime("%H:%M:%S")
                tooltip_text += f"Reset Time: {time_str}"
            
            # Show custom tooltip
            QToolTip.showText(event.globalPosition().toPoint(), tooltip_text)
            return True
            
        return super().eventFilter(watched, event)


class MultiRateLimitIndicator(QWidget):
    """Widget for displaying multiple API rate limits."""
    
    def __init__(self, parent=None):
        """Initialize the multi-rate limit indicator widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store rate limit indicators by endpoint
        self._indicators = {}
        
        self._init_ui()
        
        logger.debug("Multi-rate limit indicator initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(10)
        
        # Title label
        title_label = QLabel("API Rate Limits")
        title_label.setObjectName("title_label")
        font = title_label.font()
        font.setBold(True)
        title_label.setFont(font)
        self._layout.addWidget(title_label)
        
        # Add a frame to contain the indicators
        self._container = QFrame()
        self._container.setFrameShape(QFrame.Shape.NoFrame)
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(8)
        
        self._layout.addWidget(self._container)
    
    def update_rate_limit(self, endpoint: str, limit: int, remaining: int,
                        reset_time: Union[int, datetime, None] = None):
        """Update rate limit information for a specific endpoint.
        
        Args:
            endpoint: API endpoint description
            limit: Total request limit
            remaining: Remaining requests
            reset_time: Time when the limit resets (timestamp or datetime)
        """
        # Create indicator if it doesn't exist
        if endpoint not in self._indicators:
            indicator = RateLimitIndicator()
            self._indicators[endpoint] = indicator
            self._container_layout.addWidget(indicator)
        
        # Update the indicator
        self._indicators[endpoint].set_rate_limit_info(
            limit=limit,
            remaining=remaining,
            reset_time=reset_time,
            endpoint=endpoint
        )
    
    def clear(self):
        """Clear all rate limit indicators."""
        # Remove and delete all indicators
        for endpoint, indicator in self._indicators.items():
            self._container_layout.removeWidget(indicator)
            indicator.deleteLater()
        
        # Clear dictionary
        self._indicators = {} 