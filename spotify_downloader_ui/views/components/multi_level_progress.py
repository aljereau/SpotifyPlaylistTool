"""
Multi-level progress indicator component.

This component displays multiple progress bars for different levels of a process:
1. Overall process progress
2. Per-playlist progress 
3. Current operation progress
"""

import logging
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QGroupBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPalette

logger = logging.getLogger(__name__)

class ProgressLevel:
    """Constants for progress levels."""
    OVERALL = 0
    PLAYLIST = 1
    OPERATION = 2

class ProgressState:
    """Constants for progress states."""
    IDLE = 0
    RUNNING = 1
    PAUSED = 2
    COMPLETED = 3
    ERROR = 4

class ProgressBarWidget(QProgressBar):
    """Enhanced progress bar with animation and states."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = ProgressState.IDLE
        self._error_message = ""
        self.setMinimumHeight(20)
        self._apply_state_style()
        
        # Setup animation
        self._animation = QPropertyAnimation(self, b"value")
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.setDuration(500)  # 500ms duration
    
    @Property(int)
    def animated_value(self):
        """Get the current value."""
        return self.value()
    
    @animated_value.setter
    def animated_value(self, value):
        """Set value with animation."""
        self.setValue(value)
    
    def set_value_animated(self, value):
        """Set the progress value with animation."""
        self._animation.stop()
        self._animation.setStartValue(self.value())
        self._animation.setEndValue(value)
        self._animation.start()
    
    def set_state(self, state: int, error_message: str = ""):
        """Set the progress bar state.
        
        Args:
            state: ProgressState enum value
            error_message: Error message if state is ERROR
        """
        self._state = state
        self._error_message = error_message
        self._apply_state_style()
        
        # Stop animation if not running
        if state != ProgressState.RUNNING:
            self._animation.stop()
    
    def _apply_state_style(self):
        """Apply styling based on current state."""
        palette = self.palette()
        
        if self._state == ProgressState.IDLE:
            # Light gray for idle
            palette.setColor(QPalette.ColorRole.Highlight, QColor(200, 200, 200))
            self.setFormat("%p%")
        elif self._state == ProgressState.RUNNING:
            # Blue for running
            palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            self.setFormat("%p%")
        elif self._state == ProgressState.PAUSED:
            # Amber for paused
            palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 191, 0))
            self.setFormat("PAUSED - %p%")
        elif self._state == ProgressState.COMPLETED:
            # Green for completed
            palette.setColor(QPalette.ColorRole.Highlight, QColor(50, 205, 50))
            self.setFormat("COMPLETED - %p%")
        elif self._state == ProgressState.ERROR:
            # Red for error
            palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 69, 0))
            error_text = self._error_message if self._error_message else "ERROR"
            self.setFormat(f"{error_text} - %p%")
        
        self.setPalette(palette)


class MultiLevelProgressIndicator(QWidget):
    """A widget for displaying multi-level progress indicators."""
    
    def __init__(self, parent=None):
        """Initialize the multi-level progress indicator.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.progress_bars = {}
        self.progress_labels = {}
        self.time_labels = {}
        self.phase_indicators = {}
        
        self._init_ui()
        
        logger.info("Multi-level progress indicator initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        
        # Overall progress
        overall_group = QGroupBox("Overall Progress")
        overall_layout = self._create_progress_level(
            overall_group, 
            "Overall Process", 
            ProgressLevel.OVERALL
        )
        main_layout.addWidget(overall_group)
        
        # Playlist progress
        playlist_group = QGroupBox("Playlist Progress")
        playlist_layout = self._create_progress_level(
            playlist_group, 
            "Current Playlist", 
            ProgressLevel.PLAYLIST
        )
        main_layout.addWidget(playlist_group)
        
        # Operation progress
        operation_group = QGroupBox("Operation Progress")
        operation_layout = self._create_progress_level(
            operation_group, 
            "Current Operation", 
            ProgressLevel.OPERATION
        )
        main_layout.addWidget(operation_group)
    
    def _create_progress_level(self, parent: QWidget, label_text: str, level: int) -> QVBoxLayout:
        """Create a progress level (progress bar + labels).
        
        Args:
            parent: Parent widget
            label_text: Label text
            level: Progress level constant
            
        Returns:
            Layout containing the progress components
        """
        layout = QVBoxLayout(parent)
        
        # Header with label, phases, and time
        header_layout = QHBoxLayout()
        
        # Label
        label = QLabel(label_text)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(label)
        self.progress_labels[level] = label
        
        # Phase indicator (dots showing phases)
        phase_frame = QFrame()
        phase_frame.setFrameShape(QFrame.Shape.NoFrame)
        phase_layout = QHBoxLayout(phase_frame)
        phase_layout.setContentsMargins(0, 0, 0, 0)
        phase_layout.setSpacing(5)
        
        # Create 5 phase dots
        self.phase_indicators[level] = []
        for i in range(5):
            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setFrameShape(QFrame.Shape.Box)
            dot.setFrameShadow(QFrame.Shadow.Plain)
            # Initial state - not active
            dot.setStyleSheet("background-color: #e0e0e0; border-radius: 5px;")
            
            phase_layout.addWidget(dot)
            self.phase_indicators[level].append(dot)
            
        header_layout.addWidget(phase_frame)
        
        # Time estimate label
        time_label = QLabel("--:--")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(time_label)
        self.time_labels[level] = time_label
        
        layout.addLayout(header_layout)
        
        # Progress bar
        progress_bar = ProgressBarWidget()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        layout.addWidget(progress_bar)
        self.progress_bars[level] = progress_bar
        
        return layout
    
    def update_progress(self, level: int, value: int, max_value: int, 
                       state: int = ProgressState.RUNNING, message: str = ""):
        """Update the progress bar for a specific level.
        
        Args:
            level: Progress level constant
            value: Current progress value
            max_value: Maximum progress value
            state: Progress state
            message: Message to display (replaces default label if provided)
        """
        if level not in self.progress_bars:
            logger.warning(f"Invalid progress level: {level}")
            return
        
        # Update progress bar
        progress_bar = self.progress_bars[level]
        if max_value > 0:
            percentage = min(100, int((value / max_value) * 100))
        else:
            percentage = 0
        
        # Animate the progress bar
        progress_bar.set_value_animated(percentage)
        
        # Set state
        progress_bar.set_state(state)
        
        # Update label if message provided
        if message:
            self.progress_labels[level].setText(message)
    
    def set_time_estimate(self, level: int, seconds_remaining: int):
        """Set the time estimate for a progress level.
        
        Args:
            level: Progress level constant
            seconds_remaining: Estimated seconds remaining
        """
        if level not in self.time_labels:
            return
            
        # Format time
        if seconds_remaining < 0:
            time_str = "--:--"
        elif seconds_remaining < 60:
            time_str = f"0:{seconds_remaining:02d}"
        elif seconds_remaining < 3600:
            minutes = seconds_remaining // 60
            seconds = seconds_remaining % 60
            time_str = f"{minutes}:{seconds:02d}"
        else:
            hours = seconds_remaining // 3600
            minutes = (seconds_remaining % 3600) // 60
            time_str = f"{hours}h {minutes}m"
            
        self.time_labels[level].setText(time_str)
    
    def set_phase_active(self, level: int, phase_index: int, active: bool = True):
        """Set a phase indicator as active/inactive.
        
        Args:
            level: Progress level constant
            phase_index: Phase index (0-based)
            active: Whether the phase is active
        """
        if level not in self.phase_indicators:
            return
            
        indicators = self.phase_indicators[level]
        if 0 <= phase_index < len(indicators):
            dot = indicators[phase_index]
            if active:
                dot.setStyleSheet("background-color: #2a82da; border-radius: 5px;")
            else:
                dot.setStyleSheet("background-color: #e0e0e0; border-radius: 5px;")
    
    def reset(self):
        """Reset all progress indicators."""
        for level in self.progress_bars:
            progress_bar = self.progress_bars[level]
            progress_bar.setValue(0)
            progress_bar.set_state(ProgressState.IDLE)
            
            # Reset time labels
            self.time_labels[level].setText("--:--")
            
            # Reset phase indicators
            for i, dot in enumerate(self.phase_indicators[level]):
                dot.setStyleSheet("background-color: #e0e0e0; border-radius: 5px;") 