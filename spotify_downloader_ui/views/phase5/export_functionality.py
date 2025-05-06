"""
Export Functionality component for exporting playlists and analytics in various formats.
"""

import logging
from typing import Dict, List, Any, Optional
from functools import partial

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QTreeWidget, QTreeWidgetItem, QGroupBox, 
    QGridLayout, QCheckBox, QRadioButton, QFileDialog,
    QListWidget, QTabWidget, QLineEdit, QDateEdit, QTimeEdit,
    QScrollArea, QFrame, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QDate, QTime
from PySide6.QtGui import QFont, QIcon

from spotify_downloader_ui.services.config_service import ConfigService
from spotify_downloader_ui.services.error_service import ErrorService

logger = logging.getLogger(__name__)

class DataSourceSelector(QWidget):
    """Widget for selecting data sources to export."""
    
    selection_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Main data types
        self.playlists_check = QCheckBox("Playlists")
        self.playlists_check.setChecked(True)
        self.playlists_check.stateChanged.connect(self._update_selection)
        layout.addWidget(self.playlists_check)
        
        self.tracks_check = QCheckBox("Tracks")
        self.tracks_check.setChecked(True)
        self.tracks_check.stateChanged.connect(self._update_selection)
        layout.addWidget(self.tracks_check)
        
        self.analytics_check = QCheckBox("Analytics")
        self.analytics_check.stateChanged.connect(self._update_selection)
        layout.addWidget(self.analytics_check)
        
        self.visualizations_check = QCheckBox("Visualizations")
        self.visualizations_check.stateChanged.connect(self._update_selection)
        layout.addWidget(self.visualizations_check)
        
        self.hidden_gems_check = QCheckBox("Hidden Gems")
        self.hidden_gems_check.stateChanged.connect(self._update_selection)
        layout.addWidget(self.hidden_gems_check)
        
        # Playlist selection
        playlist_group = QGroupBox("Selected Playlists")
        playlist_layout = QVBoxLayout()
        
        self.playlist_list = QListWidget()
        self.playlist_list.itemChanged.connect(self._update_selection)
        playlist_layout.addWidget(self.playlist_list)
        
        # Quick select buttons
        select_layout = QHBoxLayout()
        select_all = QPushButton("Select All")
        select_all.clicked.connect(self._select_all_playlists)
        deselect_all = QPushButton("Deselect All")
        deselect_all.clicked.connect(self._deselect_all_playlists)
        
        select_layout.addWidget(select_all)
        select_layout.addWidget(deselect_all)
        select_layout.addStretch()
        
        playlist_layout.addLayout(select_layout)
        playlist_group.setLayout(playlist_layout)
        layout.addWidget(playlist_group)
    
    def set_playlists(self, playlists):
        """Set available playlists."""
        self.playlist_list.clear()
        
        for playlist in playlists:
            item = QListWidgetItem(playlist.get("name", "Unnamed"))
            item.setData(Qt.ItemDataRole.UserRole, playlist.get("id"))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.playlist_list.addItem(item)
        
        self._update_selection()
    
    def _select_all_playlists(self):
        """Select all playlists."""
        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
        self._update_selection()
    
    def _deselect_all_playlists(self):
        """Deselect all playlists."""
        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
        self._update_selection()
    
    def _update_selection(self):
        """Update selection and emit signal."""
        selection = {
            "data_types": {
                "playlists": self.playlists_check.isChecked(),
                "tracks": self.tracks_check.isChecked(),
                "analytics": self.analytics_check.isChecked(),
                "visualizations": self.visualizations_check.isChecked(),
                "hidden_gems": self.hidden_gems_check.isChecked()
            },
            "selected_playlists": []
        }
        
        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                playlist_id = item.data(Qt.ItemDataRole.UserRole)
                selection["selected_playlists"].append(playlist_id)
        
        self.selection_changed.emit(selection)

class FormatSelector(QWidget):
    """Widget for selecting export formats."""
    
    format_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._formats = {}
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Format selection grid
        self.format_grid = QGridLayout()
        layout.addLayout(self.format_grid)
        
        # Format options (will be populated later)
        self.format_options = QStackedWidget()
        layout.addWidget(self.format_options)
    
    def set_formats(self, formats):
        """Set available export formats."""
        self._formats = formats
        
        # Clear existing grid
        while self.format_grid.count():
            item = self.format_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Clear existing options
        while self.format_options.count():
            widget = self.format_options.widget(0)
            self.format_options.removeWidget(widget)
            widget.deleteLater()
        
        # Add format checkboxes to grid
        row, col = 0, 0
        max_cols = 3
        self.format_checks = {}
        
        for format_id, format_data in formats.items():
            if not format_data.get("available", False):
                continue
            
            check = QCheckBox(format_id.upper())
            check.setEnabled(True)
            check.stateChanged.connect(self._update_format)
            self.format_grid.addWidget(check, row, col)
            self.format_checks[format_id] = check
            
            # Create options for this format
            options_widget = QWidget()
            options_layout = QVBoxLayout(options_widget)
            
            # Add format-specific options
            supports = format_data.get("supports", [])
            options_layout.addWidget(QLabel(f"Supported data types: {', '.join(supports)}"))
            
            # Add format-specific settings (example)
            if format_id == "pdf":
                options_layout.addWidget(QCheckBox("Include table of contents"))
                options_layout.addWidget(QCheckBox("Include cover page"))
            elif format_id == "csv":
                options_layout.addWidget(QCheckBox("Include headers"))
                options_layout.addWidget(QCheckBox("Use semicolon as separator"))
            
            self.format_options.addWidget(options_widget)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Select CSV by default if available
        if "csv" in self.format_checks:
            self.format_checks["csv"].setChecked(True)
    
    def _update_format(self):
        """Update selected format and emit signal."""
        selected = {}
        active_format = None
        
        for format_id, check in self.format_checks.items():
            is_checked = check.isChecked()
            selected[format_id] = is_checked
            
            if is_checked and active_format is None:
                active_format = format_id
                # Show options for this format
                for i in range(self.format_options.count()):
                    if i == list(self.format_checks.keys()).index(format_id):
                        self.format_options.setCurrentIndex(i)
                        break
        
        self.format_changed.emit({"selected_formats": selected, "active_format": active_format})

class TemplateSelector(QWidget):
    """Widget for selecting export templates."""
    
    template_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Template selection
        self.template_combo = QComboBox()
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        layout.addWidget(self.template_combo)
        
        # Template description
        self.description_label = QLabel("Template description")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        # Template controls
        controls_layout = QHBoxLayout()
        
        save_button = QPushButton("Save Current as Template")
        save_button.clicked.connect(self._on_save_template)
        edit_button = QPushButton("Edit Template")
        edit_button.clicked.connect(self._on_edit_template)
        
        controls_layout.addWidget(save_button)
        controls_layout.addWidget(edit_button)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
    
    def set_templates(self, templates):
        """Set available templates."""
        self.template_combo.clear()
        
        for template in templates:
            self.template_combo.addItem(template.get("name", "Unnamed"), template.get("id"))
        
        if self.template_combo.count() > 0:
            self.template_combo.setCurrentIndex(0)
            self._update_description(templates[0])
    
    def _on_template_changed(self, index):
        """Handle template selection change."""
        template_id = self.template_combo.currentData()
        self.template_changed.emit(template_id)
    
    def _update_description(self, template):
        """Update template description."""
        self.description_label.setText(template.get("description", "No description available"))
    
    def _on_save_template(self):
        """Handle save template button click."""
        # In a real implementation, this would save the current settings as a new template
        logger.info("Save template requested")
    
    def _on_edit_template(self):
        """Handle edit template button click."""
        # In a real implementation, this would allow editing the selected template
        logger.info("Edit template requested")

class DestinationSelector(QWidget):
    """Widget for selecting export destination."""
    
    destination_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._destinations = {}
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Destination types
        self.destination_group = QWidget()
        self.destination_layout = QVBoxLayout(self.destination_group)
        
        # Destination options (will be filled when set_destinations is called)
        
        layout.addWidget(self.destination_group)
        
        # Destination settings (will be populated by set_destinations)
        self.settings_stack = QStackedWidget()
        layout.addWidget(self.settings_stack)
    
    def set_destinations(self, destinations):
        """Set available destinations."""
        self._destinations = destinations
        
        # Clear existing radio buttons
        while self.destination_layout.count():
            item = self.destination_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Clear existing settings
        while self.settings_stack.count():
            widget = self.settings_stack.widget(0)
            self.settings_stack.removeWidget(widget)
            widget.deleteLater()
        
        # Add radio buttons for each destination type
        self.destination_radios = {}
        
        for dest_id, dest_data in destinations.items():
            if not dest_data.get("available", False):
                continue
            
            radio = QRadioButton(dest_id.replace("_", " ").title())
            self.destination_layout.addWidget(radio)
            self.destination_radios[dest_id] = radio
            radio.toggled.connect(self._update_destination)
            
            # Create settings for this destination
            settings_widget = QWidget()
            settings_layout = QVBoxLayout(settings_widget)
            
            # Add destination-specific settings
            if dest_id == "local_file":
                # Path selection
                path_layout = QHBoxLayout()
                path_layout.addWidget(QLabel("Save to:"))
                path_edit = QLineEdit()
                path_layout.addWidget(path_edit)
                browse_button = QPushButton("Browse")
                path_layout.addWidget(browse_button)
                settings_layout.addLayout(path_layout)
                
                # Recent paths
                if "recent_paths" in dest_data:
                    settings_layout.addWidget(QLabel("Recent Locations:"))
                    recent_list = QListWidget()
                    for path in dest_data["recent_paths"]:
                        recent_list.addItem(path)
                    settings_layout.addWidget(recent_list)
            
            elif dest_id == "cloud_storage":
                # Cloud service selection
                settings_layout.addWidget(QLabel("Select Service:"))
                service_combo = QComboBox()
                if "services" in dest_data:
                    service_combo.addItems(dest_data["services"])
                settings_layout.addWidget(service_combo)
                
                # Authentication status
                auth_status = "Not Authenticated"
                if dest_data.get("authenticated", False):
                    auth_status = "Authenticated"
                settings_layout.addWidget(QLabel(f"Status: {auth_status}"))
                
                # Auth button
                auth_button = QPushButton("Authenticate")
                settings_layout.addWidget(auth_button)
            
            elif dest_id == "web_link":
                # Link options
                settings_layout.addWidget(QLabel("Share Options:"))
                
                # Expiry options
                expiry_layout = QHBoxLayout()
                expiry_layout.addWidget(QLabel("Link Expires:"))
                expiry_combo = QComboBox()
                if "expiry_options" in dest_data:
                    expiry_combo.addItems(dest_data["expiry_options"])
                expiry_layout.addWidget(expiry_combo)
                settings_layout.addLayout(expiry_layout)
                
                # Password protection
                settings_layout.addWidget(QCheckBox("Password Protect Link"))
            
            self.settings_stack.addWidget(settings_widget)
        
        # Select local_file by default if available
        if "local_file" in self.destination_radios:
            self.destination_radios["local_file"].setChecked(True)
    
    def _update_destination(self):
        """Update selected destination and emit signal."""
        selected = None
        
        for dest_id, radio in self.destination_radios.items():
            if radio.isChecked():
                selected = dest_id
                # Show settings for this destination
                for i in range(self.settings_stack.count()):
                    if i == list(self.destination_radios.keys()).index(dest_id):
                        self.settings_stack.setCurrentIndex(i)
                        break
        
        if selected:
            self.destination_changed.emit({"destination": selected})

class ScheduleExportDialog(QWidget):
    """Widget for scheduling exports."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Frequency selection
        freq_group = QGroupBox("Export Frequency")
        freq_layout = QVBoxLayout()
        
        self.once_radio = QRadioButton("One Time")
        self.once_radio.setChecked(True)
        freq_layout.addWidget(self.once_radio)
        
        self.daily_radio = QRadioButton("Daily")
        freq_layout.addWidget(self.daily_radio)
        
        self.weekly_radio = QRadioButton("Weekly")
        freq_layout.addWidget(self.weekly_radio)
        
        self.monthly_radio = QRadioButton("Monthly")
        freq_layout.addWidget(self.monthly_radio)
        
        freq_group.setLayout(freq_layout)
        layout.addWidget(freq_group)
        
        # Date and time
        datetime_layout = QGridLayout()
        
        datetime_layout.addWidget(QLabel("Date:"), 0, 0)
        self.date_edit = QDateEdit(QDate.currentDate())
        datetime_layout.addWidget(self.date_edit, 0, 1)
        
        datetime_layout.addWidget(QLabel("Time:"), 1, 0)
        self.time_edit = QTimeEdit(QTime.currentTime())
        datetime_layout.addWidget(self.time_edit, 1, 1)
        
        layout.addLayout(datetime_layout)
        
        # Save as profile
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Save as Profile:"))
        self.profile_name = QLineEdit()
        profile_name_placeholder = f"Export {QDate.currentDate().toString('yyyy-MM-dd')}"
        self.profile_name.setPlaceholderText(profile_name_placeholder)
        profile_layout.addWidget(self.profile_name)
        
        layout.addLayout(profile_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        schedule_button = QPushButton("Schedule Export")
        schedule_button.clicked.connect(self._on_schedule)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self._on_cancel)
        
        button_layout.addStretch()
        button_layout.addWidget(schedule_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _on_schedule(self):
        """Handle schedule button click."""
        # Get frequency
        frequency = "one_time"
        if self.daily_radio.isChecked():
            frequency = "daily"
        elif self.weekly_radio.isChecked():
            frequency = "weekly"
        elif self.monthly_radio.isChecked():
            frequency = "monthly"
        
        # Get date and time
        date = self.date_edit.date().toString("yyyy-MM-dd")
        time = self.time_edit.time().toString("hh:mm:ss")
        
        # Get profile name
        profile_name = self.profile_name.text() or self.profile_name.placeholderText()
        
        logger.info(f"Scheduling export: frequency={frequency}, date={date}, time={time}, profile={profile_name}")
        
        # In a real implementation, this would schedule the export
        self.close()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.close()

class ExportFunctionality:
    """Component for exporting playlists and analytics."""
    
    def __init__(self, config_service: ConfigService, error_service: ErrorService):
        """Initialize the component.
        
        Args:
            config_service: Service for accessing configuration
            error_service: Service for handling errors
        """
        self._config_service = config_service
        self._error_service = error_service
        self._widget = self._create_widget()
        self._export_data = None
        
        logger.info("Export Functionality component initialized")
    
    def _create_widget(self):
        """Create the main widget for this component."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Export Manager")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        # Action buttons
        self.profiles_button = QPushButton("Export Profiles")
        self.profiles_button.clicked.connect(self._on_profiles)
        self.scheduled_button = QPushButton("Scheduled Exports")
        self.scheduled_button.clicked.connect(self._on_scheduled)
        
        header_layout.addWidget(self.profiles_button)
        header_layout.addWidget(self.scheduled_button)
        
        main_layout.addLayout(header_layout)
        
        # Main content with tabs
        self.tabs = QTabWidget()
        
        # Data Selection tab
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        self.data_selector = DataSourceSelector()
        data_layout.addWidget(self.data_selector)
        self.tabs.addTab(data_tab, "Data Selection")
        
        # Format tab
        format_tab = QWidget()
        format_layout = QVBoxLayout(format_tab)
        self.format_selector = FormatSelector()
        format_layout.addWidget(self.format_selector)
        self.tabs.addTab(format_tab, "Format")
        
        # Template tab
        template_tab = QWidget()
        template_layout = QVBoxLayout(template_tab)
        self.template_selector = TemplateSelector()
        template_layout.addWidget(self.template_selector)
        self.tabs.addTab(template_tab, "Template")
        
        # Destination tab
        destination_tab = QWidget()
        destination_layout = QVBoxLayout(destination_tab)
        self.destination_selector = DestinationSelector()
        destination_layout.addWidget(self.destination_selector)
        self.tabs.addTab(destination_tab, "Destination")
        
        main_layout.addWidget(self.tabs)
        
        # Export button
        export_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export Now")
        self.export_button.clicked.connect(self._on_export)
        self.export_button.setStyleSheet("font-weight: bold;")
        
        self.schedule_button = QPushButton("Schedule Export")
        self.schedule_button.clicked.connect(self._on_schedule)
        
        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self._on_preview)
        
        export_layout.addStretch()
        export_layout.addWidget(self.preview_button)
        export_layout.addWidget(self.schedule_button)
        export_layout.addWidget(self.export_button)
        
        main_layout.addLayout(export_layout)
        
        return container
    
    @property
    def widget(self):
        """Get the widget for this component."""
        return self._widget
    
    def set_export_data(self, data):
        """Set export data.
        
        Args:
            data: Dictionary containing export configuration data
        """
        self._export_data = data
        
        # Set data for each selector
        if "available_data" in data and "playlists" in data["available_data"]:
            self.data_selector.set_playlists(data["available_data"]["playlists"])
        
        if "export_formats" in data:
            self.format_selector.set_formats(data["export_formats"])
        
        if "templates" in data:
            self.template_selector.set_templates(data["templates"])
        
        if "destinations" in data:
            self.destination_selector.set_destinations(data["destinations"])
        
        logger.info("Export data set")
    
    def _on_export(self):
        """Handle export button click."""
        # In a real implementation, this would gather all settings and perform the export
        logger.info("Export requested")
        # Show a message for demonstration
        self._error_service.show_info("Export", "Export operation started. Your files will be exported soon.")
    
    def _on_schedule(self):
        """Handle schedule button click."""
        # In a real implementation, this would show a dialog to schedule the export
        dialog = ScheduleExportDialog()
        dialog.show()
        logger.info("Schedule export requested")
    
    def _on_preview(self):
        """Handle preview button click."""
        # In a real implementation, this would show a preview of the export
        logger.info("Export preview requested")
        self._error_service.show_info("Preview", "Preview feature is not yet implemented.")
    
    def _on_profiles(self):
        """Handle profiles button click."""
        # In a real implementation, this would show a dialog to manage export profiles
        logger.info("Export profiles requested")
        
        # Show demo info
        if "export_profiles" in self._export_data:
            profiles = len(self._export_data["export_profiles"])
            self._error_service.show_info("Export Profiles", f"You have {profiles} saved export profiles.")
    
    def _on_scheduled(self):
        """Handle scheduled exports button click."""
        # In a real implementation, this would show a dialog to manage scheduled exports
        logger.info("Scheduled exports requested")
        
        # Show demo info
        if "scheduled_exports" in self._export_data:
            scheduled = len(self._export_data["scheduled_exports"])
            self._error_service.show_info("Scheduled Exports", f"You have {scheduled} scheduled exports.") 