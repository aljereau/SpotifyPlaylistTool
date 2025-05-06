"""
Operation Control component for managing playlist processing operations.
"""

import logging
from typing import List, Dict, Optional, Callable
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QToolBar, QSlider, QFrame, QSizePolicy, QComboBox,
    QCheckBox, QGroupBox, QGridLayout, QToolButton
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QAction, QAction, QAction

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService

logger = logging.getLogger(__name__)

class OperationStatus(Enum):
    """Operation status states."""
    IDLE = 0
    RUNNING = 1
    PAUSED = 2
    CANCELLING = 3
    COMPLETED = 4
    FAILED = 5

class ThrottleLevel(Enum):
    """Throttling levels for operations."""
    NONE = 0        # No throttling, max speed
    LOW = 1         # Light throttling
    MEDIUM = 2      # Moderate throttling
    HIGH = 3        # Heavy throttling
    CUSTOM = 4      # Custom throttling value

class OperationControl(QWidget):
    """Widget for controlling operations with advanced features."""
    
    # Signals
    operation_start = Signal()
    operation_pause = Signal()
    operation_resume = Signal()
    operation_cancel = Signal()
    operation_retry = Signal()
    operation_skip = Signal()
    throttle_changed = Signal(int)  # Throttle percentage (0-100)
    parameter_adjusted = Signal(str, object)  # parameter name, new value
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the operation control.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        super().__init__()
        
        self.config_service = config_service
        self.error_service = error_service
        
        # State tracking
        self.operation_status = OperationStatus.IDLE
        self.can_retry = False
        self.can_skip = False
        self.operation_params = {}
        self.throttle_level = ThrottleLevel.NONE
        self.custom_throttle_percent = 0
        
        # Shutdown handling
        self.shutdown_pending = False
        self.shutdown_timer = None
        
        self._init_ui()
        
        logger.info("Operation control initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create primary control buttons
        control_layout = QHBoxLayout()
        
        # Start/Resume button
        self.start_button = QPushButton("Start")
        self.start_button.setMinimumWidth(80)
        self.start_button.clicked.connect(self._on_start_clicked)
        control_layout.addWidget(self.start_button)
        
        # Pause button
        self.pause_button = QPushButton("Pause")
        self.pause_button.setMinimumWidth(80)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.pause_button.setEnabled(False)
        control_layout.addWidget(self.pause_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(80)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.cancel_button.setEnabled(False)
        control_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(control_layout)
        
        # Secondary controls
        secondary_layout = QHBoxLayout()
        
        # Retry button
        self.retry_button = QPushButton("Retry")
        self.retry_button.setMinimumWidth(80)
        self.retry_button.clicked.connect(self._on_retry_clicked)
        self.retry_button.setEnabled(False)
        secondary_layout.addWidget(self.retry_button)
        
        # Skip button
        self.skip_button = QPushButton("Skip")
        self.skip_button.setMinimumWidth(80)
        self.skip_button.clicked.connect(self._on_skip_clicked)
        self.skip_button.setEnabled(False)
        secondary_layout.addWidget(self.skip_button)
        
        secondary_layout.addStretch()
        
        # Status indicator
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Idle")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        secondary_layout.addLayout(status_layout)
        
        main_layout.addLayout(secondary_layout)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        
        # Throttling controls
        throttle_group = QGroupBox("Throttling")
        throttle_layout = QVBoxLayout(throttle_group)
        
        # Throttle level selection
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Level:"))
        
        self.throttle_combo = QComboBox()
        self.throttle_combo.addItem("None", ThrottleLevel.NONE.value)
        self.throttle_combo.addItem("Low", ThrottleLevel.LOW.value)
        self.throttle_combo.addItem("Medium", ThrottleLevel.MEDIUM.value)
        self.throttle_combo.addItem("High", ThrottleLevel.HIGH.value)
        self.throttle_combo.addItem("Custom", ThrottleLevel.CUSTOM.value)
        self.throttle_combo.currentIndexChanged.connect(self._on_throttle_level_changed)
        level_layout.addWidget(self.throttle_combo)
        
        throttle_layout.addLayout(level_layout)
        
        # Custom throttle slider
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Rate:"))
        
        self.throttle_slider = QSlider(Qt.Orientation.Horizontal)
        self.throttle_slider.setMinimum(0)
        self.throttle_slider.setMaximum(100)
        self.throttle_slider.setValue(0)
        self.throttle_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.throttle_slider.setTickInterval(10)
        self.throttle_slider.valueChanged.connect(self._on_throttle_value_changed)
        self.throttle_slider.setEnabled(False)
        slider_layout.addWidget(self.throttle_slider)
        
        self.throttle_value_label = QLabel("0%")
        slider_layout.addWidget(self.throttle_value_label)
        
        throttle_layout.addLayout(slider_layout)
        
        # Reason for throttling
        self.throttle_reason = QLabel("")
        self.throttle_reason.setWordWrap(True)
        throttle_layout.addWidget(self.throttle_reason)
        
        main_layout.addWidget(throttle_group)
        
        # Operation parameters
        params_group = QGroupBox("Operation Parameters")
        params_layout = QGridLayout(params_group)
        
        # Retry options
        self.retry_checkbox = QCheckBox("Auto-retry on failure")
        self.retry_checkbox.stateChanged.connect(self._on_auto_retry_changed)
        params_layout.addWidget(self.retry_checkbox, 0, 0)
        
        self.retry_count_label = QLabel("Max retries:")
        params_layout.addWidget(self.retry_count_label, 0, 1)
        
        self.retry_count_combo = QComboBox()
        for i in range(1, 6):
            self.retry_count_combo.addItem(str(i), i)
        self.retry_count_combo.setCurrentIndex(2)  # Default to 3
        self.retry_count_combo.currentIndexChanged.connect(self._on_retry_count_changed)
        self.retry_count_combo.setEnabled(False)
        params_layout.addWidget(self.retry_count_combo, 0, 2)
        
        # Graceful shutdown
        self.graceful_shutdown_checkbox = QCheckBox("Enable graceful shutdown")
        self.graceful_shutdown_checkbox.setChecked(True)
        self.graceful_shutdown_checkbox.stateChanged.connect(self._on_graceful_shutdown_changed)
        params_layout.addWidget(self.graceful_shutdown_checkbox, 1, 0)
        
        self.save_state_checkbox = QCheckBox("Save state on exit")
        self.save_state_checkbox.setChecked(True)
        self.save_state_checkbox.stateChanged.connect(self._on_save_state_changed)
        params_layout.addWidget(self.save_state_checkbox, 1, 1, 1, 2)
        
        # Rate limiting avoidance
        self.avoid_rate_limits_checkbox = QCheckBox("Avoid rate limits")
        self.avoid_rate_limits_checkbox.setChecked(True)
        self.avoid_rate_limits_checkbox.stateChanged.connect(self._on_avoid_rate_limits_changed)
        params_layout.addWidget(self.avoid_rate_limits_checkbox, 2, 0, 1, 3)
        
        main_layout.addWidget(params_group)
        
        # Shutdown warning (hidden by default)
        self.shutdown_frame = QFrame()
        self.shutdown_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.shutdown_frame.setStyleSheet("background-color: #ffeeee;")
        shutdown_layout = QHBoxLayout(self.shutdown_frame)
        
        self.shutdown_label = QLabel("Graceful shutdown in progress...")
        shutdown_layout.addWidget(self.shutdown_label)
        
        self.abort_shutdown_button = QPushButton("Abort")
        self.abort_shutdown_button.clicked.connect(self._on_abort_shutdown)
        shutdown_layout.addWidget(self.abort_shutdown_button)
        
        self.shutdown_frame.setVisible(False)
        main_layout.addWidget(self.shutdown_frame)
        
        # Add vertical spacer at the bottom
        main_layout.addStretch(1)
        
        # Initialize state
        self._update_controls()
    
    def set_operation_status(self, status: OperationStatus) -> None:
        """Set the current operation status.
        
        Args:
            status: New operation status
        """
        old_status = self.operation_status
        self.operation_status = status
        
        # Update status label
        self.status_label.setText(status.name.capitalize())
        
        # Update controls based on new status
        self._update_controls()
        
        # Log status change
        logger.info(f"Operation status changed: {old_status.name} -> {status.name}")
    
    def set_can_retry(self, can_retry: bool) -> None:
        """Set whether the current operation can be retried.
        
        Args:
            can_retry: Whether retry is available
        """
        self.can_retry = can_retry
        self.retry_button.setEnabled(can_retry)
    
    def set_can_skip(self, can_skip: bool) -> None:
        """Set whether the current operation can be skipped.
        
        Args:
            can_skip: Whether skip is available
        """
        self.can_skip = can_skip
        self.skip_button.setEnabled(can_skip)
    
    def set_throttling_reason(self, reason: str) -> None:
        """Set the reason for throttling.
        
        Args:
            reason: Reason text
        """
        self.throttle_reason.setText(reason)
    
    def start_graceful_shutdown(self, timeout_seconds: int = 30) -> None:
        """Begin graceful shutdown process.
        
        Args:
            timeout_seconds: Seconds before forced shutdown
        """
        if not self.graceful_shutdown_checkbox.isChecked():
            # Graceful shutdown not enabled, just emit cancel
            self.operation_cancel.emit()
            return
            
        # Start shutdown sequence
        self.shutdown_pending = True
        self.shutdown_frame.setVisible(True)
        
        # Update label
        self.shutdown_label.setText(f"Graceful shutdown in progress ({timeout_seconds}s remaining)...")
        
        # Set up timer
        if self.shutdown_timer:
            self.shutdown_timer.stop()
        
        self.shutdown_timer = QTimer(self)
        self.shutdown_timer.timeout.connect(self._update_shutdown_timer)
        self.shutdown_timer.start(1000)  # 1 second intervals
        
        # Store countdown
        self.shutdown_countdown = timeout_seconds
        
        # Log shutdown initiated
        logger.info(f"Graceful shutdown initiated with {timeout_seconds}s timeout")
    
    def _update_controls(self) -> None:
        """Update controls based on current status."""
        # Set button states based on operation status
        if self.operation_status == OperationStatus.IDLE:
            self.start_button.setText("Start")
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            
        elif self.operation_status == OperationStatus.RUNNING:
            self.start_button.setText("Resume")
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            
        elif self.operation_status == OperationStatus.PAUSED:
            self.start_button.setText("Resume")
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            
        elif self.operation_status == OperationStatus.CANCELLING:
            self.start_button.setText("Start")
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            
        elif self.operation_status == OperationStatus.COMPLETED:
            self.start_button.setText("Start")
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            
        elif self.operation_status == OperationStatus.FAILED:
            self.start_button.setText("Start")
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            
        # Retry and skip buttons updated separately via set_can_retry/set_can_skip
        
        # Throttling controls
        throttle_enabled = self.operation_status in (
            OperationStatus.RUNNING,
            OperationStatus.PAUSED
        )
        
        self.throttle_combo.setEnabled(throttle_enabled)
        self.throttle_slider.setEnabled(
            throttle_enabled and 
            self.throttle_combo.currentData() == ThrottleLevel.CUSTOM.value
        )
    
    def _update_shutdown_timer(self) -> None:
        """Update the shutdown countdown timer."""
        self.shutdown_countdown -= 1
        
        # Update label
        self.shutdown_label.setText(
            f"Graceful shutdown in progress ({self.shutdown_countdown}s remaining)..."
        )
        
        # Check if timer expired
        if self.shutdown_countdown <= 0:
            # Stop timer
            self.shutdown_timer.stop()
            self.shutdown_timer = None
            
            # Force cancel
            logger.warning("Graceful shutdown timeout expired, forcing cancel")
            self.operation_cancel.emit()
            
            # Hide shutdown frame
            self.shutdown_frame.setVisible(False)
            self.shutdown_pending = False
    
    def _apply_throttle_level(self, level: ThrottleLevel) -> None:
        """Apply the selected throttle level.
        
        Args:
            level: Throttle level to apply
        """
        throttle_percent = 0
        
        if level == ThrottleLevel.NONE:
            throttle_percent = 0
        elif level == ThrottleLevel.LOW:
            throttle_percent = 25
        elif level == ThrottleLevel.MEDIUM:
            throttle_percent = 50
        elif level == ThrottleLevel.HIGH:
            throttle_percent = 75
        elif level == ThrottleLevel.CUSTOM:
            throttle_percent = self.custom_throttle_percent
        
        # Set slider value (without triggering signal)
        self.throttle_slider.blockSignals(True)
        self.throttle_slider.setValue(throttle_percent)
        self.throttle_slider.blockSignals(False)
        
        # Update label
        self.throttle_value_label.setText(f"{throttle_percent}%")
        
        # Emit signal for controller
        self.throttle_changed.emit(throttle_percent)
    
    @Slot()
    def _on_start_clicked(self) -> None:
        """Handle start button click."""
        if self.operation_status == OperationStatus.IDLE or self.operation_status == OperationStatus.COMPLETED or self.operation_status == OperationStatus.FAILED:
            self.operation_start.emit()
            self.set_operation_status(OperationStatus.RUNNING)
        elif self.operation_status == OperationStatus.PAUSED:
            self.operation_resume.emit()
            self.set_operation_status(OperationStatus.RUNNING)
    
    @Slot()
    def _on_pause_clicked(self) -> None:
        """Handle pause button click."""
        if self.operation_status == OperationStatus.RUNNING:
            self.operation_pause.emit()
            self.set_operation_status(OperationStatus.PAUSED)
    
    @Slot()
    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        if self.operation_status in (OperationStatus.RUNNING, OperationStatus.PAUSED):
            self.operation_cancel.emit()
            self.set_operation_status(OperationStatus.CANCELLING)
    
    @Slot()
    def _on_retry_clicked(self) -> None:
        """Handle retry button click."""
        if self.can_retry:
            self.operation_retry.emit()
    
    @Slot()
    def _on_skip_clicked(self) -> None:
        """Handle skip button click."""
        if self.can_skip:
            self.operation_skip.emit()
    
    @Slot(int)
    def _on_throttle_level_changed(self, index: int) -> None:
        """Handle throttle level combo box change.
        
        Args:
            index: Selected index
        """
        level_value = self.throttle_combo.currentData()
        level = ThrottleLevel(level_value)
        
        # Update UI
        self.throttle_level = level
        self.throttle_slider.setEnabled(level == ThrottleLevel.CUSTOM)
        
        # Apply throttling
        self._apply_throttle_level(level)
    
    @Slot(int)
    def _on_throttle_value_changed(self, value: int) -> None:
        """Handle throttle slider value change.
        
        Args:
            value: New slider value
        """
        if self.throttle_level == ThrottleLevel.CUSTOM:
            self.custom_throttle_percent = value
            
            # Update label
            self.throttle_value_label.setText(f"{value}%")
            
            # Emit signal
            self.throttle_changed.emit(value)
    
    @Slot(int)
    def _on_auto_retry_changed(self, state: int) -> None:
        """Handle auto-retry checkbox change.
        
        Args:
            state: Checkbox state
        """
        enabled = (state == Qt.CheckState.Checked.value)
        
        # Update UI
        self.retry_count_combo.setEnabled(enabled)
        
        # Emit parameter change signal
        self.parameter_adjusted.emit(
            "auto_retry",
            enabled
        )
    
    @Slot(int)
    def _on_retry_count_changed(self, index: int) -> None:
        """Handle retry count combo box change.
        
        Args:
            index: Selected index
        """
        value = self.retry_count_combo.currentData()
        
        # Emit parameter change signal
        self.parameter_adjusted.emit(
            "max_retries",
            value
        )
    
    @Slot(int)
    def _on_graceful_shutdown_changed(self, state: int) -> None:
        """Handle graceful shutdown checkbox change.
        
        Args:
            state: Checkbox state
        """
        enabled = (state == Qt.CheckState.Checked.value)
        
        # Emit parameter change signal
        self.parameter_adjusted.emit(
            "graceful_shutdown",
            enabled
        )
    
    @Slot(int)
    def _on_save_state_changed(self, state: int) -> None:
        """Handle save state checkbox change.
        
        Args:
            state: Checkbox state
        """
        enabled = (state == Qt.CheckState.Checked.value)
        
        # Emit parameter change signal
        self.parameter_adjusted.emit(
            "save_state",
            enabled
        )
    
    @Slot(int)
    def _on_avoid_rate_limits_changed(self, state: int) -> None:
        """Handle avoid rate limits checkbox change.
        
        Args:
            state: Checkbox state
        """
        enabled = (state == Qt.CheckState.Checked.value)
        
        # Emit parameter change signal
        self.parameter_adjusted.emit(
            "avoid_rate_limits",
            enabled
        )
    
    @Slot()
    def _on_abort_shutdown(self) -> None:
        """Handle abort shutdown button click."""
        if self.shutdown_timer:
            self.shutdown_timer.stop()
            self.shutdown_timer = None
        
        # Hide shutdown frame
        self.shutdown_frame.setVisible(False)
        self.shutdown_pending = False
        
        # Log shutdown aborted
        logger.info("Graceful shutdown aborted") 