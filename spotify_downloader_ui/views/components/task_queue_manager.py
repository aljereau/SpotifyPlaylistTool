"""
Task Queue Manager component for managing playlist processing tasks.
"""

import logging
from typing import List, Dict, Optional, Callable
from enum import Enum
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QMenu, QFrame, QSplitter,
    QScrollArea, QSizePolicy, QToolBar, QToolButton, QComboBox
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QDrag, QPixmap, QPainter, QColor, QAction, QAction, QAction

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2

class TaskStatus(Enum):
    """Task status states."""
    PENDING = 0
    IN_PROGRESS = 1
    PAUSED = 2
    COMPLETED = 3
    FAILED = 4
    CANCELLED = 5

class TaskItem:
    """Represents a task in the queue."""
    
    def __init__(self, 
                 task_id: str, 
                 playlist_id: str, 
                 playlist_name: str,
                 description: str = "",
                 priority: TaskPriority = TaskPriority.MEDIUM,
                 dependencies: List[str] = None):
        """Initialize a task item.
        
        Args:
            task_id: Unique identifier for the task
            playlist_id: Spotify playlist ID
            playlist_name: Name of the playlist
            description: Task description
            priority: Task priority level
            dependencies: List of task IDs this task depends on
        """
        self.task_id = task_id
        self.playlist_id = playlist_id
        self.playlist_name = playlist_name
        self.description = description
        self.priority = priority
        self.dependencies = dependencies or []
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.error_message = ""
        self.result_data = {}
        self.metadata = {}
    
    @property
    def display_name(self) -> str:
        """Get display name for the task.
        
        Returns:
            Formatted display name
        """
        return f"{self.playlist_name} ({self.task_id})"
    
    def can_start(self, completed_tasks: List[str]) -> bool:
        """Check if task can start based on dependencies.
        
        Args:
            completed_tasks: List of completed task IDs
            
        Returns:
            True if all dependencies are met
        """
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def update_progress(self, progress: int):
        """Update the task progress.
        
        Args:
            progress: Progress value (0-100)
        """
        self.progress = max(0, min(100, progress))
        
        # Update status based on progress
        if self.progress == 100:
            self.status = TaskStatus.COMPLETED
        elif self.status == TaskStatus.PENDING and self.progress > 0:
            self.status = TaskStatus.IN_PROGRESS

class TaskQueueManager(QWidget):
    """Widget for managing task queue visualization and operations."""
    
    # Signals
    task_selected = Signal(str)  # task_id
    task_double_clicked = Signal(str)  # task_id
    task_priority_changed = Signal(str, TaskPriority)  # task_id, priority
    task_cancelled = Signal(str)  # task_id
    task_restarted = Signal(str)  # task_id
    queue_reordered = Signal(list)  # new_order of task_ids
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the task queue manager.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        super().__init__()
        
        self.config_service = config_service
        self.error_service = error_service
        
        self.tasks = {}  # Dict[task_id, TaskItem]
        self.completed_tasks = []
        self.current_task_id = None
        
        self._init_ui()
        
        logger.info("Task queue manager initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("Task Queue")
        title_label.setObjectName("sectionTitle")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Queue controls
        queue_toolbar = QToolBar()
        queue_toolbar.setIconSize(QSize(16, 16))
        
        # Add actions
        self.clear_action = QAction("Clear Completed", self)
        self.clear_action.triggered.connect(self._on_clear_completed)
        queue_toolbar.addAction(self.clear_action)
        
        self.start_all_action = QAction("Start All", self)
        self.start_all_action.triggered.connect(self._on_start_all)
        queue_toolbar.addAction(self.start_all_action)
        
        self.pause_all_action = QAction("Pause All", self)
        self.pause_all_action.triggered.connect(self._on_pause_all)
        queue_toolbar.addAction(self.pause_all_action)
        
        header_layout.addWidget(queue_toolbar)
        
        main_layout.addLayout(header_layout)
        
        # Create splitter for queue and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Task list
        tasks_frame = QFrame()
        tasks_frame.setFrameShape(QFrame.Shape.StyledPanel)
        tasks_layout = QVBoxLayout(tasks_frame)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Tasks")
        self.filter_combo.addItem("Pending")
        self.filter_combo.addItem("In Progress")
        self.filter_combo.addItem("Completed")
        self.filter_combo.addItem("Failed")
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        
        tasks_layout.addLayout(filter_layout)
        
        # Task list
        self.task_list = QListWidget()
        self.task_list.setDragEnabled(True)
        self.task_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.task_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.task_list.setMinimumWidth(200)
        self.task_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.task_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.task_list.model().rowsMoved.connect(self._on_rows_moved)
        tasks_layout.addWidget(self.task_list)
        
        splitter.addWidget(tasks_frame)
        
        # Task details
        details_frame = QFrame()
        details_frame.setFrameShape(QFrame.Shape.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        
        self.details_title = QLabel("No task selected")
        self.details_title.setObjectName("detailsTitle")
        details_layout.addWidget(self.details_title)
        
        # Task details scroll area
        details_scroll = QScrollArea()
        details_scroll.setWidgetResizable(True)
        details_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        
        # Task info
        self.task_info_frame = QFrame()
        self.task_info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        task_info_layout = QVBoxLayout(self.task_info_frame)
        
        # Status and priority
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("N/A")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        status_layout.addWidget(QLabel("Priority:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("Low")
        self.priority_combo.addItem("Medium")
        self.priority_combo.addItem("High")
        self.priority_combo.currentIndexChanged.connect(self._on_priority_changed)
        status_layout.addWidget(self.priority_combo)
        
        task_info_layout.addLayout(status_layout)
        
        # Progress
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("Progress:"))
        self.progress_label = QLabel("0%")
        progress_layout.addWidget(self.progress_label)
        progress_layout.addStretch()
        task_info_layout.addLayout(progress_layout)
        
        # Description
        task_info_layout.addWidget(QLabel("Description:"))
        self.description_label = QLabel("No description")
        self.description_label.setWordWrap(True)
        task_info_layout.addWidget(self.description_label)
        
        # Dependencies
        task_info_layout.addWidget(QLabel("Dependencies:"))
        self.dependencies_label = QLabel("None")
        task_info_layout.addWidget(self.dependencies_label)
        
        self.details_layout.addWidget(self.task_info_frame)
        
        # Task actions
        actions_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self._on_start_clicked)
        actions_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self._on_pause_clicked)
        actions_layout.addWidget(self.pause_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        actions_layout.addWidget(self.cancel_button)
        
        self.details_layout.addLayout(actions_layout)
        
        # Stats section
        self.details_layout.addWidget(QLabel("Queue Statistics:"))
        self.stats_label = QLabel("No tasks in queue")
        self.details_layout.addWidget(self.stats_label)
        
        self.details_layout.addStretch()
        
        details_scroll.setWidget(self.details_widget)
        details_layout.addWidget(details_scroll)
        
        splitter.addWidget(details_frame)
        
        # Set initial splitter sizes (1:2 ratio)
        splitter.setSizes([100, 200])
        
        main_layout.addWidget(splitter)
        
        # Update UI state
        self._update_controls_state()
        self._update_statistics()
    
    def add_task(self, 
                task_id: str, 
                playlist_id: str, 
                playlist_name: str,
                description: str = "",
                priority: TaskPriority = TaskPriority.MEDIUM,
                dependencies: List[str] = None) -> None:
        """Add a task to the queue.
        
        Args:
            task_id: Unique identifier for the task
            playlist_id: Spotify playlist ID
            playlist_name: Name of the playlist
            description: Task description
            priority: Task priority level
            dependencies: List of task IDs this task depends on
        """
        # Create task
        task = TaskItem(
            task_id=task_id,
            playlist_id=playlist_id,
            playlist_name=playlist_name,
            description=description,
            priority=priority,
            dependencies=dependencies
        )
        
        # Add to dictionary
        self.tasks[task_id] = task
        
        # Add to list widget
        self._add_task_to_list(task)
        
        # Update UI
        self._update_statistics()
        logger.info(f"Added task {task_id} to queue")
    
    def _add_task_to_list(self, task: TaskItem) -> None:
        """Add a task to the list widget.
        
        Args:
            task: The task to add
        """
        item = QListWidgetItem(task.display_name)
        item.setData(Qt.ItemDataRole.UserRole, task.task_id)
        
        # Set color based on priority
        if task.priority == TaskPriority.HIGH:
            item.setBackground(QColor(255, 200, 200))  # Light red
        elif task.priority == TaskPriority.LOW:
            item.setBackground(QColor(200, 255, 200))  # Light green
        
        # Add to list based on current filter
        if self._should_show_task(task):
            self.task_list.addItem(item)
    
    def update_task_progress(self, task_id: str, progress: int) -> None:
        """Update a task's progress.
        
        Args:
            task_id: Unique identifier for the task
            progress: Progress value (0-100)
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            old_status = task.status
            
            # Update progress
            task.update_progress(progress)
            
            # If task completed, add to completed list
            if task.status == TaskStatus.COMPLETED and task_id not in self.completed_tasks:
                self.completed_tasks.append(task_id)
            
            # Update UI if selected
            if self.current_task_id == task_id:
                self._update_details_view()
            
            # If status changed, refresh list to apply filters
            if old_status != task.status:
                self._refresh_task_list()
            
            # Update stats
            self._update_statistics()
    
    def set_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Set a task's status.
        
        Args:
            task_id: Unique identifier for the task
            status: New status
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            old_status = task.status
            task.status = status
            
            # Handle completion
            if status == TaskStatus.COMPLETED and task_id not in self.completed_tasks:
                self.completed_tasks.append(task_id)
                task.progress = 100
            
            # Update UI if selected
            if self.current_task_id == task_id:
                self._update_details_view()
            
            # If status changed, refresh list to apply filters
            if old_status != status:
                self._refresh_task_list()
            
            # Update stats
            self._update_statistics()
    
    def set_task_error(self, task_id: str, error_message: str) -> None:
        """Set error message for a task.
        
        Args:
            task_id: Unique identifier for the task
            error_message: Error message
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.error_message = error_message
            task.status = TaskStatus.FAILED
            
            # Update UI if selected
            if self.current_task_id == task_id:
                self._update_details_view()
    
    def get_next_task(self) -> Optional[str]:
        """Get the next task that can be started.
        
        Returns:
            Task ID of the next task, or None if no tasks can be started
        """
        # Filter for pending tasks with dependencies met
        available_tasks = []
        
        for task_id, task in self.tasks.items():
            if (task.status == TaskStatus.PENDING and 
                task.can_start(self.completed_tasks)):
                available_tasks.append((task_id, task))
        
        if not available_tasks:
            return None
        
        # Sort by priority (highest first), then by order in list
        sorted_tasks = sorted(
            available_tasks,
            key=lambda x: (
                -x[1].priority.value,  # Higher priority first
                list(self.tasks.keys()).index(x[0])  # Maintain queue order as tiebreaker
            )
        )
        
        return sorted_tasks[0][0] if sorted_tasks else None
    
    def clear_completed_tasks(self) -> None:
        """Remove completed tasks from the queue."""
        task_ids_to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.COMPLETED:
                task_ids_to_remove.append(task_id)
        
        for task_id in task_ids_to_remove:
            self.remove_task(task_id)
    
    def remove_task(self, task_id: str) -> None:
        """Remove a task from the queue.
        
        Args:
            task_id: Unique identifier for the task
        """
        if task_id in self.tasks:
            # Remove from tasks dict
            del self.tasks[task_id]
            
            # Remove from completed list if there
            if task_id in self.completed_tasks:
                self.completed_tasks.remove(task_id)
            
            # Clear current selection if it was this task
            if self.current_task_id == task_id:
                self.current_task_id = None
                self._update_details_view()
            
            # Refresh list
            self._refresh_task_list()
            
            # Update stats
            self._update_statistics()
    
    def _refresh_task_list(self) -> None:
        """Refresh the task list widget with current tasks."""
        # Store current selection
        current_selection = self.current_task_id
        
        # Clear list
        self.task_list.clear()
        
        # Add tasks that match current filter
        for task_id, task in self.tasks.items():
            if self._should_show_task(task):
                self._add_task_to_list(task)
        
        # Restore selection if possible
        if current_selection in self.tasks:
            for i in range(self.task_list.count()):
                item = self.task_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == current_selection:
                    self.task_list.setCurrentItem(item)
                    break
    
    def _should_show_task(self, task: TaskItem) -> bool:
        """Check if a task should be shown based on current filter.
        
        Args:
            task: The task to check
            
        Returns:
            True if the task should be shown
        """
        filter_index = self.filter_combo.currentIndex()
        
        if filter_index == 0:  # All Tasks
            return True
        elif filter_index == 1:  # Pending
            return task.status == TaskStatus.PENDING
        elif filter_index == 2:  # In Progress
            return task.status == TaskStatus.IN_PROGRESS
        elif filter_index == 3:  # Completed
            return task.status == TaskStatus.COMPLETED
        elif filter_index == 4:  # Failed
            return task.status == TaskStatus.FAILED
        
        return True
    
    def _update_controls_state(self) -> None:
        """Update the state of control buttons based on selection."""
        task_selected = self.current_task_id is not None
        
        # Disable all controls if no task selected
        self.start_button.setEnabled(task_selected)
        self.pause_button.setEnabled(task_selected)
        self.cancel_button.setEnabled(task_selected)
        self.priority_combo.setEnabled(task_selected)
        
        # Further adjust based on task status if selected
        if task_selected and self.current_task_id in self.tasks:
            task = self.tasks[self.current_task_id]
            
            # Start button only enabled for pending or failed tasks
            self.start_button.setEnabled(
                task.status in (TaskStatus.PENDING, TaskStatus.FAILED, TaskStatus.PAUSED)
            )
            
            # Pause button only enabled for in-progress tasks
            self.pause_button.setEnabled(task.status == TaskStatus.IN_PROGRESS)
            
            # Cancel button not enabled for completed or cancelled tasks
            self.cancel_button.setEnabled(
                task.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)
            )
    
    def _update_details_view(self) -> None:
        """Update the details view with current selection."""
        if self.current_task_id in self.tasks:
            task = self.tasks[self.current_task_id]
            
            # Update details
            self.details_title.setText(task.display_name)
            self.status_label.setText(task.status.name)
            self.progress_label.setText(f"{task.progress}%")
            self.description_label.setText(task.description or "No description")
            
            # Set priority combobox
            self.priority_combo.blockSignals(True)
            self.priority_combo.setCurrentIndex(task.priority.value)
            self.priority_combo.blockSignals(False)
            
            # Dependencies
            if task.dependencies:
                dep_names = []
                for dep_id in task.dependencies:
                    if dep_id in self.tasks:
                        dep_names.append(self.tasks[dep_id].display_name)
                    else:
                        dep_names.append(f"Unknown ({dep_id})")
                self.dependencies_label.setText(", ".join(dep_names))
            else:
                self.dependencies_label.setText("None")
        else:
            # No task selected
            self.details_title.setText("No task selected")
            self.status_label.setText("N/A")
            self.progress_label.setText("0%")
            self.description_label.setText("No description")
            self.dependencies_label.setText("None")
        
        # Update controls
        self._update_controls_state()
    
    def _update_statistics(self) -> None:
        """Update queue statistics."""
        total_tasks = len(self.tasks)
        pending_count = 0
        in_progress_count = 0
        completed_count = 0
        failed_count = 0
        
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                pending_count += 1
            elif task.status == TaskStatus.IN_PROGRESS:
                in_progress_count += 1
            elif task.status == TaskStatus.COMPLETED:
                completed_count += 1
            elif task.status == TaskStatus.FAILED:
                failed_count += 1
        
        # Create stats text
        stats = [
            f"Total Tasks: {total_tasks}",
            f"Pending: {pending_count}",
            f"In Progress: {in_progress_count}",
            f"Completed: {completed_count}",
            f"Failed: {failed_count}"
        ]
        
        self.stats_label.setText("\n".join(stats))
    
    @Slot()
    def _on_selection_changed(self) -> None:
        """Handle selection change in task list."""
        selected_items = self.task_list.selectedItems()
        
        if selected_items:
            # Get task ID from item
            item = selected_items[0]
            task_id = item.data(Qt.ItemDataRole.UserRole)
            
            self.current_task_id = task_id
            self.task_selected.emit(task_id)
        else:
            self.current_task_id = None
        
        self._update_details_view()
    
    @Slot(QListWidgetItem)
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on a task item.
        
        Args:
            item: The clicked item
        """
        task_id = item.data(Qt.ItemDataRole.UserRole)
        self.task_double_clicked.emit(task_id)
    
    @Slot()
    def _on_filter_changed(self) -> None:
        """Handle change in filter selection."""
        self._refresh_task_list()
    
    @Slot()
    def _on_priority_changed(self) -> None:
        """Handle change in priority selection."""
        if self.current_task_id in self.tasks:
            new_priority = TaskPriority(self.priority_combo.currentIndex())
            task = self.tasks[self.current_task_id]
            
            if task.priority != new_priority:
                task.priority = new_priority
                self.task_priority_changed.emit(self.current_task_id, new_priority)
                
                # Refresh list to update visuals
                self._refresh_task_list()
    
    @Slot()
    def _on_start_clicked(self) -> None:
        """Handle click on start button."""
        if self.current_task_id in self.tasks:
            self.task_restarted.emit(self.current_task_id)
    
    @Slot()
    def _on_pause_clicked(self) -> None:
        """Handle click on pause button."""
        if self.current_task_id in self.tasks:
            task = self.tasks[self.current_task_id]
            task.status = TaskStatus.PAUSED
            self._update_details_view()
            
            # Emit signal to notify controller
            # This would be handled by a controller that interacts with the playlist service
    
    @Slot()
    def _on_cancel_clicked(self) -> None:
        """Handle click on cancel button."""
        if self.current_task_id in self.tasks:
            self.task_cancelled.emit(self.current_task_id)
            
            # Update status
            task = self.tasks[self.current_task_id]
            task.status = TaskStatus.CANCELLED
            self._update_details_view()
            self._refresh_task_list()
    
    @Slot()
    def _on_clear_completed(self) -> None:
        """Handle click on clear completed button."""
        self.clear_completed_tasks()
    
    @Slot()
    def _on_start_all(self) -> None:
        """Handle click on start all button."""
        # This would be handled by a controller
        pass
    
    @Slot()
    def _on_pause_all(self) -> None:
        """Handle click on pause all button."""
        # This would be handled by a controller
        pass
    
    @Slot()
    def _on_rows_moved(self) -> None:
        """Handle reordering of tasks in the list widget."""
        # Get the new order of task IDs
        new_order = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            task_id = item.data(Qt.ItemDataRole.UserRole)
            new_order.append(task_id)
        
        self.queue_reordered.emit(new_order)
