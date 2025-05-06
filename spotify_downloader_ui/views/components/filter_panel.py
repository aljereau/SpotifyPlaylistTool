"""
Filter Panel component for filtering track data.
"""

import logging
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QLineEdit, QComboBox, QCheckBox,
    QGroupBox, QGridLayout, QSizePolicy, QSlider,
    QToolButton, QMenu
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QDate
from PySide6.QtGui import QIcon

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService

logger = logging.getLogger(__name__)

class FilterType(Enum):
    """Types of filters."""
    TEXT = 0
    RANGE = 1
    DATE = 2
    CATEGORY = 3
    BOOLEAN = 4

class FilterOperation(Enum):
    """Filter logical operations."""
    AND = 0
    OR = 1

class FilterCriteria:
    """Represents a filter criteria."""
    
    def __init__(self, 
                 field: str, 
                 display_name: str,
                 filter_type: FilterType,
                 options: Dict[str, Any] = None):
        """Initialize filter criteria.
        
        Args:
            field: Data field to filter on
            display_name: Human-readable name for the filter
            filter_type: Type of filter
            options: Additional options for the filter
        """
        self.field = field
        self.display_name = display_name
        self.filter_type = filter_type
        self.options = options or {}
        self.is_active = False

class FilterPanel(QWidget):
    """Widget for filtering track data."""
    
    filter_changed = Signal(dict)  # Emits filter criteria when changed
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the filter panel.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        super().__init__()
        
        self.config_service = config_service
        self.error_service = error_service
        
        # Filter state
        self.criteria = []
        self.active_filters = {}
        self.filter_operation = FilterOperation.AND
        self.recent_searches = []
        
        self._init_ui()
        self._create_default_criteria()
        
        logger.info("Filter panel initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        
        header_layout.addWidget(QLabel("<b>Filter Tracks</b>"))
        
        self.operation_combo = QComboBox()
        self.operation_combo.addItem("Match All (AND)", FilterOperation.AND.value)
        self.operation_combo.addItem("Match Any (OR)", FilterOperation.OR.value)
        self.operation_combo.currentIndexChanged.connect(self._on_operation_changed)
        header_layout.addWidget(self.operation_combo)
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self._on_clear_all)
        header_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(header_layout)
        
        # Search field
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tracks...")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        main_layout.addLayout(search_layout)
        
        # Recent searches
        self.recent_group = QGroupBox("Recent Searches")
        self.recent_group.setCheckable(True)
        self.recent_group.setChecked(False)
        self.recent_group.toggled.connect(self._on_recent_toggled)
        
        recent_layout = QVBoxLayout(self.recent_group)
        self.recent_layout = recent_layout  # Store reference for updating
        
        # Add empty label as placeholder
        self.no_recent_label = QLabel("No recent searches")
        recent_layout.addWidget(self.no_recent_label)
        
        main_layout.addWidget(self.recent_group)
        
        # Filters container
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        filters_widget = QWidget()
        self.filters_layout = QVBoxLayout(filters_widget)
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.filters_layout.setSpacing(10)
        
        scroll_area.setWidget(filters_widget)
        main_layout.addWidget(scroll_area, 1)  # Give it stretch
        
        # Saved presets
        preset_layout = QHBoxLayout()
        
        preset_layout.addWidget(QLabel("Presets:"))
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Select preset...", "")
        self.preset_combo.addItem("Hidden Gems", "hidden_gems")
        self.preset_combo.addItem("Recent Additions", "recent")
        self.preset_combo.addItem("Popular Tracks", "popular")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo, 1)
        
        self.save_preset_button = QPushButton("Save")
        self.save_preset_button.clicked.connect(self._on_save_preset)
        preset_layout.addWidget(self.save_preset_button)
        
        main_layout.addLayout(preset_layout)
    
    def _create_default_criteria(self):
        """Create the default filter criteria."""
        # Define standard filter criteria
        self.criteria = [
            FilterCriteria(
                field="search",
                display_name="Text Search",
                filter_type=FilterType.TEXT
            ),
            FilterCriteria(
                field="artists.name",
                display_name="Artist",
                filter_type=FilterType.CATEGORY,
                options={"multi_select": True}
            ),
            FilterCriteria(
                field="album.name",
                display_name="Album",
                filter_type=FilterType.CATEGORY,
                options={"multi_select": True}
            ),
            FilterCriteria(
                field="popularity",
                display_name="Popularity",
                filter_type=FilterType.RANGE,
                options={"min": 0, "max": 100}
            ),
            FilterCriteria(
                field="gem_score",
                display_name="Gem Score",
                filter_type=FilterType.RANGE,
                options={"min": 0, "max": 100}
            ),
            FilterCriteria(
                field="album.release_date",
                display_name="Release Date",
                filter_type=FilterType.DATE,
                options={"date_format": "YYYY-MM-DD"}
            ),
            FilterCriteria(
                field="explicit",
                display_name="Explicit Content",
                filter_type=FilterType.BOOLEAN
            )
        ]
        
        # Create filter widgets
        self._create_filter_widgets()
    
    def _create_filter_widgets(self):
        """Create filter widgets based on criteria."""
        # Clear existing widgets
        for i in reversed(range(self.filters_layout.count())):
            widget = self.filters_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Create new widgets
        for criteria in self.criteria:
            group = QGroupBox(criteria.display_name)
            group.setCheckable(True)
            group.setChecked(False)
            group_layout = QVBoxLayout(group)
            
            # Create controls based on filter type
            if criteria.filter_type == FilterType.TEXT:
                # Text search field
                text_input = QLineEdit()
                text_input.setPlaceholderText(f"Search {criteria.display_name.lower()}...")
                text_input.textChanged.connect(
                    lambda text, field=criteria.field: self._on_text_filter_changed(field, text)
                )
                group_layout.addWidget(text_input)
                
            elif criteria.filter_type == FilterType.RANGE:
                # Range slider with labels
                range_layout = QHBoxLayout()
                
                min_value = criteria.options.get("min", 0)
                max_value = criteria.options.get("max", 100)
                
                # Min label
                min_label = QLabel(str(min_value))
                range_layout.addWidget(min_label)
                
                # Slider
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setMinimum(min_value)
                slider.setMaximum(max_value)
                slider.setValue(min_value)
                slider.setTickPosition(QSlider.TickPosition.TicksBelow)
                slider.setTickInterval((max_value - min_value) // 5)
                slider.valueChanged.connect(
                    lambda value, field=criteria.field, label=min_label: 
                    self._on_range_filter_changed(field, value, label)
                )
                range_layout.addWidget(slider, 1)
                
                # Max label
                max_label = QLabel(str(max_value))
                range_layout.addWidget(max_label)
                
                group_layout.addLayout(range_layout)
                
            elif criteria.filter_type == FilterType.CATEGORY:
                # Combo box with categories
                # In a real implementation, these would be populated from the data
                combo = QComboBox()
                combo.addItem("All", "")
                combo.addItem("Option 1", "option1")
                combo.addItem("Option 2", "option2")
                combo.addItem("Option 3", "option3")
                combo.currentIndexChanged.connect(
                    lambda index, field=criteria.field, combo=combo: 
                    self._on_category_filter_changed(field, combo.currentData())
                )
                group_layout.addWidget(combo)
            
            elif criteria.filter_type == FilterType.DATE:
                # Date filter controls
                # This is simplified - a real implementation would use a date picker
                combo = QComboBox()
                combo.addItem("Any time", "")
                combo.addItem("Last 30 days", "30days")
                combo.addItem("Last 90 days", "90days")
                combo.addItem("Last year", "1year")
                combo.addItem("Custom range", "custom")
                combo.currentIndexChanged.connect(
                    lambda index, field=criteria.field, combo=combo: 
                    self._on_date_filter_changed(field, combo.currentData())
                )
                group_layout.addWidget(combo)
                
            elif criteria.filter_type == FilterType.BOOLEAN:
                # Boolean checkboxes
                check_layout = QHBoxLayout()
                
                yes_check = QCheckBox("Yes")
                yes_check.stateChanged.connect(
                    lambda state, field=criteria.field, value=True: 
                    self._on_boolean_filter_changed(field, value, state)
                )
                check_layout.addWidget(yes_check)
                
                no_check = QCheckBox("No")
                no_check.stateChanged.connect(
                    lambda state, field=criteria.field, value=False: 
                    self._on_boolean_filter_changed(field, value, state)
                )
                check_layout.addWidget(no_check)
                
                check_layout.addStretch()
                group_layout.addLayout(check_layout)
            
            # Connect checkbox state of the group itself
            group.toggled.connect(
                lambda state, field=criteria.field: self._on_filter_toggled(field, state)
            )
            
            self.filters_layout.addWidget(group)
        
        # Add stretch at the end
        self.filters_layout.addStretch(1)
    
    def set_available_categories(self, field: str, categories: List[str]):
        """Set available categories for a category filter.
        
        Args:
            field: Filter field name
            categories: List of available category values
        """
        # Find the relevant filter widget and update its options
        # This is a simplified implementation - would need more in a real app
        logger.info(f"Would update categories for {field}: {categories}")
    
    def apply_preset(self, preset_name: str):
        """Apply a saved filter preset.
        
        Args:
            preset_name: Name of the preset to apply
        """
        # In a real implementation, this would load preset values
        # For now, just log it
        logger.info(f"Would apply preset: {preset_name}")
        
        # Simulate loading a preset
        self.clear_filters()
        
        if preset_name == "hidden_gems":
            # Set up filters for hidden gems
            self._update_filter("gem_score", {"min": 70})
            self._update_filter("popularity", {"max": 50})
        elif preset_name == "recent":
            # Set up filters for recent additions
            self._update_filter("album.release_date", {"period": "90days"})
        elif preset_name == "popular":
            # Set up filters for popular tracks
            self._update_filter("popularity", {"min": 70})
    
    def clear_filters(self):
        """Clear all active filters."""
        self.active_filters = {}
        
        # Reset UI - would uncheck all filter groups
        logger.info("Cleared all filters")
        
        # Notify of change
        self.filter_changed.emit({})
    
    def add_recent_search(self, search_text: str):
        """Add a search term to recent searches.
        
        Args:
            search_text: Search text to add
        """
        if not search_text or search_text in self.recent_searches:
            return
            
        # Add to recent searches (limit to 5)
        self.recent_searches.insert(0, search_text)
        if len(self.recent_searches) > 5:
            self.recent_searches.pop()
        
        # Update UI
        self._update_recent_searches()
    
    def _update_recent_searches(self):
        """Update the recent searches UI."""
        # Clear existing items
        for i in reversed(range(self.recent_layout.count())):
            widget = self.recent_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        if not self.recent_searches:
            self.recent_layout.addWidget(self.no_recent_label)
            return
            
        # Add recent search buttons
        for search in self.recent_searches:
            button = QPushButton(search)
            button.clicked.connect(lambda _, text=search: self._on_recent_search_clicked(text))
            self.recent_layout.addWidget(button)
    
    def _update_filter(self, field: str, value: Any):
        """Update a filter value.
        
        Args:
            field: Filter field name
            value: New filter value
        """
        # Update the active filters
        self.active_filters[field] = value
        
        # Notify of change
        self.filter_changed.emit(self.active_filters)
    
    def _remove_filter(self, field: str):
        """Remove a filter.
        
        Args:
            field: Filter field to remove
        """
        if field in self.active_filters:
            del self.active_filters[field]
            
            # Notify of change
            self.filter_changed.emit(self.active_filters)
    
    @Slot(int)
    def _on_operation_changed(self, index: int):
        """Handle filter operation change.
        
        Args:
            index: Selected index
        """
        operation = FilterOperation(self.operation_combo.currentData())
        self.filter_operation = operation
        
        # Update active filters with operation
        self._update_filter("_operation", operation.value)
    
    @Slot()
    def _on_clear_all(self):
        """Handle clear all button click."""
        self.clear_filters()
    
    @Slot()
    def _on_search(self):
        """Handle search input."""
        search_text = self.search_input.text()
        if search_text:
            # Add to recent searches
            self.add_recent_search(search_text)
            
            # Update filter
            self._update_filter("search", search_text)
    
    @Slot(bool)
    def _on_recent_toggled(self, checked: bool):
        """Handle recent searches group toggle.
        
        Args:
            checked: Whether the group is checked
        """
        # This would show/hide the recent searches in a real implementation
        pass
    
    @Slot(str)
    def _on_recent_search_clicked(self, search_text: str):
        """Handle click on a recent search.
        
        Args:
            search_text: Search text to apply
        """
        # Set the search input
        self.search_input.setText(search_text)
        
        # Apply the search
        self._update_filter("search", search_text)
    
    @Slot(str, str)
    def _on_text_filter_changed(self, field: str, text: str):
        """Handle text filter change.
        
        Args:
            field: Filter field
            text: Filter text
        """
        if text:
            self._update_filter(field, text)
        else:
            self._remove_filter(field)
    
    @Slot(str, int, QLabel)
    def _on_range_filter_changed(self, field: str, value: int, label: QLabel):
        """Handle range filter change.
        
        Args:
            field: Filter field
            value: Filter value
            label: Label to update
        """
        # Update label
        label.setText(str(value))
        
        # Update filter
        self._update_filter(field, {"min": value})
    
    @Slot(str, str)
    def _on_category_filter_changed(self, field: str, category: str):
        """Handle category filter change.
        
        Args:
            field: Filter field
            category: Selected category
        """
        if category:
            self._update_filter(field, category)
        else:
            self._remove_filter(field)
    
    @Slot(str, str)
    def _on_date_filter_changed(self, field: str, period: str):
        """Handle date filter change.
        
        Args:
            field: Filter field
            period: Selected time period
        """
        if period:
            self._update_filter(field, {"period": period})
        else:
            self._remove_filter(field)
    
    @Slot(str, bool, int)
    def _on_boolean_filter_changed(self, field: str, value: bool, state: int):
        """Handle boolean filter change.
        
        Args:
            field: Filter field
            value: Boolean value
            state: Checkbox state
        """
        if state == Qt.CheckState.Checked.value:
            self._update_filter(field, value)
        else:
            # Only remove if both checkboxes are unchecked
            # This is simplified - a real implementation would be more complex
            self._remove_filter(field)
    
    @Slot(str, bool)
    def _on_filter_toggled(self, field: str, enabled: bool):
        """Handle filter group toggle.
        
        Args:
            field: Filter field
            enabled: Whether the filter is enabled
        """
        # Update filter criteria active state
        for criteria in self.criteria:
            if criteria.field == field:
                criteria.is_active = enabled
                break
        
        if not enabled:
            self._remove_filter(field)
    
    @Slot(int)
    def _on_preset_selected(self, index: int):
        """Handle preset selection.
        
        Args:
            index: Selected index
        """
        preset = self.preset_combo.currentData()
        if preset:
            self.apply_preset(preset)
    
    @Slot()
    def _on_save_preset(self):
        """Handle save preset button click."""
        # In a real implementation, this would show a dialog to name and save the preset
        # For now, just log it
        logger.info("Would save current filter configuration as a preset")

class FilterSidebar:
    """Container component for filter panel."""
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the filter sidebar.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        self.config_service = config_service
        self.error_service = error_service
        
        # Create the filter panel
        self.filter_panel = FilterPanel(config_service, error_service)
        
        logger.info("Filter sidebar initialized")
    
    @property
    def widget(self) -> QWidget:
        """Get the main widget.
        
        Returns:
            The filter sidebar widget
        """
        return self.filter_panel
    
    @property
    def filter_changed(self) -> Signal:
        """Get the filter changed signal.
        
        Returns:
            Signal that emits when filters change
        """
        return self.filter_panel.filter_changed
    
    def clear_filters(self):
        """Clear all active filters."""
        self.filter_panel.clear_filters()
    
    def set_available_categories(self, field: str, categories: List[str]):
        """Set available categories for a category filter.
        
        Args:
            field: Filter field name
            categories: List of available category values
        """
        self.filter_panel.set_available_categories(field, categories)
    
    def apply_preset(self, preset_name: str):
        """Apply a saved filter preset.
        
        Args:
            preset_name: Name of the preset to apply
        """
        self.filter_panel.apply_preset(preset_name)