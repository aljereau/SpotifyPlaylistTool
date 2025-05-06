"""
Phase indicator component.

This component provides a visual representation of operation phases,
showing completed phases, the current phase, and upcoming phases.
"""

import logging
from typing import List, Dict, Optional, Tuple
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPalette, QFont

logger = logging.getLogger(__name__)

class PhaseIndicator(QWidget):
    """Widget for displaying operation phases and progress."""
    
    def __init__(self, parent=None):
        """Initialize the phase indicator widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Phase data
        self._phases = []
        self._current_phase_index = -1
        self._phase_indicators = []
        self._phase_labels = []
        self._connector_lines = []
        
        # Appearance
        self._completed_color = QColor(76, 175, 80)  # Green
        self._current_color = QColor(33, 150, 243)   # Blue
        self._upcoming_color = QColor(224, 224, 224) # Light gray
        self._connector_color = QColor(224, 224, 224) # Light gray
        self._connector_active_color = QColor(76, 175, 80) # Green
        
        self._indicator_size = 24
        self._connector_height = 2
        
        self._init_ui()
        
        logger.debug("Phase indicator initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        self._main_layout = QHBoxLayout(self)
        self._main_layout.setContentsMargins(0, 10, 0, 10)
        self._main_layout.setSpacing(0)
        
        # Will be populated when phases are set
    
    def set_phases(self, phases: List[str]):
        """Set the operation phases.
        
        Args:
            phases: List of phase names/descriptions
        """
        # Clear existing phase indicators
        self._clear_phases()
        
        # Store phases
        self._phases = phases
        self._current_phase_index = -1
        
        # Create phase indicators
        for i, phase in enumerate(phases):
            # Create phase widget
            phase_widget = QWidget()
            phase_layout = QVBoxLayout(phase_widget)
            phase_layout.setContentsMargins(0, 0, 0, 0)
            phase_layout.setSpacing(5)
            
            # Circle indicator
            circle = QFrame()
            circle.setFixedSize(self._indicator_size, self._indicator_size)
            circle.setObjectName(f"phase_indicator_{i}")
            circle.setFrameShape(QFrame.Shape.NoFrame)
            circle.setStyleSheet(f"""
                #phase_indicator_{i} {{
                    background-color: {self._upcoming_color.name()};
                    border-radius: {self._indicator_size // 2}px;
                }}
            """)
            
            # Label
            label = QLabel(phase)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            label.setFixedWidth(80)  # Fixed width for alignment
            
            # Add to layout
            phase_layout.addWidget(circle, 0, Qt.AlignmentFlag.AlignCenter)
            phase_layout.addWidget(label, 0, Qt.AlignmentFlag.AlignCenter)
            
            # Add to main layout
            self._main_layout.addWidget(phase_widget)
            
            # Store references
            self._phase_indicators.append(circle)
            self._phase_labels.append(label)
            
            # Add connector line between phases (except after last phase)
            if i < len(phases) - 1:
                connector = QFrame()
                connector.setFrameShape(QFrame.Shape.HLine)
                connector.setFixedHeight(self._connector_height)
                connector.setStyleSheet(f"background-color: {self._connector_color.name()};")
                self._main_layout.addWidget(connector, 0, Qt.AlignmentFlag.AlignCenter)
                self._connector_lines.append(connector)
        
        # Set initial state
        self.set_current_phase(0)
    
    def _clear_phases(self):
        """Clear all phase indicators."""
        # Remove all widgets from layout
        while self._main_layout.count():
            item = self._main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear lists
        self._phase_indicators = []
        self._phase_labels = []
        self._connector_lines = []
    
    def set_current_phase(self, phase_index: int):
        """Set the current active phase.
        
        Args:
            phase_index: Index of the current phase (0-based)
        """
        if not self._phases or phase_index < 0 or phase_index >= len(self._phases):
            logger.warning(f"Invalid phase index: {phase_index}")
            return
        
        # Store current phase
        self._current_phase_index = phase_index
        
        # Update indicator styles
        for i, indicator in enumerate(self._phase_indicators):
            if i < phase_index:
                # Completed phase
                indicator.setStyleSheet(f"""
                    #phase_indicator_{i} {{
                        background-color: {self._completed_color.name()};
                        border-radius: {self._indicator_size // 2}px;
                    }}
                """)
            elif i == phase_index:
                # Current phase
                indicator.setStyleSheet(f"""
                    #phase_indicator_{i} {{
                        background-color: {self._current_color.name()};
                        border-radius: {self._indicator_size // 2}px;
                    }}
                """)
            else:
                # Upcoming phase
                indicator.setStyleSheet(f"""
                    #phase_indicator_{i} {{
                        background-color: {self._upcoming_color.name()};
                        border-radius: {self._indicator_size // 2}px;
                    }}
                """)
        
        # Update connector lines
        for i, connector in enumerate(self._connector_lines):
            if i < phase_index:
                # Completed connector
                connector.setStyleSheet(f"background-color: {self._connector_active_color.name()};")
            else:
                # Upcoming connector
                connector.setStyleSheet(f"background-color: {self._connector_color.name()};")
    
    def get_current_phase(self) -> int:
        """Get the current phase index.
        
        Returns:
            Current phase index (0-based)
        """
        return self._current_phase_index
    
    def advance_phase(self):
        """Advance to the next phase."""
        if self._current_phase_index < len(self._phases) - 1:
            self.set_current_phase(self._current_phase_index + 1)
    
    def set_phase_colors(self, completed_color: QColor, current_color: QColor, 
                       upcoming_color: QColor):
        """Set the colors for different phase states.
        
        Args:
            completed_color: Color for completed phases
            current_color: Color for the current phase
            upcoming_color: Color for upcoming phases
        """
        self._completed_color = completed_color
        self._current_color = current_color
        self._upcoming_color = upcoming_color
        self._connector_active_color = completed_color
        
        # Update the current view
        if self._current_phase_index >= 0:
            self.set_current_phase(self._current_phase_index)
    
    def set_indicator_size(self, size: int):
        """Set the size of phase indicators.
        
        Args:
            size: Size in pixels
        """
        self._indicator_size = size
        
        # Update sizes of existing indicators
        for i, indicator in enumerate(self._phase_indicators):
            indicator.setFixedSize(size, size)
            indicator.setStyleSheet(f"""
                #phase_indicator_{i} {{
                    border-radius: {size // 2}px;
                }}
            """)


class AnimatedPhaseIndicator(PhaseIndicator):
    """Animated phase indicator with smooth transitions."""
    
    def __init__(self, parent=None):
        """Initialize the animated phase indicator.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Animation properties
        self._animations = []
        self._animation_duration = 500  # ms
        
        logger.debug("Animated phase indicator initialized")
    
    def set_current_phase(self, phase_index: int):
        """Set the current phase with animation.
        
        Args:
            phase_index: Index of the current phase (0-based)
        """
        if not self._phases or phase_index < 0 or phase_index >= len(self._phases):
            logger.warning(f"Invalid phase index: {phase_index}")
            return
        
        # Store previous and current phase
        prev_phase_index = self._current_phase_index
        self._current_phase_index = phase_index
        
        # Stop any running animations
        for animation in self._animations:
            if animation.state() == QPropertyAnimation.State.Running:
                animation.stop()
        
        # Clear animations list
        self._animations = []
        
        # Create and start animations for smooth transition
        for i, indicator in enumerate(self._phase_indicators):
            # Determine target color based on phase status
            if i < phase_index:
                target_color = self._completed_color
            elif i == phase_index:
                target_color = self._current_color
            else:
                target_color = self._upcoming_color
            
            # Create animation for this indicator
            self._animate_indicator_color(indicator, i, target_color)
        
        # Animate connector lines
        for i, connector in enumerate(self._connector_lines):
            if i < phase_index:
                # Completed connector
                connector.setStyleSheet(f"background-color: {self._connector_active_color.name()};")
            else:
                # Upcoming connector
                connector.setStyleSheet(f"background-color: {self._connector_color.name()};")
    
    def _animate_indicator_color(self, indicator: QFrame, index: int, target_color: QColor):
        """Animate the color change of an indicator.
        
        Args:
            indicator: The indicator frame
            index: Index of the indicator
            target_color: Target color
        """
        # We need to use stylesheet animation workarounds since Qt doesn't directly
        # support color property animations in stylesheets
        
        # Create animation
        animation = QPropertyAnimation(self, b"dummy")
        animation.setDuration(self._animation_duration)
        animation.setStartValue(0)
        animation.setEndValue(100)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Current color - parse from stylesheet
        style = indicator.styleSheet()
        current_color = self._extract_color_from_stylesheet(style)
        
        # Update the color at each animation step
        def update_color(value):
            # Interpolate color based on animation progress
            progress = value / 100.0
            r = int(current_color.red() + (target_color.red() - current_color.red()) * progress)
            g = int(current_color.green() + (target_color.green() - current_color.green()) * progress)
            b = int(current_color.blue() + (target_color.blue() - current_color.blue()) * progress)
            
            # Create interpolated color
            interpolated_color = QColor(r, g, b)
            
            # Update stylesheet
            indicator.setStyleSheet(f"""
                #phase_indicator_{index} {{
                    background-color: {interpolated_color.name()};
                    border-radius: {self._indicator_size // 2}px;
                }}
            """)
        
        # Connect value changed signal
        animation.valueChanged.connect(update_color)
        
        # Start animation
        animation.start()
        
        # Keep reference to prevent garbage collection
        self._animations.append(animation)
    
    def _extract_color_from_stylesheet(self, style: str) -> QColor:
        """Extract the background color from a stylesheet.
        
        Args:
            style: Stylesheet string
            
        Returns:
            Extracted color or default color
        """
        # Simple parsing to extract background-color
        if "background-color:" in style:
            parts = style.split("background-color:")
            if len(parts) > 1:
                color_part = parts[1].split(";")[0].strip()
                return QColor(color_part)
        
        # Default fallback
        return QColor(224, 224, 224)  # Light gray 