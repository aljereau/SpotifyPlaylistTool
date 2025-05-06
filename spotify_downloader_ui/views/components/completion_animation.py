"""
Completion animation component.

This component provides animated visual feedback when a process completes
successfully or encounters an error.
"""

import logging
from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsOpacityEffect,
    QFrame, QSizePolicy
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QPropertyAnimation, QParallelAnimationGroup,
    QSequentialAnimationGroup, QEasingCurve, QSize, QTimer, QRect, QPoint, Property
)
from PySide6.QtGui import (
    QPainter, QPainterPath, QPen, QBrush, QColor, QFont, QPaintEvent,
    QLinearGradient, QRadialGradient
)

logger = logging.getLogger(__name__)

class CheckmarkAnimation(QWidget):
    """Animated checkmark for successful completion."""
    
    def __init__(self, parent=None):
        """Initialize the checkmark animation widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Animation properties
        self._stroke_width = 3
        self._color = QColor(76, 175, 80)  # Green
        self._progress = 0.0
        self._size = 100
        
        # Set fixed size
        self.setFixedSize(self._size, self._size)
        
        # Setup animation
        self._animation = QPropertyAnimation(self, b"progress")
        self._animation.setDuration(800)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.valueChanged.connect(self.update)
        
        logger.debug("Checkmark animation initialized")
    
    def sizeHint(self) -> QSize:
        """Get the recommended size for the widget."""
        return QSize(self._size, self._size)
    
    def minimumSizeHint(self) -> QSize:
        """Get the minimum recommended size for the widget."""
        return QSize(50, 50)
    
    def set_color(self, color: QColor):
        """Set the checkmark color.
        
        Args:
            color: Color to use
        """
        self._color = color
        self.update()
    
    def get_progress(self) -> float:
        """Get the current progress.
        
        Returns:
            Progress value between 0.0 and 1.0
        """
        return self._progress
    
    def set_progress(self, value: float):
        """Set the progress value.
        
        Args:
            value: Progress value between 0.0 and 1.0
        """
        self._progress = value
        self.update()
    
    progress = Property(float, get_progress, set_progress)
    
    def start(self):
        """Start the animation."""
        self._animation.stop()
        self._progress = 0.0
        self._animation.start()
    
    def paintEvent(self, event: QPaintEvent):
        """Handle paint event.
        
        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        # Calculate center and radius
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - self._stroke_width
        
        # Draw circle background with alpha
        if self._progress < 0.5:
            # Scale circle from 0 to 1
            circle_progress = min(1.0, self._progress * 2)
            circle_radius = radius * circle_progress
            
            # Draw growing circle
            painter.setPen(Qt.PenStyle.NoPen)
            bg_color = QColor(self._color)
            bg_color.setAlphaF(0.2)
            painter.setBrush(QBrush(bg_color))
            painter.drawEllipse(QPoint(int(center_x), int(center_y)), 
                               int(circle_radius), int(circle_radius))
            
        else:
            # Circle is complete, draw with full radius
            painter.setPen(Qt.PenStyle.NoPen)
            bg_color = QColor(self._color)
            bg_color.setAlphaF(0.2)
            painter.setBrush(QBrush(bg_color))
            painter.drawEllipse(QPoint(int(center_x), int(center_y)), 
                               int(radius), int(radius))
            
            # Draw checkmark
            checkmark_progress = min(1.0, (self._progress - 0.5) * 2)
            
            # Calculate checkmark points
            # Bottom of checkmark
            point1_x = center_x - radius * 0.3
            point1_y = center_y + radius * 0.2
            
            # Middle of checkmark
            point2_x = center_x - radius * 0.1
            point2_y = center_y + radius * 0.4
            
            # Top of checkmark
            point3_x = center_x + radius * 0.4
            point3_y = center_y - radius * 0.3
            
            # Calculate actual points based on progress
            if checkmark_progress <= 0.5:
                # First line segment (normalized to 0-1 range)
                first_progress = checkmark_progress * 2
                current_x = point1_x + (point2_x - point1_x) * first_progress
                current_y = point1_y + (point2_y - point1_y) * first_progress
                
                # Draw first segment
                pen = QPen(self._color, self._stroke_width, Qt.PenStyle.SolidLine, 
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(int(point1_x), int(point1_y), int(current_x), int(current_y))
            else:
                # Draw complete first segment
                pen = QPen(self._color, self._stroke_width, Qt.PenStyle.SolidLine, 
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(int(point1_x), int(point1_y), int(point2_x), int(point2_y))
                
                # Draw second segment (normalized to 0-1 range)
                second_progress = (checkmark_progress - 0.5) * 2
                current_x = point2_x + (point3_x - point2_x) * second_progress
                current_y = point2_y + (point3_y - point2_y) * second_progress
                
                painter.drawLine(int(point2_x), int(point2_y), int(current_x), int(current_y))


class CrossAnimation(QWidget):
    """Animated cross/X for failure or error states."""
    
    def __init__(self, parent=None):
        """Initialize the cross animation widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Animation properties
        self._stroke_width = 3
        self._color = QColor(244, 67, 54)  # Red
        self._progress = 0.0
        self._size = 100
        
        # Set fixed size
        self.setFixedSize(self._size, self._size)
        
        # Setup animation
        self._animation = QPropertyAnimation(self, b"progress")
        self._animation.setDuration(800)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.valueChanged.connect(self.update)
        
        logger.debug("Cross animation initialized")
    
    def sizeHint(self) -> QSize:
        """Get the recommended size for the widget."""
        return QSize(self._size, self._size)
    
    def minimumSizeHint(self) -> QSize:
        """Get the minimum recommended size for the widget."""
        return QSize(50, 50)
    
    def set_color(self, color: QColor):
        """Set the cross color.
        
        Args:
            color: Color to use
        """
        self._color = color
        self.update()
    
    def get_progress(self) -> float:
        """Get the current progress.
        
        Returns:
            Progress value between 0.0 and 1.0
        """
        return self._progress
    
    def set_progress(self, value: float):
        """Set the progress value.
        
        Args:
            value: Progress value between 0.0 and 1.0
        """
        self._progress = value
        self.update()
    
    progress = Property(float, get_progress, set_progress)
    
    def start(self):
        """Start the animation."""
        self._animation.stop()
        self._progress = 0.0
        self._animation.start()
    
    def paintEvent(self, event: QPaintEvent):
        """Handle paint event.
        
        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        # Calculate center and radius
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - self._stroke_width
        
        # Draw circle background with alpha
        if self._progress < 0.3:
            # Scale circle from 0 to 1
            circle_progress = min(1.0, self._progress * (1.0 / 0.3))
            circle_radius = radius * circle_progress
            
            # Draw growing circle
            painter.setPen(Qt.PenStyle.NoPen)
            bg_color = QColor(self._color)
            bg_color.setAlphaF(0.2)
            painter.setBrush(QBrush(bg_color))
            painter.drawEllipse(QPoint(int(center_x), int(center_y)), 
                               int(circle_radius), int(circle_radius))
            
        else:
            # Circle is complete, draw with full radius
            painter.setPen(Qt.PenStyle.NoPen)
            bg_color = QColor(self._color)
            bg_color.setAlphaF(0.2)
            painter.setBrush(QBrush(bg_color))
            painter.drawEllipse(QPoint(int(center_x), int(center_y)), 
                               int(radius), int(radius))
            
            # Draw X
            cross_progress = min(1.0, (self._progress - 0.3) * (1.0 / 0.7))
            
            # Calculate X points
            offset = radius * 0.5
            top_left_x = center_x - offset
            top_left_y = center_y - offset
            bottom_right_x = center_x + offset
            bottom_right_y = center_y + offset
            
            top_right_x = center_x + offset
            top_right_y = center_y - offset
            bottom_left_x = center_x - offset
            bottom_left_y = center_y + offset
            
            # Setup pen
            pen = QPen(self._color, self._stroke_width, Qt.PenStyle.SolidLine, 
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            
            # Draw X based on progress
            if cross_progress <= 0.5:
                # First line - top left to bottom right
                first_progress = cross_progress * 2
                current_right_x = top_left_x + (bottom_right_x - top_left_x) * first_progress
                current_right_y = top_left_y + (bottom_right_y - top_left_y) * first_progress
                
                painter.drawLine(int(top_left_x), int(top_left_y), 
                                int(current_right_x), int(current_right_y))
            else:
                # First line - complete
                painter.drawLine(int(top_left_x), int(top_left_y), 
                                int(bottom_right_x), int(bottom_right_y))
                
                # Second line - top right to bottom left
                second_progress = (cross_progress - 0.5) * 2
                current_left_x = top_right_x + (bottom_left_x - top_right_x) * second_progress
                current_left_y = top_right_y + (bottom_left_y - top_right_y) * second_progress
                
                painter.drawLine(int(top_right_x), int(top_right_y), 
                                int(current_left_x), int(current_left_y))


class SpinnerAnimation(QWidget):
    """Animated spinner for loading/busy states."""
    
    def __init__(self, parent=None):
        """Initialize the spinner animation widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Animation properties
        self._stroke_width = 3
        self._color = QColor(33, 150, 243)  # Blue
        self._rotation = 0.0
        self._size = 100
        self._is_running = False
        
        # Set fixed size
        self.setFixedSize(self._size, self._size)
        
        # Setup timer for continuous rotation
        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60fps
        self._timer.timeout.connect(self._update_rotation)
        
        logger.debug("Spinner animation initialized")
    
    def sizeHint(self) -> QSize:
        """Get the recommended size for the widget."""
        return QSize(self._size, self._size)
    
    def minimumSizeHint(self) -> QSize:
        """Get the minimum recommended size for the widget."""
        return QSize(50, 50)
    
    def set_color(self, color: QColor):
        """Set the spinner color.
        
        Args:
            color: Color to use
        """
        self._color = color
        self.update()
    
    def _update_rotation(self):
        """Update the rotation angle."""
        self._rotation = (self._rotation + 5) % 360
        self.update()
    
    def start(self):
        """Start the animation."""
        if not self._is_running:
            self._is_running = True
            self._timer.start()
    
    def stop(self):
        """Stop the animation."""
        if self._is_running:
            self._is_running = False
            self._timer.stop()
    
    def paintEvent(self, event: QPaintEvent):
        """Handle paint event.
        
        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        # Calculate center and radius
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - self._stroke_width
        
        # Set up pen
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw spinner segments with varying opacity
        for i in range(8):
            # Calculate angle
            angle = (self._rotation + i * 45) % 360
            
            # Calculate opacity based on position
            opacity = 0.2 + ((i / 8) * 0.8)
            
            # Set color with opacity
            color = QColor(self._color)
            color.setAlphaF(opacity)
            painter.setBrush(QBrush(color))
            
            # Draw arc segment
            start_angle = angle - 20
            span = 40
            
            # Create circular segment
            path = QPainterPath()
            path.moveTo(center_x, center_y)
            
            # Convert angles to Qt's 16th of a degree units
            start_angle16 = int(start_angle * 16)
            span16 = int(span * 16)
            
            # Add arc to path
            path.arcTo(int(center_x - radius), int(center_y - radius), 
                      int(radius * 2), int(radius * 2), 
                      start_angle, span)
            path.closeSubpath()
            
            # Draw path
            painter.drawPath(path)


class CompletionAnimation(QWidget):
    """Widget for animated completion feedback."""
    
    # Signal emitted when animation completes
    animation_finished = Signal()
    
    # Animation states
    STATE_SUCCESS = 1
    STATE_ERROR = 2
    STATE_LOADING = 3
    
    def __init__(self, parent=None):
        """Initialize the completion animation widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Animation state
        self._state = self.STATE_SUCCESS
        self._message = ""
        
        self._init_ui()
        
        # Set up opacity animation for fade in/out
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)
        
        self._opacity_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._opacity_animation.setDuration(500)
        self._opacity_animation.finished.connect(self._on_animation_finished)
        
        logger.debug("Completion animation initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Animation container
        animation_frame = QFrame()
        animation_layout = QVBoxLayout(animation_frame)
        animation_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create all animations but only show the active one
        self.checkmark = CheckmarkAnimation()
        self.cross = CrossAnimation()
        self.spinner = SpinnerAnimation()
        
        # Initially hide all
        self.checkmark.hide()
        self.cross.hide()
        self.spinner.hide()
        
        animation_layout.addWidget(self.checkmark)
        animation_layout.addWidget(self.cross)
        animation_layout.addWidget(self.spinner)
        
        layout.addWidget(animation_frame)
        
        # Message label
        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        
        # Use larger font
        font = self.message_label.font()
        font.setPointSize(12)
        self.message_label.setFont(font)
        
        layout.addWidget(self.message_label)
    
    def set_message(self, message: str):
        """Set the message text.
        
        Args:
            message: Message to display
        """
        self._message = message
        self.message_label.setText(message)
    
    def show_success(self, message: str = ""):
        """Show success animation.
        
        Args:
            message: Message to display
        """
        self._state = self.STATE_SUCCESS
        if message:
            self.set_message(message)
        
        # Show checkmark, hide others
        self.checkmark.show()
        self.cross.hide()
        self.spinner.hide()
        self.spinner.stop()
        
        # Start animation
        self._start_animation()
    
    def show_error(self, message: str = ""):
        """Show error animation.
        
        Args:
            message: Message to display
        """
        self._state = self.STATE_ERROR
        if message:
            self.set_message(message)
        
        # Show cross, hide others
        self.checkmark.hide()
        self.cross.show()
        self.spinner.hide()
        self.spinner.stop()
        
        # Start animation
        self._start_animation()
    
    def show_loading(self, message: str = ""):
        """Show loading animation.
        
        Args:
            message: Message to display
        """
        self._state = self.STATE_LOADING
        if message:
            self.set_message(message)
        
        # Show spinner, hide others
        self.checkmark.hide()
        self.cross.hide()
        self.spinner.show()
        
        # Start spinner animation
        self.spinner.start()
        
        # Fade in
        self._opacity_animation.setStartValue(0.0)
        self._opacity_animation.setEndValue(1.0)
        self._opacity_animation.start()
    
    def hide_animation(self):
        """Hide the animation with fade out effect."""
        self._opacity_animation.setStartValue(1.0)
        self._opacity_animation.setEndValue(0.0)
        self._opacity_animation.start()
    
    def _start_animation(self):
        """Start the appropriate animation based on state."""
        # Fade in
        self._opacity_animation.setStartValue(0.0)
        self._opacity_animation.setEndValue(1.0)
        self._opacity_animation.start()
        
        # Start specific animation
        if self._state == self.STATE_SUCCESS:
            self.checkmark.start()
        elif self._state == self.STATE_ERROR:
            self.cross.start()
    
    def _on_animation_finished(self):
        """Handle animation finished event."""
        # Only emit signal when completely hidden
        if self._opacity_effect.opacity() < 0.1:
            self.animation_finished.emit()
            
            # Stop spinner if it was running
            if self._state == self.STATE_LOADING:
                self.spinner.stop() 