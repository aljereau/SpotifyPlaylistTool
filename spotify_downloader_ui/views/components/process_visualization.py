"""
Process visualization component.

This component provides a comprehensive visualization of processing operations
with multi-level progress indicators, time estimates, and detailed status
information.
"""

import logging
from typing import Dict, List, Optional, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox, QTextEdit, QSplitter, QFrame,
    QGridLayout, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QColor, QPixmap, QIcon

from .multi_level_progress import MultiLevelProgressIndicator, ProgressLevel, ProgressState
from .enhanced_progress_bar import EnhancedProgressBar
from .time_estimator import TimeEstimator

logger = logging.getLogger(__name__)

class ProcessStage:
    """Constants for process stages."""
    INITIALIZATION = 0
    METADATA = 1
    TRACKS = 2
    AUDIO_FEATURES = 3
    FINALIZING = 4
    
    @staticmethod
    def get_stage_name(stage: int) -> str:
        """Get the name of a stage.
        
        Args:
            stage: Stage constant
            
        Returns:
            Stage name string
        """
        stage_names = {
            ProcessStage.INITIALIZATION: "Initialization",
            ProcessStage.METADATA: "Retrieving Metadata",
            ProcessStage.TRACKS: "Processing Tracks",
            ProcessStage.AUDIO_FEATURES: "Analyzing Audio Features",
            ProcessStage.FINALIZING: "Finalizing"
        }
        return stage_names.get(stage, f"Unknown Stage ({stage})")


class ProcessVisualization(QWidget):
    """Comprehensive process visualization widget."""
    
    # Signals
    cancel_requested = Signal()
    pause_requested = Signal()
    resume_requested = Signal()
    
    def __init__(self, parent=None):
        """Initialize the process visualization widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # State
        self._is_paused = False
        self._current_stage = ProcessStage.INITIALIZATION
        
        # Time estimators - one for each level
        self._time_estimators = {
            ProgressLevel.OVERALL: TimeEstimator(),
            ProgressLevel.PLAYLIST: TimeEstimator(),
            ProgressLevel.OPERATION: TimeEstimator()
        }
        
        # Timer for periodic updates
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(1000)  # Update every second
        self._update_timer.timeout.connect(self._update_time_labels)
        
        self._init_ui()
        
        logger.info("Process visualization initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Title and status
        title_layout = QHBoxLayout()
        
        self.title_label = QLabel("Processing Playlist")
        self.title_label.setObjectName("title_label")
        title_layout.addWidget(self.title_label)
        
        # Status indicator
        status_frame = QFrame()
        status_frame.setFixedSize(16, 16)
        status_frame.setFrameShape(QFrame.Shape.NoFrame)
        status_frame.setStyleSheet("background-color: #2a82da; border-radius: 8px;")
        title_layout.addWidget(status_frame)
        self.status_indicator = status_frame
        
        main_layout.addLayout(title_layout)
        
        # Current status label
        self.status_label = QLabel("Starting process...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Stage indicator (steps)
        stages_frame = QFrame()
        stages_layout = QHBoxLayout(stages_frame)
        stages_layout.setContentsMargins(0, 5, 0, 5)
        stages_layout.setSpacing(5)
        
        self.stage_indicators = []
        for i in range(5):  # 5 stages
            # Create stage indicator
            stage_frame = QFrame()
            stage_layout = QVBoxLayout(stage_frame)
            stage_layout.setContentsMargins(0, 0, 0, 0)
            stage_layout.setSpacing(5)
            
            # Circle indicator
            circle = QFrame()
            circle.setFixedSize(24, 24)
            circle.setFrameShape(QFrame.Shape.Box)
            circle.setFrameShadow(QFrame.Shadow.Plain)
            circle.setStyleSheet("background-color: #e0e0e0; border-radius: 12px; border: none;")
            
            # Label
            stage_name = ProcessStage.get_stage_name(i)
            label = QLabel(stage_name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            stage_layout.addWidget(circle, 0, Qt.AlignmentFlag.AlignCenter)
            stage_layout.addWidget(label, 0, Qt.AlignmentFlag.AlignCenter)
            
            stages_layout.addWidget(stage_frame)
            self.stage_indicators.append((circle, label))
            
            # Add connector between stages (except after last stage)
            if i < 4:
                connector = QFrame()
                connector.setFrameShape(QFrame.Shape.HLine)
                connector.setFrameShadow(QFrame.Shadow.Plain)
                connector.setFixedHeight(2)
                connector.setStyleSheet("background-color: #e0e0e0;")
                stages_layout.addWidget(connector)
        
        main_layout.addWidget(stages_frame)
        
        # Multi-level progress indicator
        self.progress_indicator = MultiLevelProgressIndicator()
        main_layout.addWidget(self.progress_indicator)
        
        # Details group
        details_group = QGroupBox("Processing Details")
        details_layout = QVBoxLayout(details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMinimumHeight(100)
        details_layout.addWidget(self.details_text)
        
        main_layout.addWidget(details_group, 1)  # Give stretch priority
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_requested)
        controls_layout.addWidget(self.cancel_button)
        
        controls_layout.addStretch()
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self._on_pause_clicked)
        controls_layout.addWidget(self.pause_button)
        
        main_layout.addLayout(controls_layout)
        
        # Start update timer
        self._update_timer.start()
    
    def _update_time_labels(self):
        """Update time labels with latest estimates."""
        for level, estimator in self._time_estimators.items():
            # Skip levels with no progress data yet
            if not estimator.progress_history:
                continue
                
            # Get latest estimate
            newest = estimator.progress_history[-1]
            estimate = estimator.update(newest['current'], newest['total'])
            
            # Update time in progress indicator
            self.progress_indicator.set_time_estimate(level, estimate['remaining_seconds'])
    
    @Slot()
    def _on_pause_clicked(self):
        """Handle pause/resume button click."""
        self._is_paused = not self._is_paused
        
        if self._is_paused:
            self.pause_button.setText("Resume")
            self.status_indicator.setStyleSheet("background-color: #ffa500; border-radius: 8px;")
            self.pause_requested.emit()
        else:
            self.pause_button.setText("Pause")
            self.status_indicator.setStyleSheet("background-color: #2a82da; border-radius: 8px;")
            self.resume_requested.emit()
    
    def set_title(self, title: str):
        """Set the process title.
        
        Args:
            title: Title text
        """
        self.title_label.setText(title)
    
    def set_status(self, status: str):
        """Set the status text.
        
        Args:
            status: Status text
        """
        self.status_label.setText(status)
    
    def set_stage(self, stage: int):
        """Set the current processing stage.
        
        Args:
            stage: Stage constant
        """
        if not 0 <= stage < len(self.stage_indicators):
            logger.warning(f"Invalid stage: {stage}")
            return
            
        self._current_stage = stage
        
        # Update status with stage name
        self.set_status(f"Current stage: {ProcessStage.get_stage_name(stage)}")
        
        # Update stage indicators
        for i, (circle, label) in enumerate(self.stage_indicators):
            if i < stage:
                # Completed stage
                circle.setStyleSheet("background-color: #4caf50; border-radius: 12px; border: none;")
            elif i == stage:
                # Current stage
                circle.setStyleSheet("background-color: #2a82da; border-radius: 12px; border: none;")
            else:
                # Future stage
                circle.setStyleSheet("background-color: #e0e0e0; border-radius: 12px; border: none;")
    
    def update_progress(self, level: int, current: int, total: int, message: str = ""):
        """Update progress for a specific level.
        
        Args:
            level: Progress level constant
            current: Current progress value
            total: Total items to process
            message: Optional message to display
        """
        # Update progress indicator
        self.progress_indicator.update_progress(
            level, 
            current, 
            total,
            ProgressState.PAUSED if self._is_paused else ProgressState.RUNNING,
            message
        )
        
        # Update time estimator
        estimator = self._time_estimators.get(level)
        if estimator:
            estimator.update(current, total)
    
    def set_phase(self, level: int, phase: int):
        """Set the active phase for a progress level.
        
        Args:
            level: Progress level constant
            phase: Phase index (0-based)
        """
        self.progress_indicator.set_phase_active(level, phase, True)
    
    def add_detail(self, detail: str):
        """Add a detail to the processing log.
        
        Args:
            detail: Detail text to add
        """
        # Add timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Append to text edit
        self.details_text.append(f"[{timestamp}] {detail}")
    
    def set_processing_complete(self, success: bool = True, error_message: str = ""):
        """Set the processing as complete.
        
        Args:
            success: Whether processing was successful
            error_message: Error message if not successful
        """
        # Update status indicator
        if success:
            self.status_indicator.setStyleSheet("background-color: #4caf50; border-radius: 8px;")
            self.progress_indicator.update_progress(
                ProgressLevel.OVERALL, 100, 100, ProgressState.COMPLETED
            )
            self.set_status("Processing completed successfully")
        else:
            self.status_indicator.setStyleSheet("background-color: #f44336; border-radius: 8px;")
            self.progress_indicator.update_progress(
                ProgressLevel.OVERALL, 0, 100, ProgressState.ERROR, error_message
            )
            self.set_status(f"Error: {error_message}")
        
        # Update buttons
        self.pause_button.setEnabled(False)
        self.cancel_button.setText("Close")
        
        # Stop timer
        self._update_timer.stop()
    
    def reset(self):
        """Reset the visualization to initial state."""
        # Reset progress indicators
        self.progress_indicator.reset()
        
        # Reset time estimators
        for estimator in self._time_estimators.values():
            estimator.reset()
        
        # Reset stage indicators
        for i, (circle, label) in enumerate(self.stage_indicators):
            circle.setStyleSheet("background-color: #e0e0e0; border-radius: 12px; border: none;")
        
        # Reset status
        self.set_status("Starting process...")
        self.status_indicator.setStyleSheet("background-color: #2a82da; border-radius: 8px;")
        
        # Reset buttons
        self.pause_button.setText("Pause")
        self.pause_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
        
        # Reset details
        self.details_text.clear()
        
        # Reset state
        self._is_paused = False
        self._current_stage = ProcessStage.INITIALIZATION
        
        # Start timer
        self._update_timer.start() 