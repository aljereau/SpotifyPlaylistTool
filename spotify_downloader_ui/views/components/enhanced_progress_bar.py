"""
Enhanced progress bar component with animations and customizable appearance.

This component extends the base Qt progress bar with:
- Smooth animations between progress values
- Customizable styling (colors, gradients, etc.)
- Ability to show additional information (text overlays, etc.)
- Pulsing/indeterminate mode with animated effects
"""

import logging
from typing import Dict, List, Optional, Union, Tuple
from PySide6.QtWidgets import (
    QProgressBar, QWidget, QHBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import (
    Qt, Signal, Slot, Property, QPropertyAnimation, 
    QEasingCurve, QSize, QTimer
)
from PySide6.QtGui import (
    QPainter, QLinearGradient, QBrush, QPen, QColor, QFont,
    QPalette, QFontMetrics
)

logger = logging.getLogger(__name__)

class EnhancedProgressBar(QWidget):
    """Enhanced progress bar with animations and customizable appearance."""
    
    # Signal when progress changes
    progress_changed = Signal(int)
    
    def __init__(self, parent=None):
        """Initialize the enhanced progress bar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Progress properties
        self._min_value = 0
        self._max_value = 100
        self._value = 0
        self._animated_value = 0
        self._indeterminate = False
        
        # Animation properties
        self._animation = QPropertyAnimation(self, b"animated_value")
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.setDuration(500)  # 500ms duration
        
        # Indeterminate animation
        self._indeterminate_position = 0
        self._indeterminate_timer = QTimer(self)
        self._indeterminate_timer.setInterval(16)  # ~60fps
        self._indeterminate_timer.timeout.connect(self._update_indeterminate)
        
        # Appearance properties
        self._background_color = QColor(240, 240, 240)
        self._border_color = QColor(210, 210, 210)
        self._progress_color = QColor(42, 130, 218)
        self._text_color = QColor(0, 0, 0)
        self._use_gradient = True
        self._gradient_color1 = QColor(42, 130, 218)
        self._gradient_color2 = QColor(32, 100, 200)
        self._text_visible = True
        self._text_format = "%p%"
        self._height = 24
        self._border_radius = 4
        self._custom_text = ""
        
        # Layout 
        self._init_ui()
        
        # Set size policy
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        
        logger.debug("Enhanced progress bar initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Set minimum height
        self.setMinimumHeight(self._height)
    
    def sizeHint(self) -> QSize:
        """Get the recommended size for the widget."""
        return QSize(200, self._height)
    
    def minimumSizeHint(self) -> QSize:
        """Get the minimum recommended size for the widget."""
        return QSize(100, self._height)
    
    @Property(int)
    def animated_value(self) -> int:
        """Get the animated value property.
        
        Returns:
            The current animated value
        """
        return self._animated_value
    
    @animated_value.setter
    def animated_value(self, value: int):
        """Set the animated value with property animation.
        
        Args:
            value: The new value
        """
        self._animated_value = value
        self.update()  # Trigger repaint
    
    def setValue(self, value: int):
        """Set the progress value.
        
        Args:
            value: New progress value
        """
        if value == self._value:
            return
            
        # Clamp value to range
        value = max(self._min_value, min(self._max_value, value))
        
        # Store new value
        old_value = self._value
        self._value = value
        
        # Emit signal
        self.progress_changed.emit(value)
        
        # Animate to new value
        self._animation.stop()
        self._animation.setStartValue(self._animated_value)
        self._animation.setEndValue(value)
        self._animation.start()
    
    def value(self) -> int:
        """Get the current progress value.
        
        Returns:
            Current progress value
        """
        return self._value
    
    def setRange(self, min_value: int, max_value: int):
        """Set the progress range.
        
        Args:
            min_value: Minimum value
            max_value: Maximum value
        """
        if min_value > max_value:
            min_value, max_value = max_value, min_value
            
        self._min_value = min_value
        self._max_value = max_value
        
        # Clamp current value to new range
        if self._value < min_value:
            self.setValue(min_value)
        elif self._value > max_value:
            self.setValue(max_value)
    
    def minimum(self) -> int:
        """Get the minimum value.
        
        Returns:
            Minimum value
        """
        return self._min_value
    
    def maximum(self) -> int:
        """Get the maximum value.
        
        Returns:
            Maximum value
        """
        return self._max_value
    
    def setMinimum(self, value: int):
        """Set the minimum value.
        
        Args:
            value: New minimum value
        """
        self.setRange(value, self._max_value)
    
    def setMaximum(self, value: int):
        """Set the maximum value.
        
        Args:
            value: New maximum value
        """
        self.setRange(self._min_value, value)
    
    def setIndeterminate(self, indeterminate: bool):
        """Set indeterminate/pulsing state.
        
        Args:
            indeterminate: Whether to show an indeterminate progress indicator
        """
        if indeterminate == self._indeterminate:
            return
            
        self._indeterminate = indeterminate
        
        if indeterminate:
            # Start animation timer
            self._indeterminate_timer.start()
            self._animation.stop()
        else:
            # Stop animation timer
            self._indeterminate_timer.stop()
            # Reset to actual value
            self._animated_value = self._value
        
        self.update()
    
    def isIndeterminate(self) -> bool:
        """Check if the progress bar is in indeterminate mode.
        
        Returns:
            True if indeterminate, False otherwise
        """
        return self._indeterminate
    
    def _update_indeterminate(self):
        """Update the indeterminate animation state."""
        self._indeterminate_position = (self._indeterminate_position + 2) % 300
        self.update()
    
    def setTextVisible(self, visible: bool):
        """Set whether text is visible on the progress bar.
        
        Args:
            visible: Whether text should be visible
        """
        if visible == self._text_visible:
            return
            
        self._text_visible = visible
        self.update()
    
    def isTextVisible(self) -> bool:
        """Check if text is visible.
        
        Returns:
            True if text is visible, False otherwise
        """
        return self._text_visible
    
    def setFormat(self, format_str: str):
        """Set the text format string.
        
        Args:
            format_str: Format string (%p for percentage, %v for value, %m for maximum)
        """
        if format_str == self._text_format:
            return
            
        self._text_format = format_str
        self.update()
    
    def format(self) -> str:
        """Get the text format string.
        
        Returns:
            Current format string
        """
        return self._text_format
    
    def setCustomText(self, text: str):
        """Set custom text to display (overrides format).
        
        Args:
            text: Custom text to display
        """
        if text == self._custom_text:
            return
            
        self._custom_text = text
        self.update()
    
    def customText(self) -> str:
        """Get the custom text.
        
        Returns:
            Current custom text
        """
        return self._custom_text
    
    def setProgressColor(self, color: Union[QColor, str, Tuple[int, int, int]]):
        """Set the progress bar color.
        
        Args:
            color: Color to use (QColor, string color name, or RGB tuple)
        """
        if isinstance(color, str):
            color = QColor(color)
        elif isinstance(color, tuple):
            color = QColor(*color)
            
        self._progress_color = color
        
        # Update gradient colors
        if self._use_gradient:
            h, s, v, a = color.getHsv()
            self._gradient_color1 = QColor.fromHsv(h, s, v, a)
            self._gradient_color2 = QColor.fromHsv(h, min(s + 20, 255), max(v - 30, 0), a)
        
        self.update()
    
    def setGradient(self, use_gradient: bool, color1: Optional[QColor] = None, color2: Optional[QColor] = None):
        """Set gradient for progress bar.
        
        Args:
            use_gradient: Whether to use gradient fill
            color1: First gradient color (optional)
            color2: Second gradient color (optional)
        """
        self._use_gradient = use_gradient
        
        if color1 is not None:
            self._gradient_color1 = color1
            
        if color2 is not None:
            self._gradient_color2 = color2
            
        self.update()
    
    def setBorderRadius(self, radius: int):
        """Set the border radius.
        
        Args:
            radius: Border radius in pixels
        """
        self._border_radius = radius
        self.update()
    
    def paintEvent(self, event):
        """Handle paint event.
        
        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        # Draw background
        painter.setPen(QPen(self._border_color))
        painter.setBrush(QBrush(self._background_color))
        painter.drawRoundedRect(0, 0, width - 1, height - 1, 
                               self._border_radius, self._border_radius)
        
        # Calculate progress width
        if self._indeterminate:
            # Draw pulsing/moving progress
            gradient = QLinearGradient(0, 0, width, 0)
            gradient.setColorAt(0, QColor(240, 240, 240))
            gradient.setColorAt(0.4, self._progress_color)
            gradient.setColorAt(0.6, self._progress_color)
            gradient.setColorAt(1, QColor(240, 240, 240))
            
            # Shift gradient based on animation position
            shift = self._indeterminate_position / 100.0 - 1
            gradient.setStart(width * shift, 0)
            gradient.setFinalStop(width * (shift + 1), 0)
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(1, 1, width - 2, height - 2, 
                                  self._border_radius - 1, self._border_radius - 1)
        else:
            # Draw regular progress
            range_size = self._max_value - self._min_value
            if range_size > 0:
                progress_width = int(((self._animated_value - self._min_value) / range_size) * (width - 2))
                
                # Ensure we have at least 1px width when not at minimum
                if self._animated_value > self._min_value and progress_width < 1:
                    progress_width = 1
                    
                if progress_width > 0:
                    if self._use_gradient:
                        # Create gradient
                        gradient = QLinearGradient(0, 0, 0, height)
                        gradient.setColorAt(0, self._gradient_color1)
                        gradient.setColorAt(1, self._gradient_color2)
                        painter.setBrush(QBrush(gradient))
                    else:
                        painter.setBrush(QBrush(self._progress_color))
                    
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRoundedRect(1, 1, progress_width, height - 2, 
                                         self._border_radius - 1, self._border_radius - 1)
        
        # Draw text if enabled
        if self._text_visible:
            text = self._custom_text
            if not text:
                # Format text based on format string
                percentage = 0
                if self._max_value > self._min_value:
                    percentage = int(((self._value - self._min_value) / 
                                    (self._max_value - self._min_value)) * 100)
                
                text = self._text_format
                text = text.replace("%p", str(percentage))
                text = text.replace("%v", str(self._value))
                text = text.replace("%m", str(self._max_value))
            
            painter.setPen(self._text_color)
            painter.setFont(self.font())
            
            # Center text
            metrics = QFontMetrics(self.font())
            text_width = metrics.horizontalAdvance(text)
            text_height = metrics.height()
            
            text_x = (width - text_width) // 2
            text_y = (height + text_height) // 2 - metrics.descent()
            
            painter.drawText(text_x, text_y, text) 